from collections.abc import Hashable, Sequence
from importlib.resources import files

import numpy as np
import pandas as pd
from pandas.io.formats.style import Styler


TABLE_CLASS = "ts-data-table"
THEME_RESOURCE = "table_theme.css"


def load_table_theme_css() -> str:
    """Load the adaptive Light/Dark table theme bundled with the package."""
    return (
        files("practice_1.visualization")
        .joinpath(THEME_RESOURCE)
        .read_text(encoding="utf-8")
    )


def enable_table_theme() -> None:
    """Inject the packaged table theme into the current notebook output."""
    from IPython.display import HTML, display

    display(HTML(f"<style>{load_table_theme_css()}</style>"))


def visualise_table(
    frame: pd.DataFrame,
    caption: str,
    *,
    hide_index: bool = True,
    precision: int = 10,
    gradient_columns: Sequence[Hashable] | None = None,
    gradient_axis: int | None = 0,
    gradient_cmap: str = "Blues",
) -> Styler:
    """Create a consistently formatted, theme-aware notebook table."""
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("frame must be a pandas DataFrame")
    if not caption.strip():
        raise ValueError("caption must not be empty")

    styled = (
        frame.style
        .set_caption(caption)
        .set_table_attributes(f'class="{TABLE_CLASS}"')
        .format(precision=precision, thousands=",", na_rep="—")
    )
    if hide_index:
        styled = styled.hide(axis="index")
    if gradient_columns:
        styled = styled.background_gradient(
            cmap=gradient_cmap,
            subset=list(gradient_columns),
            axis=gradient_axis,
        )
    return styled


def boolean_cell_color(value: object, *, alert: bool = False) -> str:
    """Return accessible success or alert colors for boolean table cells."""
    if not isinstance(value, (bool, np.bool_)):
        return ""
    if alert and value:
        return "background-color: #fee2e2; color: #991b1b; font-weight: 700;"
    if value:
        return "background-color: #dcfce7; color: #166534; font-weight: 700;"
    return "background-color: #fee2e2; color: #991b1b; font-weight: 700;"
