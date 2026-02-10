#!/usr/bin/env python3
"""IFRS9 Visualization Dashboard using Plotly.

Generates:
1. Sunburst chart: Portfolio by Sector → Stage
2. Bar chart: ECL comparison Base vs Downturn by Sector
3. KPI cards: Total provisions & average coverage ratio

Usage: python ifrs9_viz.py
"""
import csv
from typing import List, Dict
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ---------------------------------------------------------------------------
# ECL Calculation (duplicated from ecl_engine for scenario comparison)
# ---------------------------------------------------------------------------
def calculate_ecl_scenario(
    stage: int,
    current_pd: float,
    lgd: float,
    ead: float,
    maturity_years: int,
    eir: float,
    pd_multiplier: float,
) -> float:
    """Compute ECL under a specific scenario."""
    pd_adj = min(current_pd * pd_multiplier, 1.0)

    if stage == 1:
        ecl = pd_adj * lgd * ead
    else:
        ecl = 0.0
        cum_survival = 1.0
        for t in range(1, maturity_years + 1):
            marginal_pd = cum_survival * pd_adj
            discount_factor = 1.0 / ((1.0 + eir) ** t)
            ecl += marginal_pd * lgd * ead * discount_factor
            cum_survival *= (1.0 - pd_adj)
    return ecl


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------
def load_results(filepath: str = "data/ifrs9_results.csv") -> List[Dict]:
    """Load the ECL results CSV."""
    rows = []
    with open(filepath, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "Loan_ID": row["Loan_ID"],
                "Sector": row["Sector"],
                "Principal": float(row["Principal"]),
                "Initial_PD": float(row["Initial_PD"]),
                "Current_PD": float(row["Current_PD"]),
                "Maturity_Years": int(row["Maturity_Years"]),
                "EIR": float(row["EIR"]),
                "LGD": float(row["LGD"]),
                "Stage": int(row["Stage"]),
                "ECL": float(row["ECL"]),
            })
    return rows


# ---------------------------------------------------------------------------
# Chart 1: Sunburst — Sector → Stage
# ---------------------------------------------------------------------------
def create_sunburst(data: List[Dict]) -> go.Figure:
    """Create a sunburst chart showing Sector -> Stage hierarchy."""
    # Aggregate Principal by Sector and Stage
    agg = {}
    for row in data:
        key = (row["Sector"], row["Stage"])
        agg[key] = agg.get(key, 0) + row["Principal"]

    labels = ["Portfolio"]
    parents = [""]
    values = [sum(r["Principal"] for r in data)]

    # Sectors (level 1)
    sectors = sorted(set(r["Sector"] for r in data))
    for sector in sectors:
        sector_total = sum(r["Principal"] for r in data if r["Sector"] == sector)
        labels.append(sector)
        parents.append("Portfolio")
        values.append(sector_total)

    # Stages (level 2)
    for sector in sectors:
        for stage in (1, 2, 3):
            key = (sector, stage)
            if key in agg and agg[key] > 0:
                labels.append(f"Stage {stage}")
                parents.append(sector)
                values.append(agg[key])

    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        hovertemplate="<b>%{label}</b><br>Principal: %{value:,.0f}<extra></extra>",
        marker=dict(
            colors=values,
            colorscale="Blues",
        ),
    ))
    fig.update_layout(
        title=dict(text="Portfolio Breakdown by Sector → Stage", x=0.5),
        margin=dict(t=50, l=10, r=10, b=10),
    )
    return fig


