#!/usr/bin/env python3
"""IFRS9 ECL Engine — Stage assignment and Expected Credit Loss calculation.

Loads ifrs9_portfolio.csv, assigns stages, computes ECL under 3 scenarios,
and outputs ifrs9_results.csv.

Usage: python ecl_engine.py
"""
import csv
from typing import List, Dict

# Scenario weights
SCENARIO_WEIGHTS = {
    "Optimistic": 0.30,
    "Base": 0.40,
    "Downturn": 0.30,
}

# PD multipliers per scenario
PD_MULTIPLIERS = {
    "Optimistic": 0.80,
    "Base": 1.00,
    "Downturn": 1.50,
}


def load_portfolio(filepath: str) -> List[Dict]:
    """Load portfolio CSV into a list of dicts with numeric conversion."""
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
            })
    return rows


def assign_stage(initial_pd: float, current_pd: float) -> int:
    """Assign IFRS9 stage based on PD deterioration.

    Rules (evaluated in order):
      - Stage 3 if Current_PD > 0.5 (default)
      - Stage 2 if Current_PD / Initial_PD > 3.0 (significant increase)
      - Stage 1 otherwise
    """
    if current_pd > 0.5:
        return 3
    if initial_pd > 0 and (current_pd / initial_pd) > 3.0:
        return 2
    return 1


def calculate_ecl(
    stage: int,
    current_pd: float,
    lgd: float,
    ead: float,
    maturity_years: int,
    eir: float,
    pd_multiplier: float = 1.0,
) -> float:
    """Compute ECL for a single loan under a given scenario.

    Stage 1: 12-month ECL = PD_12m * LGD * EAD
    Stage 2 & 3: Lifetime ECL = sum of discounted marginal losses.

    Args:
        stage: IFRS9 stage (1, 2, or 3)
        current_pd: annualised probability of default
        lgd: loss given default (e.g., 0.45)
        ead: exposure at default (principal)
        maturity_years: remaining time to maturity
        eir: effective interest rate for discounting
        pd_multiplier: scenario adjustment (0.8, 1.0, 1.5)

    Returns:
        Expected credit loss (currency units)
    """
    # Adjust PD for scenario, cap at 1.0
    pd_adj = min(current_pd * pd_multiplier, 1.0)

    if stage == 1:
        # 12-month ECL (1 year horizon)
        pd_12m = pd_adj  # already annual
        ecl = pd_12m * lgd * ead
    else:
        # Lifetime ECL: sum discounted marginal losses
        ecl = 0.0
        cum_survival = 1.0  # survival probability up to t-1
        for t in range(1, maturity_years + 1):
            # Marginal PD in year t = P(survive to t-1) * P(default in year t)
            marginal_pd = cum_survival * pd_adj
            discount_factor = 1.0 / ((1.0 + eir) ** t)
            ecl += marginal_pd * lgd * ead * discount_factor
            # Update cumulative survival
            cum_survival *= (1.0 - pd_adj)

    return round(ecl, 2)


def calculate_weighted_ecl(
    stage: int,
    current_pd: float,
    lgd: float,
    ead: float,
    maturity_years: int,
    eir: float,
) -> float:
    """Compute probability-weighted ECL across 3 macro scenarios."""
    weighted_ecl = 0.0
    for scenario, weight in SCENARIO_WEIGHTS.items():
        mult = PD_MULTIPLIERS[scenario]
        ecl_scenario = calculate_ecl(stage, current_pd, lgd, ead, maturity_years, eir, mult)
        weighted_ecl += weight * ecl_scenario
    return round(weighted_ecl, 2)


def process_portfolio(portfolio: List[Dict]) -> List[Dict]:
    """Assign stages and calculate ECL for each loan."""
    results = []
    for loan in portfolio:
        stage = assign_stage(loan["Initial_PD"], loan["Current_PD"])
        ecl = calculate_weighted_ecl(
            stage=stage,
            current_pd=loan["Current_PD"],
            lgd=loan["LGD"],
            ead=loan["Principal"],
            maturity_years=loan["Maturity_Years"],
            eir=loan["EIR"],
        )
        results.append({
            "Loan_ID": loan["Loan_ID"],
            "Sector": loan["Sector"],
            "Principal": loan["Principal"],
            "Initial_PD": loan["Initial_PD"],
            "Current_PD": loan["Current_PD"],
            "Maturity_Years": loan["Maturity_Years"],
            "EIR": loan["EIR"],
            "LGD": loan["LGD"],
            "Stage": stage,
            "ECL": ecl,
        })
    return results


def save_results(results: List[Dict], filepath: str):
    """Write results to CSV."""
    fieldnames = [
        "Loan_ID",
        "Sector",
        "Principal",
        "Initial_PD",
        "Current_PD",
        "Maturity_Years",
        "EIR",
        "LGD",
        "Stage",
        "ECL",
    ]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def main():
    input_file = "data/ifrs9_portfolio.csv"
    output_file = "data/ifrs9_results.csv"

    print(f"Loading portfolio from {input_file}...")
    portfolio = load_portfolio(input_file)
    print(f"  {len(portfolio)} loans loaded.")

    print("Assigning stages and calculating ECL...")
    results = process_portfolio(portfolio)

    # Summary statistics
    stage_counts = {1: 0, 2: 0, 3: 0}
    total_ecl = 0.0
    for r in results:
        stage_counts[r["Stage"]] += 1
        total_ecl += r["ECL"]

    print("\n--- Stage Distribution ---")
    for s in (1, 2, 3):
        print(f"  Stage {s}: {stage_counts[s]} loans")

    print(f"\n--- Total ECL: {total_ecl:,.2f} ---")

    print(f"\nSaving results to {output_file}...")
    save_results(results, output_file)
    print("Done.")


if __name__ == "__main__":
    main()
