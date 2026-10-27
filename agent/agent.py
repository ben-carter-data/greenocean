"""ODEPA price download agent.

Flow: load_input_resources -> download_all_resources -> download_file
      -> validate_downloaded_file -> log_resource_result.

Downloads the CSV files listed in input.csv, validates each one and writes one
log line per resource. It does not load data into the database: etl/etl.py does.
"""

import csv
import hashlib
import json
import logging
import sys
import tempfile
import time
from datetime import date, datetime
from pathlib import Path

import certifi
import requests

# region Constants
AGENT_ID = "ODEPA_PRICES_DL"

STATUS_DOWNLOADED = "DOWNLOADED"
STATUS_UNCHANGED = "UNCHANGED"
STATUS_ALREADY_EXISTS = "ALREADY_EXISTS"
STATUS_FAILED = "FAILED"

REASON_EMPTY_FILE = "EMPTY_FILE"
REASON_UNEXPECTED_HEADER = "UNEXPECTED_HEADER"
REASON_NO_ROWS = "NO_ROWS"
REASON_DOWNLOAD_ERROR = "DOWNLOAD_ERROR"
# endregion

# region Variables
BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "input.csv"
DOWNLOAD_DIR = BASE_DIR / "downloads"
LOG_DIR = BASE_DIR / "logs"
MANIFEST_FILE = DOWNLOAD_DIR / "manifest.json"
# D-164: datos.odepa.gob.cl chains to «emSign Root CA - G1», which certifi dropped
# on 2026-10-18. The root is kept here and trusted in addition to certifi, so
# the certificate is still fully verified.
EXTRA_ROOT_CERTIFICATES = [BASE_DIR / "certs" / "emsign_root_ca_g1.pem"]

# Maximum failed attempts per resource before it counts as a harvest failure.
FETCH_WARNINGS_THRESHOLD = 3
# Maximum failed resources before the agent stops cleanly.
HARVEST_FAILURES_THRESHOLD = 1
REQUEST_TIMEOUT_SECONDS = 120
SECONDS_BETWEEN_RETRIES = 5

# Columns each source must contain, exactly as published by ODEPA (Spanish).
# If they change, the file is rejected instead of being loaded silently.
EXPECTED_HEADERS = {
    "wholesale": [
        "Fecha",
        "ID region",
        "Region",
        "Mercado",
        "Subsector",
        "Producto",
        "Variedad / Tipo",
        "Calidad",
        "Unidad de comercializacion",
        "Origen",
        "Volumen",
        "Precio minimo",
        "Precio maximo",
        "Precio promedio",
    ],
    "consumer": [
        "Anio",
        "Mes",
        "Semana",
        "Fecha inicio",
        "Fecha termino",
        "ID region",
        "Region",
        "Sector",
        "Tipo de punto monitoreo",
        "Grupo",
        "Producto",
        "Unidad",
        "Precio minimo",
        "Precio maximo",
        "Precio promedio",
    ],
}

logger = logging.getLogger(AGENT_ID)
# endregion


# region Logging
def setup_logging():
    """Create one log file per run and also print to the console."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"{AGENT_ID}_{datetime.now():%Y%m%d_%H%M%S}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
        force=True,
    )
    return log_file


def log_resource_result(resource, status, detail=""):
    """Write the final outcome of one resource as a single log line."""
    logger.info("%s | %s %s | %s", status, resource["source"], resource["year"], detail)


# endregion


# region Input
def load_input_resources(input_file=INPUT_FILE):
    """Read the list of resources to download: source, year and url."""
    with open(input_file, encoding="utf-8", newline="") as file:
        resources = list(csv.DictReader(file))
    for resource in resources:
        if resource["source"] not in EXPECTED_HEADERS:
            raise ValueError(f"Unknown source in input file: {resource['source']}")
        resource["year"] = int(resource["year"])
    return resources


# endregion


# region Download and validation
def build_certificate_bundle(extra_certificates=EXTRA_ROOT_CERTIFICATES):
    """Path of a CA bundle: certifi's roots plus the extra ones (D-164)."""
    bundle = Path(tempfile.gettempdir()) / f"{AGENT_ID}_ca_bundle.pem"
    parts = [Path(certifi.where()).read_text(encoding="utf-8")]
    parts += [certificate.read_text(encoding="utf-8") for certificate in extra_certificates]
    bundle.write_text("\n".join(parts), encoding="utf-8")
    return bundle