# ---------------------------------------------------------------------------
# Chart 2: Bar Chart — ECL Base vs Downturn by Sector
# ---------------------------------------------------------------------------
def create_ecl_comparison_bar(data: List[Dict]) -> go.Figure:
    """Bar chart comparing ECL under Base vs Downturn scenarios by sector."""
    sectors = sorted(set(r["Sector"] for r in data))

    ecl_base = {s: 0.0 for s in sectors}
    ecl_downturn = {s: 0.0 for s in sectors}

    for row in data:
        sector = row["Sector"]
        base_ecl = calculate_ecl_scenario(
            stage=row["Stage"],
            current_pd=row["Current_PD"],
            lgd=row["LGD"],
            ead=row["Principal"],
            maturity_years=row["Maturity_Years"],
            eir=row["EIR"],
            pd_multiplier=1.0,  # Base
        )
        downturn_ecl = calculate_ecl_scenario(
            stage=row["Stage"],
            current_pd=row["Current_PD"],
            lgd=row["LGD"],
            ead=row["Principal"],
            maturity_years=row["Maturity_Years"],
            eir=row["EIR"],
            pd_multiplier=1.5,  # Downturn
        )
        ecl_base[sector] += base_ecl
        ecl_downturn[sector] += downturn_ecl

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Base",
        x=sectors,
        y=[ecl_base[s] for s in sectors],
        marker_color="#3498db",
        text=[f"{ecl_base[s]:,.0f}" for s in sectors],
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        name="Downturn",
        x=sectors,
        y=[ecl_downturn[s] for s in sectors],
        marker_color="#e74c3c",
        text=[f"{ecl_downturn[s]:,.0f}" for s in sectors],
        textposition="outside",
    ))
    fig.update_layout(
        title=dict(text="ECL Comparison: Base vs Downturn by Sector", x=0.5),
        xaxis_title="Sector",
        yaxis_title="ECL Amount",
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        margin=dict(t=80, l=60, r=30, b=50),
    )
    return fig


# ---------------------------------------------------------------------------
# Chart 3: KPI Cards — Total Provisions & Coverage Ratio
# ---------------------------------------------------------------------------
def create_kpi_cards(data: List[Dict]) -> go.Figure:
    """Create KPI indicator cards for total provisions and coverage ratio."""
    total_provisions = sum(r["ECL"] for r in data)
    total_exposure = sum(r["Principal"] for r in data)
    coverage_ratio = (total_provisions / total_exposure * 100) if total_exposure > 0 else 0

    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "indicator"}, {"type": "indicator"}]],
        horizontal_spacing=0.1,
    )

    # KPI 1: Total Provisions
    fig.add_trace(go.Indicator(
        mode="number",
        value=total_provisions,
        title=dict(text="<b>Total IFRS9 Provisions</b>", font=dict(size=18)),
        number=dict(
            prefix="€ ",
            valueformat=",.0f",
            font=dict(size=40, color="#2c3e50"),
        ),
        domain=dict(x=[0, 0.45], y=[0, 1]),
    ), row=1, col=1)

    # KPI 2: Coverage Ratio
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=coverage_ratio,
        title=dict(text="<b>Average Coverage Ratio</b>", font=dict(size=18)),
        number=dict(suffix=" %", font=dict(size=36, color="#2c3e50")),
        gauge=dict(
            axis=dict(range=[0, 5], ticksuffix=" %"),
            bar=dict(color="#27ae60"),
            bgcolor="white",
            borderwidth=2,
            bordercolor="#bdc3c7",
            steps=[
                dict(range=[0, 1], color="#e8f8f5"),
                dict(range=[1, 2], color="#a9dfbf"),
                dict(range=[2, 5], color="#f5b7b1"),
            ],
            threshold=dict(
                line=dict(color="#c0392b", width=4),
                thickness=0.75,
                value=coverage_ratio,
            ),
        ),
        domain=dict(x=[0.55, 1], y=[0, 1]),
    ), row=1, col=2)

    fig.update_layout(
        title=dict(text="IFRS9 Key Performance Indicators", x=0.5, font=dict(size=22)),
        margin=dict(t=80, l=30, r=30, b=30),
        paper_bgcolor="#f9f9f9",
    )
    return fig


