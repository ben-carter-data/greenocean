"""Compact lists for the tables that grow (D-348): at most PAGE_SIZE rows at a time, each row collapsed to one line and
only one open at a time.

Streamlit draws them: a row is a button (its summary line) and, when it is the open one, the detail under it. The open
row and the page live in the session; changing the filters (the «signature») brings the list back to its first page with
every row closed. The detail is HTML the caller already escaped.
"""

from __future__ import annotations

from typing import Any, Callable, Sequence

import streamlit as st

from bi.i18n import tr

PAGE_SIZE = 20


def page_count(total: int, size: int = PAGE_SIZE) -> int:
    return max(1, -(-total // size))


def show_compact_rows(
    key: str,
    rows: Sequence[Any],
    summary_of: Callable[[Any], str],
    detail_of: Callable[[Any], str],
    signature: str = "",
    size: int = PAGE_SIZE,
    after_detail: Callable[[Any], None] | None = None,
) -> int:
    """Draw one page of «rows»; returns how many rows it drew (never more than «size»)."""
    if st.session_state.get(f"{key}_signature") != signature:
        st.session_state[f"{key}_signature"] = signature
        st.session_state[f"{key}_page"] = 0
        st.session_state[f"{key}_open"] = None
    pages = page_count(len(rows), size)
    page = min(max(int(st.session_state.get(f"{key}_page", 0)), 0), pages - 1)
    st.session_state[f"{key}_page"] = page
    opened = st.session_state.get(f"{key}_open")
    first = page * size
    drawn = rows[first : first + size]
    for offset, row in enumerate(drawn):
        index = first + offset
        is_open = opened == index
        with st.container(key=f"{key}_row_{offset}"):
            if st.button(
                summary_of(row),
                key=f"{key}_toggle_{offset}",
                icon=":material/expand_less:" if is_open else ":material/expand_more:",
                type="tertiary",
                width="stretch",
            ):
                st.session_state[f"{key}_open"] = None if is_open else index
                st.rerun()
            if is_open:
                st.markdown(detail_of(row), unsafe_allow_html=True)
                if after_detail:
                    after_detail(row)
    if pages > 1:
        with st.container(horizontal=True, vertical_alignment="center", key=f"{key}_pager"):
            if st.button(tr("Anterior"), key=f"{key}_prev", icon=":material/chevron_left:", disabled=page == 0):
                st.session_state[f"{key}_page"] = page - 1
                st.session_state[f"{key}_open"] = None
                st.rerun()
            st.caption(tr("Página {} de {} · {} filas").format(page + 1, pages, len(rows)))
            if st.button(
                tr("Siguiente"), key=f"{key}_next", icon=":material/chevron_right:", disabled=page == pages - 1
            ):
                st.session_state[f"{key}_page"] = page + 1
                st.session_state[f"{key}_open"] = None
                st.rerun()
    return len(drawn)


def build_css(palette: dict[str, str]) -> str:
    """Rows as one line each: a hairline between them, the summary left-aligned, the detail indented under it."""
    line, text = palette["card_border"], palette["text"]
    return f"""<style>
[class*="st-key-cr_"][class*="_row_"] {{ border-bottom:1px solid {line}; padding:0 !important; gap:0 !important; }}
[class*="st-key-cr_"][class*="_row_"] button {{ justify-content:flex-start !important; text-align:left !important; width:100% !important; }}
[class*="st-key-cr_"][class*="_row_"] button p {{ font-size:13px !important; color:{text} !important; text-align:left !important; overflow-wrap:anywhere; }}
[class*="st-key-cr_"][class*="_row_"] [data-testid="stMarkdownContainer"] .cr-detail {{ margin:0 0 10px 34px; font-size:12.5px; color:{text}; }}
</style>"""
