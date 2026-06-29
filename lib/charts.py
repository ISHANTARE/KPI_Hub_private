"""
lib/charts.py
-------------
Plotly figure builder functions for KPI Hub.

All builders:
  - Accept typed data parameters + optional overrides: dict
  - Return plotly.graph_objects.Figure
  - Never call any Streamlit function (st.*)
  - Use COLORS, CHART_DEFAULTS, STATUS_COLORS from lib.styling
  - Return annotated Figure on empty/None DataFrame input

Builders (implemented in task 5.2):
  build_portfolio_health_chart, build_schedule_status_chart,
  build_risk_matrix_chart, build_defect_trend_chart,
  build_test_execution_chart, build_resource_utilization_chart,
  build_monthly_utilization_chart, build_budget_variance_chart,
  build_aspice_radar_chart, build_traceability_heatmap_chart,
  build_kpi_gauge_chart, build_milestone_gantt_chart,
  build_defect_severity_chart, build_cost_burn_chart,
  build_dev_velocity_chart
"""

import logging
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

logger = logging.getLogger(__name__)

# ── Import styling tokens ──────────────────────────────────────────────────
# Raise ImportError naming the missing token if any import fails
try:
    from lib.styling import COLORS
except ImportError:
    raise ImportError("Cannot import COLORS from lib.styling")
try:
    from lib.styling import CHART_DEFAULTS
except ImportError:
    raise ImportError("Cannot import CHART_DEFAULTS from lib.styling")
try:
    from lib.styling import STATUS_COLORS
except ImportError:
    raise ImportError("Cannot import STATUS_COLORS from lib.styling")


# ── Infrastructure helpers ─────────────────────────────────────────────────

def _apply_overrides(fig: go.Figure, overrides: dict | None) -> go.Figure:
    """Apply update_layout keyword args from overrides dict to the figure."""
    if overrides:
        fig.update_layout(**overrides)
    return fig


def _empty_figure(message: str = "No data available", overrides: dict | None = None) -> go.Figure:
    """
    Return a blank Figure with a centred annotation describing the missing data.
    Used by all builder functions when input DataFrames are empty or None.
    """
    fig = go.Figure()
    # Build layout dict: start from CHART_DEFAULTS, then overlay empty-figure specifics
    layout = {
        **CHART_DEFAULTS,
        "annotations": [
            dict(
                text=message,
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=14, color=COLORS["text_muted"]),
            )
        ],
        "xaxis": dict(visible=False),
        "yaxis": dict(visible=False),
    }
    fig.update_layout(**layout)
    return _apply_overrides(fig, overrides)


def _is_empty(df) -> bool:
    """Return True if df is None or an empty DataFrame."""
    if df is None:
        return True
    if isinstance(df, pd.DataFrame) and df.empty:
        return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# 1. build_portfolio_health_chart
# ─────────────────────────────────────────────────────────────────────────────

def build_portfolio_health_chart(
    projects: pd.DataFrame,
    overrides: dict | None = None,
) -> go.Figure:
    """
    Bar chart: PROGRAM → mean HEALTH_SCORE, bars colored by status threshold.
    ≥75 = HEALTHY color, ≥60 = WATCHLIST color, else CRITICAL color.
    """
    if _is_empty(projects):
        return _empty_figure("No project data available", overrides)

    if "PROGRAM" not in projects.columns or "HEALTH_SCORE" not in projects.columns:
        return _empty_figure("Missing PROGRAM or HEALTH_SCORE column", overrides)

    domain_data = projects.groupby("PROGRAM")["HEALTH_SCORE"].mean().to_dict()
    domain_data = {k: (v if not pd.isna(v) else 0) for k, v in domain_data.items()}

    if not domain_data:
        return _empty_figure("No program health data", overrides)

    bar_colors = [
        STATUS_COLORS.get(
            "HEALTHY" if v >= 75 else ("WATCHLIST" if v >= 60 else "CRITICAL"),
            COLORS["blue"],
        )
        for v in domain_data.values()
    ]

    fig = go.Figure(data=[
        go.Bar(
            x=list(domain_data.keys()),
            y=list(domain_data.values()),
            marker=dict(color=bar_colors),
            text=[f"{v:.0f}%" for v in domain_data.values()],
            textposition="outside",
            textfont=dict(color=COLORS["text_secondary"], size=12, family="Inter, sans-serif"),
        )
    ])

    layout = dict(**CHART_DEFAULTS)
    layout["yaxis"] = dict(range=[0, 115], **CHART_DEFAULTS["yaxis"])
    layout["height"] = 300
    fig.update_layout(**layout)
    return _apply_overrides(fig, overrides)


