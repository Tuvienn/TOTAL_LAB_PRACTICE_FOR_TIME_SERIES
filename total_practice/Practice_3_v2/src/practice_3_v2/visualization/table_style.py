from collections.abc import Callable, Mapping
from typing import Any

import pandas as pd
from pandas.io.formats.style import Styler


SELECTED_ROW_STYLE = (
    "background-color: #1f4e78; "
    "color: #ffffff; "
    "font-weight: 600; "
    "border-left: 4px solid #5b9bd5"
)

TABLE_STYLES = [
    {
        "selector": "table",
        "props": [
            ("color-scheme", "light dark"),
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
            ("color", "#5dade2"),
            ("font-size", "17px"),
            ("font-weight", "600"),
            ("padding", "10px"),
        ],
    },
    {
        "selector": "thead th",
        "props": [
            ("background-color", "#1f4e78"),
            ("color", "#f8fafc"),
            ("font-weight", "600"),
            ("padding", "10px 14px"),
            ("text-align", "center"),
            ("white-space", "nowrap"),
            ("border", "1px solid #5b9bd5"),
        ],
    },
    {
        "selector": "tbody td",
        "props": [
            ("background-color", "light-dark(#f8fafc, #1f1f1f)"),
            ("color", "light-dark(#172033, #e6edf5)"),
            ("padding", "9px 14px"),
            ("border", "0"),
            ("border-bottom", "1px solid light-dark(#d8e1eb, #3a3a3a)"),
            ("vertical-align", "top"),
        ],
    },
    {
        "selector": "tbody tr:nth-child(even) td",
        "props": [
            ("background-color", "rgba(91, 155, 213, 0.15)"),
        ],
    },
    {
        "selector": "tbody tr:hover td",
        "props": [
            ("background-color", "rgba(91, 155, 213, 0.30)"),
        ],
    },
    {
        "selector": "tbody td:first-child",
        "props": [
            ("font-weight", "500"),
        ],
    },
]


def style_table(
    dataframe: pd.DataFrame,
    formats: Mapping[str, Any] | None = None,
    row_highlighter: Callable[[pd.Series], list[str]] | None = None,
    caption: str | None = None,
) -> Styler:
    styled = dataframe.style.hide(axis="index").set_table_styles(TABLE_STYLES)
    if caption:
        styled = styled.set_caption(caption)
    if formats:
        styled = styled.format(formats)
    numeric_columns = list(dataframe.select_dtypes(include="number").columns)
    if numeric_columns:
        styled = styled.set_properties(
            subset=numeric_columns,
            **{
                "text-align": "right",
                "font-variant-numeric": "tabular-nums",
                "white-space": "nowrap",
            },
        )
    if row_highlighter is not None:
        styled = styled.apply(row_highlighter, axis=1)
    return styled
