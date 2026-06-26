"""
lib/styling.py
--------------
Design system for the KPI Hub dashboard.

Provides:
  - COLORS          : token dict (shared with charting code)
  - CHART_DEFAULTS  : standard Plotly layout kwargs
  - load_css()      : inject lib/styles.css into Streamlit
  - render_page_header()  : consistent page title block
  - badge()               : status badge HTML
  - escalation_panel()    : escalation flag strip HTML
"""

from pathlib import Path
from datetime import datetime
import streamlit as st

# ── Color tokens (mirrors :root in styles.css) ─────────────────────────────
COLORS = {
    # Backgrounds
    "bg":             "#F4F6F9",
    "surface":        "#FFFFFF",
    "surface_raised": "#F8FAFC",
    "border":         "#DDE3EC",
    "border_strong":  "#B8C4D4",
    # Typography
    "text_primary":   "#0F1923",
    "text_secondary": "#4A5568",
    "text_muted":     "#8896A7",
    # Status
    "green":          "#16803C",
    "green_bg":       "#F0FAF4",
    "amber":          "#B45309",
    "amber_bg":       "#FFFBEB",
    "red":            "#B91C1C",
    "red_bg":         "#FEF2F2",
    "blue":           "#1D4ED8",
    "blue_bg":        "#EFF6FF",
    # Chart series
    "chart_primary":  "#1D4ED8",
    "chart_secondary":"#64748B",
    "chart_positive": "#16803C",
    "chart_warning":  "#D97706",
    "chart_critical": "#DC2626",
    "chart_neutral":  "#E2E8F0",
    # Sidebar (kept for any inline references)
    "sidebar_bg":     "#0F1923",
}

# ── Standard Plotly layout kwargs ──────────────────────────────────────────
CHART_DEFAULTS = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor":  "rgba(0,0,0,0)",
    "font":          {"family": "Inter, sans-serif", "color": "#4A5568"},
    "margin":        {"t": 8, "b": 8, "l": 0, "r": 0},
    "xaxis": {
        "gridcolor":  "#E2E8F0",
        "linecolor":  "#DDE3EC",
        "showgrid":   True,
        "gridwidth":  0.5,
    },
    "yaxis": {
        "gridcolor":  "#E2E8F0",
        "linecolor":  "#DDE3EC",
        "showgrid":   True,
        "gridwidth":  0.5,
    },
    "showlegend": False,
}

# ── Chart color sequences ───────────────────────────────────────────────────
STATUS_COLORS = {
    "CRITICAL": "#DC2626",
    "HIGH":     "#D97706",
    "MEDIUM":   "#B45309",
    "LOW":      "#16803C",
    "PASSED":   "#16803C",
    "FAILED":   "#DC2626",
    "BLOCKED":  "#D97706",
    "NOT_EXECUTED": "#CBD5E1",
    "GREEN":    "#16803C",
    "YELLOW":   "#D97706",
    "RED":      "#DC2626",
    "EXCELLENT":"#16803C",
    "HEALTHY":  "#1D4ED8",
    "WATCHLIST":"#D97706",
}


def load_css() -> None:
    """Inject lib/styles.css into the Streamlit page."""
    css_path = Path(__file__).parent / "styles.css"
    if css_path.exists():
        css_text = css_path.read_text(encoding="utf-8")
        st.markdown(f"<style>{css_text}</style>", unsafe_allow_html=True)
    else:
        st.warning("styles.css not found — UI may appear unstyled.")


def render_page_header(title: str, description: str = "", last_synced: bool = True) -> None:
    """
    Render a consistent page title block.

    Args:
        title:       Page name (e.g. "Portfolio Overview")
        description: One-line context string shown below the title.
        last_synced: Whether to show a 'Last synced' timestamp.
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M") if last_synced else ""
    ts_html = (
        f'<span class="page-meta" style="float:right;">'
        f'<span class="sync-dot"></span>Last synced {ts}'
        f'</span>'
    ) if ts else ""

    desc_html = (
        f'<div class="page-meta" style="margin-top:3px;">{description}</div>'
    ) if description else ""

    st.markdown(
        f'<div style="overflow:hidden;">'
        f'{ts_html}'
        f'<div class="page-title">{title}</div>'
        f'{desc_html}'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.divider()


def badge(label: str, variant: str = "blue") -> str:
    """
    Return an HTML badge string.

    Args:
        label:   Text to display (will be uppercased by CSS).
        variant: One of 'red', 'amber', 'green', 'blue'.

    Returns:
        HTML string — use inside st.markdown(..., unsafe_allow_html=True)
    """
    v = variant.lower()
    if v not in ("red", "amber", "green", "blue"):
        v = "blue"
    return f'<span class="badge badge-{v}">{label}</span>'


def severity_badge(severity: str) -> str:
    """Map a severity/status string to a badge HTML snippet."""
    s = severity.upper()
    if s in ("CRITICAL", "FAILED", "RED", "OVERDUE"):
        return badge(s, "red")
    if s in ("HIGH", "BLOCKED", "YELLOW", "AT_RISK", "WATCHLIST"):
        return badge(s, "amber")
    if s in ("LOW", "PASSED", "GREEN", "READY", "COMPLETED", "EXCELLENT"):
        return badge(s, "green")
    return badge(s, "blue")


def escalation_panel(items: list[dict]) -> str:
    """
    Build an escalation panel HTML strip.

    Args:
        items: List of dicts with keys 'value' (int/str), 'label' (str),
               and optionally 'description' (str).
               If all values are 0, the panel renders in 'clear' style.

    Returns:
        HTML string.
    """
    all_clear = all(int(i.get("value", 0)) == 0 for i in items)
    panel_class = "escalation-panel clear" if all_clear else "escalation-panel"

    cells = []
    for item in items:
        val = item.get("value", 0)
        label = item.get("label", "")
        desc = item.get("description", "")
        value_class = "escalation-value clear" if all_clear else "escalation-value"
        desc_html = f'<div class="escalation-desc">{desc}</div>' if desc else ""
        cells.append(
            f'<div>'
            f'<div class="escalation-label">{label}</div>'
            f'<div class="{value_class}">{val}</div>'
            f'{desc_html}'
            f'</div>'
        )

    header = (
        '<div style="font-size:11px;font-weight:600;text-transform:uppercase;'
        'letter-spacing:0.5px;color:#8896A7;white-space:nowrap;">Escalation Flags</div>'
    )
    content = "".join(cells)
    return (
        f'<div class="{panel_class}">'
        f'{header}'
        f'<div style="display:flex;gap:32px;align-items:flex-start;">{content}</div>'
        f'</div>'
    )
