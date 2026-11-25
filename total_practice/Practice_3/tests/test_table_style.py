import pandas as pd

from practice_3.visualization.table_style import (
    SELECTED_ROW_STYLE,
    style_table,
)


def test_style_table_adds_theme_aware_presentation() -> None:
    dataframe = pd.DataFrame(
        [["Development", 112535], ["Holdout", 8761]],
        columns=["Partition", "Rows"],
    )
    html = style_table(
        dataframe,
        formats={"Rows": "{:,}"},
        caption="Dữ liệu ban đầu",
    ).to_html()
    assert "light-dark(#f8fafc, #1f1f1f)" in html
    assert "background-color: #1f4e78" in html
    assert "border: 1px solid #5b9bd5" in html
    assert "background-color: rgba(91, 155, 213, 0.15)" in html
    assert "background-color: rgba(91, 155, 213, 0.30)" in html
    assert "font-variant-numeric: tabular-nums" in html
    assert "112,535" in html
    assert "row_heading" not in html
    assert "Dữ liệu ban đầu" in html


def test_style_table_applies_selected_row_highlight() -> None:
    dataframe = pd.DataFrame(
        [["persistence", False], ["xgboost_tuned", True]],
        columns=["Candidate", "Selected"],
    )

    def highlight_selected(row: pd.Series) -> list[str]:
        return [SELECTED_ROW_STYLE if row["Selected"] else "" for _ in row]

    html = style_table(dataframe, row_highlighter=highlight_selected).to_html()
    assert "background-color: #1f4e78" in html
    assert "color: #ffffff" in html
    assert "border-left: 4px solid #5b9bd5" in html
