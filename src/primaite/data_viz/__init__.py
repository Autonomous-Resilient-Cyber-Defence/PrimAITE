from enum import Enum


class PlotlyTemplate(Enum):
    """The built-in plotly templates."""

    PLOTLY = "plotly"
    PLOTLY_WHITE = "plotly_white"
    PLOTLY_DARK = "plotly_dark"
    GGPLOT2 = "ggplot2"
    SEABORN = "seaborn"
    SIMPLE_WHITE = "simple_white"
    NONE = "none"