# ─────────────────────────────────────────────────────────────────────────────
# 2. build_schedule_status_chart
# ─────────────────────────────────────────────────────────────────────────────

def build_schedule_status_chart(
    projects: pd.DataFrame,
    overrides: dict | None = None,
) -> go.Figure:
    """
    Donut chart: SCHEDULE_STATUS distribution (GREEN/YELLOW/RED) across projects.
    """
    if _is_empty(projects):
        return _empty_figure("No project data available", overrides)

    if "SCHEDULE_STATUS" not in projects.columns:
        return _empty_figure("Missing SCHEDULE_STATUS column", overrides)

    status_counts = projects["SCHEDULE_STATUS"].value_counts()
    if status_counts.empty:
        return _empty_figure("No schedule status data", overrides)

    fig = go.Figure(data=[
        go.Pie(
            labels=status_counts.index.tolist(),
            values=status_counts.values.tolist(),
            marker=dict(
                colors=[STATUS_COLORS.get(x, COLORS["text_muted"]) for x in status_counts.index],
            ),
            hole=0.6,
            textfont=dict(color=COLORS["text_secondary"], size=12, family="Inter, sans-serif"),
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
        )
    ])

    pie_layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"], family="Inter, sans-serif"),
        height=300,
        showlegend=True,
        legend=dict(font=dict(color=COLORS["text_secondary"], size=11), bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=8, b=8, l=0, r=0),
    )
    fig.update_layout(**pie_layout)
    return _apply_overrides(fig, overrides)


# ─────────────────────────────────────────────────────────────────────────────
# 3. build_risk_matrix_chart
# ─────────────────────────────────────────────────────────────────────────────

def build_risk_matrix_chart(
    risks: pd.DataFrame,
    overrides: dict | None = None,
) -> go.Figure:
    """
    Pie/donut chart: SEVERITY distribution across risks (Risk Distribution).
    Uses px.pie with hole=0.6, colored by STATUS_COLORS.
    """
    if _is_empty(risks):
        return _empty_figure("No risk data available", overrides)

    if "SEVERITY" not in risks.columns:
        return _empty_figure("Missing SEVERITY column", overrides)

    risk_counts = risks["SEVERITY"].value_counts()
    if risk_counts.empty:
        return _empty_figure("No risk severity data", overrides)

    fig = go.Figure(data=[
        go.Pie(
            labels=risk_counts.index.tolist(),
            values=risk_counts.values.tolist(),
            marker=dict(
                colors=[STATUS_COLORS.get(x, COLORS["text_muted"]) for x in risk_counts.index],
            ),
            hole=0.6,
            textfont=dict(color=COLORS["text_secondary"], size=12, family="Inter, sans-serif"),
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
        )
    ])

    pie_layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"], family="Inter, sans-serif"),
        height=300,
        showlegend=True,
        legend=dict(font=dict(color=COLORS["text_secondary"], size=11), bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=8, b=8, l=0, r=0),
    )
    fig.update_layout(**pie_layout)
    return _apply_overrides(fig, overrides)


# ─────────────────────────────────────────────────────────────────────────────
# 4. build_defect_trend_chart
# ─────────────────────────────────────────────────────────────────────────────

def build_defect_trend_chart(
    defect_trends: pd.DataFrame,
    overrides: dict | None = None,
) -> go.Figure:
    """
    Line chart: OPEN_DEFECTS over WEEK, summed across all projects.
    From web_app.py "Weekly Defect Trend" section.
    """
    if _is_empty(defect_trends):
        return _empty_figure("No defect trend data available", overrides)

    if "WEEK" not in defect_trends.columns or "OPEN_DEFECTS" not in defect_trends.columns:
        return _empty_figure("Missing WEEK or OPEN_DEFECTS column", overrides)

    trend_sum = defect_trends.groupby("WEEK")["OPEN_DEFECTS"].sum().reset_index()

    fig = px.line(
        trend_sum,
        x="WEEK",
        y="OPEN_DEFECTS",
        markers=True,
        color_discrete_sequence=["#ef4444"],
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#f8fafc",
        height=250,
        margin=dict(t=30, b=10, l=10, r=10),
        font=dict(color=COLORS["text_secondary"], family="Inter, sans-serif"),
        xaxis=dict(title="Week"),
        yaxis=dict(title="Open Defects"),
    )
    return _apply_overrides(fig, overrides)


