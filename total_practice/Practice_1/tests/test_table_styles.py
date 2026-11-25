import pandas as pd
import pytest

from practice_1.visualization import (
    boolean_cell_color,
    load_table_theme_css,
    visualise_table,
)


def test_table_theme_supports_light_and_dark_modes() -> None:
    css = load_table_theme_css()

    assert ".ts-data-table" in css
    assert "@media (prefers-color-scheme: dark)" in css
    assert "--jp-layout-color1" in css


def test_visualise_table_sets_caption_and_theme_class() -> None:
    frame = pd.DataFrame({"metric": [1.23456]})

    html = visualise_table(frame, "Diagnostic summary").to_html()

    assert 'class="ts-data-table"' in html
    assert "<caption>Diagnostic summary</caption>" in html
    assert "1.2346" in html


def test_visualise_table_rejects_empty_caption() -> None:
    with pytest.raises(ValueError, match="caption must not be empty"):
        visualise_table(pd.DataFrame({"metric": [1]}), "   ")


def test_boolean_cell_color_distinguishes_success_and_alert() -> None:
    assert "#dcfce7" in boolean_cell_color(True)
    assert "#fee2e2" in boolean_cell_color(False)
    assert "#fee2e2" in boolean_cell_color(True, alert=True)
    assert boolean_cell_color("True") == ""