# ---------------------------------------------------------------------------
# Combined Dashboard
# ---------------------------------------------------------------------------
def create_dashboard(data: List[Dict]) -> go.Figure:
    """Create a combined dashboard with all visualizations."""
    from plotly.subplots import make_subplots

    # We'll create individual figures and combine them in HTML
    # For a single figure layout, we use subplots with mixed types

    fig = make_subplots(
        rows=2, cols=2,
        specs=[
            [{"type": "sunburst"}, {"type": "xy"}],
            [{"type": "indicator"}, {"type": "indicator"}],
        ],
        subplot_titles=(
            "Portfolio by Sector → Stage",
            "ECL: Base vs Downturn by Sector",
            "",
            "",
        ),
        vertical_spacing=0.12,
        horizontal_spacing=0.08,
    )

    # --- Sunburst data ---
    agg = {}
    for row in data:
        key = (row["Sector"], row["Stage"])
        agg[key] = agg.get(key, 0) + row["Principal"]

    labels = ["Portfolio"]
    parents = [""]
    values = [sum(r["Principal"] for r in data)]

    sectors = sorted(set(r["Sector"] for r in data))
    for sector in sectors:
        sector_total = sum(r["Principal"] for r in data if r["Sector"] == sector)
        labels.append(sector)
        parents.append("Portfolio")
        values.append(sector_total)

    for sector in sectors:
        for stage in (1, 2, 3):
            key = (sector, stage)
            if key in agg and agg[key] > 0:
                labels.append(f"{sector} - Stage {stage}")
                parents.append(sector)
                values.append(agg[key])

    fig.add_trace(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        hovertemplate="<b>%{label}</b><br>Principal: %{value:,.0f}<extra></extra>",
        marker=dict(colorscale="Blues"),
    ), row=1, col=1)

    # --- Bar chart data ---
    ecl_base = {s: 0.0 for s in sectors}
    ecl_downturn = {s: 0.0 for s in sectors}

    for row in data:
        sector = row["Sector"]
        ecl_base[sector] += calculate_ecl_scenario(
            row["Stage"], row["Current_PD"], row["LGD"], row["Principal"],
            row["Maturity_Years"], row["EIR"], 1.0
        )
        ecl_downturn[sector] += calculate_ecl_scenario(
            row["Stage"], row["Current_PD"], row["LGD"], row["Principal"],
            row["Maturity_Years"], row["EIR"], 1.5
        )

    fig.add_trace(go.Bar(
        name="Base", x=sectors, y=[ecl_base[s] for s in sectors],
        marker_color="#3498db", showlegend=True,
    ), row=1, col=2)
    fig.add_trace(go.Bar(
        name="Downturn", x=sectors, y=[ecl_downturn[s] for s in sectors],
        marker_color="#e74c3c", showlegend=True,
    ), row=1, col=2)

    # --- KPIs ---
    total_provisions = sum(r["ECL"] for r in data)
    total_exposure = sum(r["Principal"] for r in data)
    coverage_ratio = (total_provisions / total_exposure * 100) if total_exposure > 0 else 0

    fig.add_trace(go.Indicator(
        mode="number",
        value=total_provisions,
        title=dict(text="<b>Total Provisions</b>", font=dict(size=16)),
        number=dict(prefix="€ ", valueformat=",.0f", font=dict(size=32, color="#2c3e50")),
    ), row=2, col=1)

    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=coverage_ratio,
        title=dict(text="<b>Coverage Ratio</b>", font=dict(size=16)),
        number=dict(suffix=" %", font=dict(size=28, color="#2c3e50")),
        gauge=dict(
            axis=dict(range=[0, 5], ticksuffix="%"),
            bar=dict(color="#27ae60"),
            steps=[
                dict(range=[0, 1], color="#e8f8f5"),
                dict(range=[1, 2], color="#a9dfbf"),
                dict(range=[2, 5], color="#f5b7b1"),
            ],
        ),
    ), row=2, col=2)

    fig.update_layout(
        title=dict(text="<b>IFRS9 ECL Dashboard</b>", x=0.5, font=dict(size=24)),
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.75),
        height=800,
        margin=dict(t=100, l=40, r=40, b=40),
        paper_bgcolor="#fafafa",
    )
    return fig


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("Loading IFRS9 results...")
    data = load_results("data/ifrs9_results.csv")
    print(f"  {len(data)} loans loaded.")

    print("\nGenerating visualizations...")

    # Individual charts (saved as separate HTML files)
    sunburst_fig = create_sunburst(data)
    sunburst_fig.write_html("chart_sunburst.html")
    print("  ✓ chart_sunburst.html")

    bar_fig = create_ecl_comparison_bar(data)
    bar_fig.write_html("chart_ecl_comparison.html")
    print("  ✓ chart_ecl_comparison.html")

    kpi_fig = create_kpi_cards(data)
    kpi_fig.write_html("chart_kpi.html")
    print("  ✓ chart_kpi.html")

    # Combined dashboard
    dashboard_fig = create_dashboard(data)
    dashboard_fig.write_html("ifrs9_dashboard.html")
    print("  ✓ ifrs9_dashboard.html (combined dashboard)")

    print("\nDone! Open ifrs9_dashboard.html in a browser to view the dashboard.")


if __name__ == "__main__":
    main()
