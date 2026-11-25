import pandas as pd
import pytest

from practice_2.visualization.table_style import style_table


def test_style_table_adds_practice_theme_and_formats() -> None:
    dataframe = pd.DataFrame({"Partition": ["Train", "Test"], "Rows": [163, 41]})

    html = style_table(
        dataframe,
        caption="Chronological split",
        formats={"Rows": "{:,}"},
    ).to_html()

    assert "Chronological split" in html
    assert "background-color: #1f4e78" in html
    assert "font-variant-numeric: tabular-nums" in html
    assert "163" in html


def test_style_table_can_highlight_a_selected_row() -> None:
    dataframe = pd.DataFrame(
        {"Candidate": ["ARIMA", "Seasonal naive"], "Status": ["Draft", "Baseline"]}
    )

    def highlight_baseline(row: pd.Series) -> list[str]:
        if row["Status"] == "Baseline":
            return ["background-color: #dbeafe; font-weight: 600"] * len(row)
        return [""] * len(row)

    html = style_table(
        dataframe,
        caption="Candidate status",
        row_highlighter=highlight_baseline,
    ).to_html()

    assert "background-color: #dbeafe" in html


def test_style_table_rejects_invalid_input() -> None:
    with pytest.raises(TypeError, match="pandas DataFrame"):
        style_table([], caption="Invalid")

    with pytest.raises(ValueError, match="at least one row"):
        style_table(pd.DataFrame(), caption="Empty")