# ─────────────────────────────────────────────────────────────────────────────
# 5. build_test_execution_chart
# ─────────────────────────────────────────────────────────────────────────────

def build_test_execution_chart(
    tests: pd.DataFrame,
    overrides: dict | None = None,
) -> go.Figure:
    """
    Donut chart: STATUS distribution across test executions (PASSED/FAILED/BLOCKED/etc.).
    From web_app.py "Test Execution Status" section.
    """
    if _is_empty(tests):
        return _empty_figure("No test execution data available", overrides)

    if "STATUS" not in tests.columns:
        return _empty_figure("Missing STATUS column", overrides)

    test_status = tests["STATUS"].value_counts()
    if test_status.empty:
        return _empty_figure("No test status data", overrides)

    fig = px.pie(
        names=test_status.index.tolist(),
        values=test_status.values.tolist(),
        color=test_status.index.tolist(),
        color_discrete_map={k: STATUS_COLORS.get(k, COLORS["text_muted"]) for k in test_status.index},
        hole=0.6,
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"], family="Inter, sans-serif"),
        margin=dict(t=8, b=8, l=0, r=0),
        showlegend=True,
        legend=dict(font=dict(color=COLORS["text_secondary"], size=11), bgcolor="rgba(0,0,0,0)"),
    )
    return _apply_overrides(fig, overrides)


# ─────────────────────────────────────────────────────────────────────────────
# 6. build_resource_utilization_chart
# ─────────────────────────────────────────────────────────────────────────────

def _parse_util_pct(val) -> float:
    """Parse a UTILIZATION_PCT string like '95%' or '118%' to float. Returns 0.0 on failure."""
    try:
        if pd.isna(val) or val is None:
            return 0.0
        s = str(val).replace("%", "").replace(">", "").strip()
        if "(" in s:
            s = s.split("(")[1].replace(")", "")
        return float(s)
    except Exception as e:
        logger.warning(f"Could not parse utilization percentage '{val}': {e}")
        return 0.0


def build_resource_utilization_chart(
    resources: pd.DataFrame,
    overrides: dict | None = None,
) -> go.Figure:
    """
    Bar chart: per TEAM_MEMBER UTILIZATION_PCT.
    Bars for >100% are highlighted in chart_critical red; others in chart_primary blue.
    """
    if _is_empty(resources):
        return _empty_figure("No resource allocation data available", overrides)

    if "TEAM_MEMBER" not in resources.columns or "UTILIZATION_PCT" not in resources.columns:
        return _empty_figure("Missing TEAM_MEMBER or UTILIZATION_PCT column", overrides)

    df = resources.copy()
    df["_util_num"] = df["UTILIZATION_PCT"].apply(_parse_util_pct)
    df = df.sort_values("_util_num", ascending=False)

    bar_colors = [
        COLORS["chart_critical"] if v > 100 else COLORS["chart_primary"]
        for v in df["_util_num"]
    ]

    fig = go.Figure(data=[
        go.Bar(
            x=df["TEAM_MEMBER"].tolist(),
            y=df["_util_num"].tolist(),
            marker=dict(color=bar_colors),
            text=[f"{v:.0f}%" for v in df["_util_num"]],
            textposition="outside",
            textfont=dict(color=COLORS["text_secondary"], size=11, family="Inter, sans-serif"),
        )
    ])

    layout = dict(**CHART_DEFAULTS)
    layout["height"] = 320
    layout["xaxis"] = dict(title="Team Member", tickangle=-30, **CHART_DEFAULTS["xaxis"])
    layout["yaxis"] = dict(title="Utilization %", range=[0, max(df["_util_num"].max() * 1.15, 120)],
                           **CHART_DEFAULTS["yaxis"])
    # Reference line at 100%
    fig.update_layout(**layout)
    fig.add_hline(y=100, line_dash="dash", line_color=COLORS["chart_critical"],
                  annotation_text="100%", annotation_position="right")
    return _apply_overrides(fig, overrides)


# ─────────────────────────────────────────────────────────────────────────────
# 7. build_monthly_utilization_chart
# ─────────────────────────────────────────────────────────────────────────────

