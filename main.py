#!/usr/bin/env python3
"""IFRS9 ECL Pipeline — Main orchestrator.

Runs the full IFRS9 Expected Credit Loss workflow:
1. Generate/refresh synthetic portfolio (ifrs9_data.py)
2. Assign stages & calculate weighted ECL (ecl_engine.py)
3. Generate Plotly dashboard & charts (ifrs9_viz.py)

Usage:
    python main.py           # Normal mode
    python main.py --stress   # Stress mode (credit shocks + defaults)
"""
import argparse
import time

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def print_header(title: str):
    """Print a formatted section header."""
    line = "=" * 60
    print(f"\n{line}")
    print(f"  {title}")
    print(f"{line}")


def print_step(msg: str):
    """Print a step indicator."""
    print(f"  → {msg}")


def print_done(msg: str):
    """Print a completion message."""
    print(f"  ✓ {msg}")


# ---------------------------------------------------------------------------
# Pipeline Steps
# ---------------------------------------------------------------------------
def step_generate_portfolio(stress=False):
    """Step 1: Generate/refresh the loan portfolio."""
    mode_label = "STRESS MODE" if stress else "NORMAL MODE"
    print_header(f"STEP 1: Portfolio Generation ({mode_label})")
    print_step("Importing ifrs9_data module...")

    from src import ifrs9_data

    if stress:
        print_step("Creating 500 loans with credit shocks (volatility 0.5x-6x)...")
        print_step("Simulating 2% defaults (PD > 50%)...")
    else:
        print_step("Creating 500 synthetic loans...")
    
    rows = ifrs9_data.generate_portfolio(n=500, seed=42, stress=stress)

    print_step("Saving to data/ifrs9_portfolio.csv...")
    ifrs9_data.save_csv(rows, out_file="data/ifrs9_portfolio.csv")

    print_done(f"Portfolio generated: {len(rows)} loans saved.")


def step_calculate_ecl():
    """Step 2: Assign stages and calculate weighted ECL."""
    print_header("STEP 2: Classification & ECL Calculation")
    print_step("Importing ecl_engine module...")

    from src import ecl_engine

    print_step("Loading portfolio...")
    portfolio = ecl_engine.load_portfolio("data/ifrs9_portfolio.csv")
    print_done(f"{len(portfolio)} loans loaded.")

    print_step("Assigning IFRS9 Stages (1, 2, 3)...")
    print_step("Calculating weighted ECL (Optimistic 30%, Base 40%, Downturn 30%)...")
    results = ecl_engine.process_portfolio(portfolio)

    # Compute summary stats
    stage_counts = {1: 0, 2: 0, 3: 0}
    total_ecl = 0.0
    for r in results:
        stage_counts[r["Stage"]] += 1
        total_ecl += r["ECL"]

    print_done("Classification completed.")
    print(f"       Stage 1: {stage_counts[1]} loans")
    print(f"       Stage 2: {stage_counts[2]} loans")
    print(f"       Stage 3: {stage_counts[3]} loans")

    print_step("Saving to data/ifrs9_results.csv...")
    ecl_engine.save_results(results, "data/ifrs9_results.csv")

    print_done(f"Weighted ECL calculation completed. Total ECL: {total_ecl:,.2f}")


def step_generate_visualizations():
    """Step 3: Generate Plotly dashboard and charts."""
    print_header("STEP 3: Generating Visualizations")
    print_step("Importing ifrs9_viz module...")

    from src import ifrs9_viz

    print_step("Loading ECL results...")
    data = ifrs9_viz.load_results("data/ifrs9_results.csv")
    print_done(f"{len(data)} loans loaded for visualization.")

    print_step("Creating Sunburst chart (Sector → Stage)...")
    sunburst_fig = ifrs9_viz.create_sunburst(data)
    sunburst_fig.write_html("chart_sunburst.html")
    print_done("chart_sunburst.html generated.")

    print_step("Creating Bar Chart (ECL Base vs Downturn)...")
    bar_fig = ifrs9_viz.create_ecl_comparison_bar(data)
    bar_fig.write_html("chart_ecl_comparison.html")
    print_done("chart_ecl_comparison.html generated.")

    print_step("Creating KPI Cards (Provisions & Coverage)...")
    kpi_fig = ifrs9_viz.create_kpi_cards(data)
    kpi_fig.write_html("chart_kpi.html")
    print_done("chart_kpi.html generated.")

    print_step("Creating combined dashboard...")
    dashboard_fig = ifrs9_viz.create_dashboard(data)
    dashboard_fig.write_html("ifrs9_dashboard.html")
    print_done("ifrs9_dashboard.html generated.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="IFRS9 ECL Pipeline")
    parser.add_argument("--stress", action="store_true", 
                        help="Stress mode: credit shocks + 2%% defaults")
    args = parser.parse_args()

    start_time = time.time()

    mode_banner = " [STRESS MODE]" if args.stress else ""
    print("\n" + "█" * 60)
    print(f"       IFRS9 EXPECTED CREDIT LOSS — FULL PIPELINE{mode_banner}")
    print("█" * 60)

    # Execute pipeline steps
    step_generate_portfolio(stress=args.stress)
    step_calculate_ecl()
    step_generate_visualizations()

    # Final summary
    elapsed = time.time() - start_time
    print_header("PIPELINE COMPLETED")
    print(f"  Execution time: {elapsed:.2f} seconds")
    print()
    print("  Generated files:")
    print("    • data/ifrs9_portfolio.csv   — Loan portfolio")
    print("    • data/ifrs9_results.csv     — ECL results with Stages")
    print("    • ifrs9_dashboard.html       — Full interactive dashboard")
    print("    • chart_sunburst.html        — Sector/Stage breakdown")
    print("    • chart_ecl_comparison.html  — Base/Downturn comparison")
    print("    • chart_kpi.html             — Key performance indicators")
    print()
    print("  → Open ifrs9_dashboard.html in your browser.")
    print()


if __name__ == "__main__":
    main()
