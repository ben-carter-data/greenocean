"""The places where the products are sold, by region (D-306): information only, no price.

ODEPA names the wholesale market of each wholesale quote and the type of point (and, in Santiago, the sector) of each
consumer quote. The star schema does not keep them (a price is per region and channel), so this small file keeps what
exists in each region, regenerated from the downloaded CSV files:  python etl/points_of_sale.py
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DOWNLOADS = ROOT / "agent" / "downloads"
OUTPUT = ROOT / "bi" / "assets" / "points_of_sale.json"


def build(download_dir=DOWNLOADS):
    """{region: {"wholesale": [markets], "consumer": [types], "sectors": [sectors]}} read from every downloaded year."""
    wholesale = pd.concat(
        [pd.read_csv(path, dtype=str, encoding="utf-8-sig") for path in sorted(download_dir.glob("wholesale_*.csv"))]
    )
    consumer = pd.concat(
        [pd.read_csv(path, dtype=str, encoding="utf-8-sig") for path in sorted(download_dir.glob("consumer_*.csv"))]
    )
    points = {}
    for region in sorted(set(wholesale["Region"]) | set(consumer["Region"])):
        rows = consumer[consumer["Region"] == region]
        sectors = rows.loc[rows["Sector"].isin(["Norte", "Sur", "Oriente", "Poniente", "Centro"]), "Sector"]
        points[region] = {
            "wholesale": sorted(wholesale.loc[wholesale["Region"] == region, "Mercado"].dropna().unique()),
            "consumer": [name for name, _ in rows["Tipo de punto monitoreo"].value_counts().items()],
            "sectors": sorted(sectors.unique()),
        }
    return points


if __name__ == "__main__":
    OUTPUT.write_text(json.dumps(build(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("written", OUTPUT)