_MONTH_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def build_monthly_utilization_chart(
    monthly_utilization: pd.DataFrame,
    month_range: list | None = None,
    overrides: dict | None = None,
) -> go.Figure:
    """
    Grouped bar: UTILIZATION_PCT by RESOURCE_ID × MONTH+YEAR.
    month_range is a list of (month_name, year) tuples. If empty/None, uses all data.
    """
    if _is_empty(monthly_utilization):
        return _empty_figure("No monthly utilization data available", overrides)

    required_cols = {"RESOURCE_ID", "MONTH", "YEAR", "UTILIZATION_PCT"}
    if not required_cols.issubset(set(monthly_utilization.columns)):
        return _empty_figure("Missing required columns for monthly utilization", overrides)

    df = monthly_utilization.copy()
    df["YEAR"] = df["YEAR"].astype(int)

    # Filter to month_range if provided
    if month_range:
        allowed = {(m, int(y)) for m, y in month_range}
        df = df[df.apply(lambda r: (r["MONTH"], int(r["YEAR"])) in allowed, axis=1)]

    if df.empty:
        return _empty_figure("No utilization data for the selected month range", overrides)

    # Build ordered month labels
    def _month_ord(row):
        try:
            return int(row["YEAR"]) * 100 + (_MONTH_ORDER.index(row["MONTH"]) + 1)
        except Exception:
            return 0

    df["_ord"] = df.apply(_month_ord, axis=1)
    df = df.sort_values("_ord")
    df["MONTH_YEAR"] = df["MONTH"].str[:3] + " " + df["YEAR"].astype(str).str[-2:]

    # Sum utilization per resource per month (decimal → percentage)
    pivot = (
        df.groupby(["RESOURCE_ID", "MONTH_YEAR"])["UTILIZATION_PCT"]
        .sum()
        .reset_index()
    )
    pivot["UTILIZATION_PCT"] = pivot["UTILIZATION_PCT"] * 100

    month_order = df["MONTH_YEAR"].unique().tolist()

    fig = px.bar(
        pivot,
        x="MONTH_YEAR",
        y="UTILIZATION_PCT",
        color="RESOURCE_ID",
        barmode="group",
        category_orders={"MONTH_YEAR": month_order},
        labels={"UTILIZATION_PCT": "Utilization %", "MONTH_YEAR": "Month"},
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"], family="Inter, sans-serif"),
        margin=dict(t=8, b=8, l=0, r=0),
        height=320,
        legend=dict(font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
    )
    fig.add_hline(y=100, line_dash="dash", line_color=COLORS["chart_critical"],
                  annotation_text="100%", annotation_position="right")
    return _apply_overrides(fig, overrides)


# ─────────────────────────────────────────────────────────────────────────────
# 8. build_budget_variance_chart
# ─────────────────────────────────────────────────────────────────────────────

def build_budget_variance_chart(
    budget: pd.DataFrame,
    overrides: dict | None = None,
) -> go.Figure:
    """
    Grouped bar chart: PLANNED_AMOUNT vs SPENT_AMOUNT by BUDGET_CATEGORY.
    Uses COLORS["chart_primary"] for planned, COLORS["chart_critical"] for spent.
    """
    if _is_empty(budget):
        return _empty_figure("No budget data available", overrides)

    required_cols = {"BUDGET_CATEGORY", "PLANNED_AMOUNT", "SPENT_AMOUNT"}
    if not required_cols.issubset(set(budget.columns)):
        return _empty_figure("Missing BUDGET_CATEGORY, PLANNED_AMOUNT, or SPENT_AMOUNT column", overrides)

    df = budget.copy()
    df["PLANNED_AMOUNT"] = pd.to_numeric(df["PLANNED_AMOUNT"], errors="coerce").fillna(0)
    df["SPENT_AMOUNT"] = pd.to_numeric(df["SPENT_AMOUNT"], errors="coerce").fillna(0)
    grp = df.groupby("BUDGET_CATEGORY")[["PLANNED_AMOUNT", "SPENT_AMOUNT"]].sum().reset_index()

    fig = go.Figure(data=[
        go.Bar(
            name="Planned",
            x=grp["BUDGET_CATEGORY"].tolist(),
            y=grp["PLANNED_AMOUNT"].tolist(),
            marker_color=COLORS["chart_primary"],
            text=[f"€{v:,.0f}" for v in grp["PLANNED_AMOUNT"]],
            textposition="outside",
            textfont=dict(size=10, color=COLORS["text_secondary"]),
        ),
        go.Bar(
            name="Spent",
            x=grp["BUDGET_CATEGORY"].tolist(),
            y=grp["SPENT_AMOUNT"].tolist(),
            marker_color=COLORS["chart_critical"],
            text=[f"€{v:,.0f}" for v in grp["SPENT_AMOUNT"]],
            textposition="outside",
            textfont=dict(size=10, color=COLORS["text_secondary"]),
        ),
    ])

    layout = dict(**CHART_DEFAULTS)
    layout["barmode"] = "group"
    layout["height"] = 320
    layout["showlegend"] = True
    layout["legend"] = dict(font=dict(size=11, color=COLORS["text_secondary"]), bgcolor="rgba(0,0,0,0)")
    layout["yaxis"] = dict(title="Amount (€)", **CHART_DEFAULTS["yaxis"])
    layout["xaxis"] = dict(title="Budget Category", tickangle=-20, **CHART_DEFAULTS["xaxis"])
    fig.update_layout(**layout)
    return _apply_overrides(fig, overrides)


# ─────────────────────────────────────────────────────────────────────────────
# 9. build_aspice_radar_chart
# ─────────────────────────────────────────────────────────────────────────────

def _aspice_level_to_num(val) -> float:
    """Convert 'Level 0', 'Level 1', ... 'Level 5' to float 0..5. Returns 0.0 on failure."""
    try:
        s = str(val).strip()
        # Handle plain integer strings
        if s.isdigit():
            return float(s)
        # Handle "Level N" pattern
        parts = s.split()
        if len(parts) >= 2 and parts[0].lower() == "level":
            return float(parts[1])
    except Exception:
        pass
    return 0.0


def build_aspice_radar_chart(
    aspice: pd.DataFrame,
    project_id: str | None = None,
    overrides: dict | None = None,
) -> go.Figure:
    """
    Radar/polar chart: CURRENT_LEVEL vs TARGET_LEVEL per ASPICE_PROCESS.
    Optionally filtered by project_id.
    """
    if _is_empty(aspice):
        return _empty_figure("No ASPICE data available", overrides)

    required_cols = {"ASPICE_PROCESS", "CURRENT_LEVEL", "TARGET_LEVEL"}
    if not required_cols.issubset(set(aspice.columns)):
        return _empty_figure("Missing required ASPICE columns", overrides)

    df = aspice.copy()
    if project_id and "PROJECT_ID" in df.columns:
        df = df[df["PROJECT_ID"] == project_id]
    if df.empty:
        return _empty_figure(f"No ASPICE data for project {project_id}", overrides)

    # Aggregate: mean levels per process (in case of duplicates)
    df["_current"] = df["CURRENT_LEVEL"].apply(_aspice_level_to_num)
    df["_target"] = df["TARGET_LEVEL"].apply(_aspice_level_to_num)
    grp = df.groupby("ASPICE_PROCESS")[["_current", "_target"]].mean().reset_index()

    processes = grp["ASPICE_PROCESS"].tolist()
    # Close the radar loop
    processes_loop = processes + [processes[0]] if processes else processes
    current_vals = grp["_current"].tolist()
    current_loop = current_vals + [current_vals[0]] if current_vals else current_vals
    target_vals = grp["_target"].tolist()
    target_loop = target_vals + [target_vals[0]] if target_vals else target_vals

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=target_loop,
        theta=processes_loop,
        fill="toself",
        fillcolor=f"rgba(29,78,216,0.10)",
        line=dict(color=COLORS["chart_primary"], width=2, dash="dash"),
        name="Target Level",
    ))
    fig.add_trace(go.Scatterpolar(
        r=current_loop,
        theta=processes_loop,
        fill="toself",
        fillcolor=f"rgba(22,128,60,0.15)",
        line=dict(color=COLORS["chart_positive"], width=2),
        name="Current Level",
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                tickvals=[0, 1, 2, 3, 4, 5],
                tickfont=dict(size=9, color=COLORS["text_muted"]),
                gridcolor=COLORS["border"],
            ),
            angularaxis=dict(
                tickfont=dict(size=10, color=COLORS["text_secondary"]),
            ),
            bgcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"], family="Inter, sans-serif"),
        showlegend=True,
        legend=dict(font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=40, b=20, l=40, r=40),
        height=380,
    )
    return _apply_overrides(fig, overrides)