def download_file(url, destination_path):
    """Download the url into a file. Raises an exception if anything fails."""
    response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS, verify=str(build_certificate_bundle()))
    response.raise_for_status()
    destination_path.write_bytes(response.content)


def validate_downloaded_file(file_path, source):
    """Check the file is usable. Returns (True, "") or (False, reason)."""
    if not file_path.exists() or file_path.stat().st_size == 0:
        return False, REASON_EMPTY_FILE
    with open(file_path, encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file)
        header = next(reader, None)
        first_data_row = next(reader, None)
    if header != EXPECTED_HEADERS[source]:
        return False, REASON_UNEXPECTED_HEADER
    if first_data_row is None:
        return False, REASON_NO_ROWS
    return True, ""


def compute_file_hash(file_path):
    """Fingerprint of the file content, used to detect changes between runs."""
    return hashlib.sha256(file_path.read_bytes()).hexdigest()


# endregion


# region Manifest
def load_manifest():
    """Read the record of previously downloaded files (empty on first run)."""
    if MANIFEST_FILE.exists():
        return json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    return {}


def save_manifest(manifest):
    """Persist the record of downloaded files."""
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


# endregion


# region Navigation
def download_all_resources(resources, downloader=download_file, seconds_between_retries=SECONDS_BETWEEN_RETRIES):
    """Download and validate every resource, with retries and failure limits.

    Returns the number of resources that could not be downloaded.
    """
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    harvest_failures = 0

    for resource in resources:
        file_name = f"{resource['source']}_{resource['year']}.csv"
        final_path = DOWNLOAD_DIR / file_name
        temporary_path = DOWNLOAD_DIR / (file_name + ".tmp")

        # A closed year that was already downloaded is not downloaded again.
        if resource["year"] < date.today().year and final_path.exists():
            log_resource_result(resource, STATUS_ALREADY_EXISTS, file_name)
            continue

        fetch_warnings = 0
        is_downloaded = False
        failure_reason = ""
        while fetch_warnings < FETCH_WARNINGS_THRESHOLD:
            try:
                downloader(resource["url"], temporary_path)
                is_valid, failure_reason = validate_downloaded_file(temporary_path, resource["source"])
            except Exception as error:  # network down, HTTP error, timeout
                is_valid, failure_reason = False, f"{REASON_DOWNLOAD_ERROR}: {error}"

            if is_valid:
                is_downloaded = True
                break

            fetch_warnings += 1
            logger.warning(
                "Attempt %s of %s failed | %s %s | %s",
                fetch_warnings,
                FETCH_WARNINGS_THRESHOLD,
                resource["source"],
                resource["year"],
                failure_reason,
            )
            temporary_path.unlink(missing_ok=True)
            # Retrying cannot fix a changed header, so stop immediately.
            if failure_reason == REASON_UNEXPECTED_HEADER:
                break
            if fetch_warnings < FETCH_WARNINGS_THRESHOLD:
                time.sleep(seconds_between_retries)

        if not is_downloaded:
            harvest_failures += 1
            log_resource_result(resource, STATUS_FAILED, failure_reason)
            if harvest_failures >= HARVEST_FAILURES_THRESHOLD:
                logger.error("Maximum harvest failures reached. Stopping the agent.")
                break
            continue

        # The previous file is replaced only after the new one passed validation.
        new_hash = compute_file_hash(temporary_path)
        is_unchanged = manifest.get(file_name, {}).get("hash") == new_hash
        temporary_path.replace(final_path)
        manifest[file_name] = {
            "source": resource["source"],
            "year": resource["year"],
            "hash": new_hash,
            "bytes": final_path.stat().st_size,
            "downloaded_at": datetime.now().isoformat(timespec="seconds"),
        }
        save_manifest(manifest)
        log_resource_result(
            resource,
            STATUS_UNCHANGED if is_unchanged else STATUS_DOWNLOADED,
            f"{file_name} ({final_path.stat().st_size} bytes)",
        )

    return harvest_failures


# endregion


# region Entry point
def main():
    """Run the agent. Exit code 0 means every resource was downloaded."""
    setup_logging()
    logger.info("Agent %s started", AGENT_ID)
    try:
        resources = load_input_resources()
        harvest_failures = download_all_resources(resources)
    except Exception as error:
        logger.error("Unhandled error: %s", error)
        harvest_failures = 1
    logger.info("Agent finished. Failed resources: %s", harvest_failures)
    return 1 if harvest_failures else 0


if __name__ == "__main__":
    sys.exit(main())
# endregion
