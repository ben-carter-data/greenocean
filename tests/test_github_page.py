"""The GitHub page: its links come from PROJECT_LINKS and its markup stays balanced."""

import html
from html.parser import HTMLParser

import pytest

from bi import charts, github_page, project

VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class BalanceChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"</{tag}> closes {self.stack[-1] if self.stack else 'nothing'}")
            return
        self.stack.pop()


def links():
    return {link["name"]: link["url"] for link in project.PROJECT_LINKS}


@pytest.mark.parametrize("mode", sorted(set(charts.THEMES) | set(charts.PALETTES)))
def test_page_has_every_item_with_its_real_url(mode):
    page = github_page.build_github_page_html(mode)
    urls = links()
    for name, title in [
        ("GitHub Actions", "GitHub Actions"),
        ("Historial de cambios", "Historial de cambios"),
        ("DECISIONES", "Decisiones"),
        ("MANUAL", "Manual"),
        ("Informes semanales", "Informes semanales"),
    ]:
        assert f"<h3>{html.escape(title)}</h3>" in page
        assert f'href="{html.escape(urls[name], quote=True)}"' in page
        assert f'data-copy="{html.escape(urls[name], quote=True)}"' in page
    assert f'href="{project.GITHUB_URL}"' in page
    assert github_page.REPO_SLUG in page
    assert page.count('class="gh-copy"') == 6
    assert page.count('target="_blank"') == 6
    assert "robot" not in page.lower()


@pytest.mark.parametrize("mode", sorted(set(charts.THEMES) | set(charts.PALETTES)))
def test_page_tags_balance(mode):
    checker = BalanceChecker()
    checker.feed(github_page.build_github_page_html(mode))
    checker.close()
    assert checker.errors == []
    assert checker.stack == []


def test_items_without_url_are_skipped(monkeypatch):
    changed = [{**link, "url": None} if link["name"] == "MANUAL" else link for link in project.PROJECT_LINKS]
    monkeypatch.setattr(project, "PROJECT_LINKS", changed)
    page = github_page.build_github_page_html(charts.MODE_LIGHT)
    assert "<h3>Manual</h3>" not in page
    assert "<h3>Informes semanales</h3>" in page


def test_script_is_one_element_without_markup_strings():
    script = github_page.GITHUB_PAGE_SCRIPT
    assert script.startswith("<script>") and script.endswith("</script>")
    body = script[len("<script>") : -len("</script>")]
    assert "<" not in body.replace("<=", "")
    assert ".gh-copy" in body and "1500" in body