# ─────────────────────────────────────────────────────────────────────────────
# 10. build_traceability_heatmap_chart
# ─────────────────────────────────────────────────────────────────────────────

def build_traceability_heatmap_chart(
    traceability_insights: pd.DataFrame,
    overrides: dict | None = None,
) -> go.Figure:
    """
    Heatmap: ISSUE_TYPE counts by PROJECT_ID × ISSUE_CATEGORY (pivot table).
    """
    if _is_empty(traceability_insights):
        return _empty_figure("No traceability data available", overrides)

    required_cols = {"PROJECT_ID", "ISSUE_CATEGORY", "ISSUE_TYPE"}
    if not required_cols.issubset(set(traceability_insights.columns)):
        return _empty_figure("Missing required traceability columns", overrides)

    # Build pivot: rows=PROJECT_ID, columns=ISSUE_CATEGORY, values=count of ISSUE_TYPE
    df = traceability_insights.copy()
    pivot = (
        df.groupby(["PROJECT_ID", "ISSUE_CATEGORY"])
        .size()
        .unstack(fill_value=0)
    )

    if pivot.empty:
        return _empty_figure("No traceability issues to display", overrides)

    z = pivot.values.tolist()
    x = pivot.columns.tolist()
    y = pivot.index.tolist()

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=x,
        y=y,
        colorscale=[
            [0.0, COLORS["surface_raised"]],
            [0.5, COLORS["chart_warning"]],
            [1.0, COLORS["chart_critical"]],
        ],
        hoverongaps=False,
        hovertemplate="Project: %{y}<br>Category: %{x}<br>Count: %{z}<extra></extra>",
        showscale=True,
        colorbar=dict(
            tickfont=dict(color=COLORS["text_secondary"], size=10),
            outlinecolor=COLORS["border"],
        ),
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"], family="Inter, sans-serif"),
        xaxis=dict(title="Issue Category", tickangle=-20),
        yaxis=dict(title="Project ID"),
        margin=dict(t=8, b=8, l=0, r=0),
        height=max(280, len(y) * 40 + 80),
    )
    return _apply_overrides(fig, overrides)


