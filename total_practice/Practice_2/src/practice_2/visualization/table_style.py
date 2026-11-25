"""Reusable Pandas Styler presentation for notebook decision tables."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

import pandas as pd
from pandas.io.formats.style import Styler


TABLE_STYLES = [
    {
        "selector": "table",
        "props": [
            ("border-collapse", "separate"),
            ("border-spacing", "0"),
            ("font-family", "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"),
            ("font-size", "14px"),
            ("line-height", "1.45"),
            ("margin", "0.4rem 0 1.2rem 0"),
            ("max-width", "100%"),
        ],
    },
    {
        "selector": "caption",
        "props": [
            ("caption-side", "top"),
            ("color", "#1f4e78"),
            ("font-size", "17px"),
            ("font-weight", "600"),
            ("padding", "10px 0"),
            ("text-align", "left"),
        ],
    },
    {
        "selector": "thead th",
        "props": [
            ("background-color", "#1f4e78"),
            ("color", "#ffffff"),
            ("padding", "10px 14px"),
            ("text-align", "left"),
            ("border", "1px solid #5b9bd5"),
        ],
    },
    {
        "selector": "tbody td",
        "props": [
            ("background-color", "light-dark(#f8fafc, #1f1f1f)"),
            ("color", "light-dark(#172033, #e6edf5)"),
            ("padding", "9px 14px"),
            ("border-bottom", "1px solid light-dark(#d8e1eb, #3a3a3a)"),
            ("vertical-align", "middle"),
        ],
    },
    {
        "selector": "tbody tr:nth-child(even) td",
        "props": [("background-color", "rgba(91, 155, 213, 0.15)")],
    },
    {
        "selector": "tbody tr:hover td",
        "props": [("background-color", "rgba(91, 155, 213, 0.30)")],
    },
    {
        "selector": "tbody td:first-child",
        "props": [("font-weight", "500"), ("white-space", "nowrap")],
    },
]


def style_table(
    dataframe: pd.DataFrame,
    *,
    caption: str,
    formats: Mapping[str, str] | None = None,
    row_highlighter: Callable[[pd.Series], list[str]] | None = None,
) -> Styler:
    """Return a consistently formatted notebook table.

    ``row_highlighter`` receives each row and returns one CSS declaration per
    column. It is intentionally caller-owned so scientific decision criteria
    remain visible at the notebook layer rather than hidden in presentation code.
    """
    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError("dataframe must be a pandas DataFrame")
    if dataframe.empty:
        raise ValueError("dataframe must contain at least one row")

    numeric_columns = dataframe.select_dtypes(include="number").columns.tolist()
    styled = (
        dataframe.style.hide(axis="index")
        .set_table_styles(TABLE_STYLES)
        .set_caption(caption)
        .set_properties(
            subset=numeric_columns,
            **{"text-align": "right", "font-variant-numeric": "tabular-nums"},
        )
    )
    if formats:
        styled = styled.format(dict(formats))
    if row_highlighter:
        styled = styled.apply(row_highlighter, axis=1)
    return styled