# ─────────────────────────────────────────────────────────────────────────────
# 11. build_kpi_gauge_chart
# ─────────────────────────────────────────────────────────────────────────────

def build_kpi_gauge_chart(
    value: float,
    title: str,
    max_val: float = 100.0,
    overrides: dict | None = None,
) -> go.Figure:
    """
    Gauge indicator: single KPI value.
    Color thresholds: <60=red, <75=amber, <90=blue, else green.
    """
    if value is None:
        return _empty_figure("No KPI value provided", overrides)

    if value < 60:
        bar_color = COLORS["chart_critical"]
    elif value < 75:
        bar_color = COLORS["chart_warning"]
    elif value < 90:
        bar_color = COLORS["chart_primary"]
    else:
        bar_color = COLORS["chart_positive"]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title=dict(text=title, font=dict(size=14, color=COLORS["text_secondary"], family="Inter, sans-serif")),
        number=dict(
            font=dict(size=28, color=COLORS["text_primary"], family="Inter, sans-serif"),
            suffix="%",
        ),
        gauge=dict(
            axis=dict(
                range=[0, max_val],
                tickwidth=1,
                tickcolor=COLORS["border"],
                tickfont=dict(size=10, color=COLORS["text_muted"]),
            ),
            bar=dict(color=bar_color, thickness=0.6),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=1,
            bordercolor=COLORS["border"],
            steps=[
                dict(range=[0, 60], color=f"rgba(220,38,38,0.08)"),
                dict(range=[60, 75], color=f"rgba(217,119,6,0.08)"),
                dict(range=[75, 90], color=f"rgba(29,78,216,0.08)"),
                dict(range=[90, max_val], color=f"rgba(22,128,60,0.08)"),
            ],
            threshold=dict(
                line=dict(color=bar_color, width=3),
                thickness=0.8,
                value=value,
            ),
        ),
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=COLORS["text_secondary"]),
        margin=dict(t=20, b=10, l=10, r=10),
        height=220,
    )
    return _apply_overrides(fig, overrides)


# ─────────────────────────────────────────────────────────────────────────────
# 12. build_milestone_gantt_chart
# ─────────────────────────────────────────────────────────────────────────────

def build_milestone_gantt_chart(
    milestones: pd.DataFrame,
    proj_to_mgr: dict | None = None,
    overrides: dict | None = None,
) -> go.Figure:
    """
    Timeline/Gantt bar chart.
    Uses px.timeline if both PLANNED_DATE and ACTUAL_DATE columns exist;
    otherwise a horizontal bar chart using PLANNED_DATE as the x-axis.
    STATUS drives color. PROJECT_ID is the y-axis.
    """
    if _is_empty(milestones):
        return _empty_figure("No milestone data available", overrides)

    if "PLANNED_DATE" not in milestones.columns:
        return _empty_figure("Missing PLANNED_DATE column", overrides)

    df = milestones.copy()
    df["PLANNED_DATE"] = pd.to_datetime(df["PLANNED_DATE"], errors="coerce")

    # Optionally enrich with manager
    if proj_to_mgr and "PROJECT_ID" in df.columns:
        df["PROJECT_MANAGER"] = df["PROJECT_ID"].map(proj_to_mgr).fillna("Unknown")
    else:
        df["PROJECT_MANAGER"] = df.get("PROJECT_ID", "Unknown")

    # Map STATUS to color
    status_col = "STATUS" if "STATUS" in df.columns else None
    color_map = {
        "COMPLETED": STATUS_COLORS.get("GREEN", "#16803C"),
        "IN_PROGRESS": STATUS_COLORS.get("YELLOW", "#D97706"),
        "ON_TRACK": STATUS_COLORS.get("GREEN", "#16803C"),
        "AT_RISK": STATUS_COLORS.get("HIGH", "#D97706"),
        "DELAYED": STATUS_COLORS.get("RED", "#DC2626"),
        "OVERDUE": STATUS_COLORS.get("CRITICAL", "#DC2626"),
    }

    has_actual = "ACTUAL_DATE" in df.columns
    if has_actual:
        df["ACTUAL_DATE"] = pd.to_datetime(df["ACTUAL_DATE"], errors="coerce")
        # For px.timeline we need a start and end; use PLANNED_DATE as start, ACTUAL_DATE (or same day) as finish
        df["_finish"] = df["ACTUAL_DATE"].fillna(df["PLANNED_DATE"])
        # Avoid zero-length bars: add 1 day where start == finish
        same = df["PLANNED_DATE"] == df["_finish"]
        df.loc[same, "_finish"] = df.loc[same, "PLANNED_DATE"] + pd.Timedelta(days=1)

        y_col = "PROJECT_ID" if "PROJECT_ID" in df.columns else df.columns[0]
        name_col = "MILESTONE_NAME" if "MILESTONE_NAME" in df.columns else None
        hover = [name_col] if name_col else None

        try:
            fig = px.timeline(
                df.dropna(subset=["PLANNED_DATE"]),
                x_start="PLANNED_DATE",
                x_end="_finish",
                y=y_col,
                color=status_col if status_col else None,
                color_discrete_map=color_map,
                hover_name=name_col,
                hover_data=hover,
            )
            fig.update_yaxes(autorange="reversed")
        except Exception:
            has_actual = False  # fall back to bar

    if not has_actual:
        # Simple scatter/bar chart using PLANNED_DATE
        y_col = "PROJECT_ID" if "PROJECT_ID" in df.columns else df.columns[0]
        name_col = "MILESTONE_NAME" if "MILESTONE_NAME" in df.columns else None
        fig = px.scatter(
            df.dropna(subset=["PLANNED_DATE"]),
            x="PLANNED_DATE",
            y=y_col,
            color=status_col if status_col else None,
            color_discrete_map=color_map,
            symbol=name_col if name_col else None,
            hover_name=name_col,
            size_max=12,
        )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"], family="Inter, sans-serif"),
        margin=dict(t=8, b=8, l=0, r=0),
        height=max(300, len(df["PROJECT_ID"].unique()) * 50 + 80) if "PROJECT_ID" in df.columns else 300,
        showlegend=True,
        legend=dict(font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(title="Date"),
        yaxis=dict(title="Project"),
    )
    return _apply_overrides(fig, overrides)


# ─────────────────────────────────────────────────────────────────────────────
# 13. build_defect_severity_chart
# ─────────────────────────────────────────────────────────────────────────────

def build_defect_severity_chart(
    defects: pd.DataFrame,
    overrides: dict | None = None,
) -> go.Figure:
    """
    Donut chart: SEVERITY distribution across defects.
    From web_app.py "Defect Severity Distribution" section.
    """
    if _is_empty(defects):
        return _empty_figure("No defect data available", overrides)

    if "SEVERITY" not in defects.columns:
        return _empty_figure("Missing SEVERITY column", overrides)

    defect_sev = defects["SEVERITY"].value_counts()
    if defect_sev.empty:
        return _empty_figure("No defect severity data", overrides)

    fig = px.pie(
        names=defect_sev.index.tolist(),
        values=defect_sev.values.tolist(),
        color=defect_sev.index.tolist(),
        color_discrete_map={k: STATUS_COLORS.get(k, COLORS["text_muted"]) for k in defect_sev.index},
        hole=0.6,
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"], family="Inter, sans-serif"),
        margin=dict(t=8, b=8, l=0, r=0),
        showlegend=True,
        legend=dict(font=dict(color=COLORS["text_secondary"], size=11), bgcolor="rgba(0,0,0,0)"),
    )
    return _apply_overrides(fig, overrides)


# ─────────────────────────────────────────────────────────────────────────────
# 14. build_cost_burn_chart
# ─────────────────────────────────────────────────────────────────────────────

def build_cost_burn_chart(
    budget: pd.DataFrame,
    overrides: dict | None = None,
) -> go.Figure:
    """
    Line chart: cumulative SPENT_AMOUNT vs PLANNED_AMOUNT over BUDGET_PERIOD.
    Sorts by BUDGET_PERIOD and computes cumulative sums.
    """
    if _is_empty(budget):
        return _empty_figure("No budget data available", overrides)

    required_cols = {"BUDGET_PERIOD", "PLANNED_AMOUNT", "SPENT_AMOUNT"}
    if not required_cols.issubset(set(budget.columns)):
        return _empty_figure("Missing BUDGET_PERIOD, PLANNED_AMOUNT, or SPENT_AMOUNT column", overrides)

    df = budget.copy()
    df["PLANNED_AMOUNT"] = pd.to_numeric(df["PLANNED_AMOUNT"], errors="coerce").fillna(0)
    df["SPENT_AMOUNT"] = pd.to_numeric(df["SPENT_AMOUNT"], errors="coerce").fillna(0)
    grp = df.groupby("BUDGET_PERIOD")[["PLANNED_AMOUNT", "SPENT_AMOUNT"]].sum().reset_index()
    grp = grp.sort_values("BUDGET_PERIOD")

    grp["CUM_PLANNED"] = grp["PLANNED_AMOUNT"].cumsum()
    grp["CUM_SPENT"] = grp["SPENT_AMOUNT"].cumsum()
    periods = grp["BUDGET_PERIOD"].tolist()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=periods,
        y=grp["SPENT_AMOUNT"].tolist(),
        name="Monthly Spend",
        marker_color="rgba(29,78,216,0.45)",
        yaxis="y",
    ))
    fig.add_trace(go.Scatter(
        x=periods,
        y=grp["CUM_SPENT"].tolist(),
        name="Cumulative Spent",
        mode="lines+markers",
        line=dict(color=COLORS["chart_critical"], width=2),
        yaxis="y",
    ))
    fig.add_trace(go.Scatter(
        x=periods,
        y=grp["CUM_PLANNED"].tolist(),
        name="Cumulative Planned",
        mode="lines",
        line=dict(color=COLORS["chart_primary"], width=2, dash="dash"),
        yaxis="y",
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#f8fafc",
        font=dict(color=COLORS["text_secondary"], family="Inter, sans-serif"),
        xaxis=dict(title="Budget Period", gridcolor=COLORS["border"]),
        yaxis=dict(title="Cost (€)", gridcolor=COLORS["border"]),
        legend=dict(orientation="h", y=1.08, x=0, font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=40, b=20, l=20, r=20),
        height=320,
        showlegend=True,
    )
    return _apply_overrides(fig, overrides)


# ─────────────────────────────────────────────────────────────────────────────
# 15. build_dev_velocity_chart
# ─────────────────────────────────────────────────────────────────────────────

def build_dev_velocity_chart(
    dev_metrics: pd.DataFrame,
    overrides: dict | None = None,
) -> go.Figure:
    """
    Multi-line chart: COMMITS_COUNT by WEEK_START, colored by PROJECT_ID.
    From web_app.py "Weekly Commit Count Trends" section.
    """
    if _is_empty(dev_metrics):
        return _empty_figure("No development metrics data available", overrides)

    required_cols = {"WEEK_START", "COMMITS_COUNT", "PROJECT_ID"}
    if not required_cols.issubset(set(dev_metrics.columns)):
        return _empty_figure("Missing WEEK_START, COMMITS_COUNT, or PROJECT_ID column", overrides)

    fig = px.line(
        dev_metrics,
        x="WEEK_START",
        y="COMMITS_COUNT",
        color="PROJECT_ID",
        markers=True,
        color_discrete_sequence=[
            COLORS["chart_primary"],
            COLORS["chart_positive"],
            COLORS["chart_warning"],
            COLORS["chart_critical"],
            COLORS["chart_secondary"],
        ],
        labels={"WEEK_START": "Week", "COMMITS_COUNT": "Commits", "PROJECT_ID": "Project"},
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"], family="Inter, sans-serif"),
        margin=dict(t=8, b=8, l=0, r=0),
        showlegend=True,
        legend=dict(font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(title="Week", gridcolor=COLORS["border"]),
        yaxis=dict(title="Commits", gridcolor=COLORS["border"]),
        height=300,
    )
    return _apply_overrides(fig, overrides)
