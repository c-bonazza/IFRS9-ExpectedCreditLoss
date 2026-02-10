#!/usr/bin/env python3
"""Generate a synthetic IFRS9 loan portfolio CSV.

Creates `ifrs9_portfolio.csv` with 500 loans (default). Columns:
- Loan_ID, Sector, Principal (EAD), Initial_PD, Current_PD,
  Maturity_Years, EIR, LGD, Stage

Usage: python ifrs9_data.py [--n N] [--out FILE]
"""
import csv
import math
import random
import argparse


def generate_portfolio(n=500, seed=42, stress=False):
    """Generate synthetic loan portfolio.
    
    Args:
        n: Number of loans to generate
        seed: Random seed for reproducibility
        stress: If True, apply credit shocks (higher PD volatility + defaults)
    """
    random.seed(seed)
    sectors = [
        "Retail",
        "Corporate",
        "SME",
        "Mortgage",
        "Consumer",
        "Sovereign",
    ]

    rows = []
    min_principal = 5_000
    max_principal = 5_000_000
    log_min = math.log10(min_principal)
    log_max = math.log10(max_principal)

    for i in range(1, n + 1):
        loan_id = f"LOAN{i:05d}"
        sector = random.choice(sectors)

        # Principal (log-uniform to create a realistic skewed distribution)
        principal = int(10 ** random.uniform(log_min, log_max))

        # Initial PD sampled from a Beta distribution and scaled to [0, 0.20]
        initial_pd = round(random.betavariate(0.8, 10) * 0.20, 4)
        initial_pd = max(initial_pd, 0.0001)

        # Current PD: apply stress or normal volatility
        if stress:
            # Stress mode: shocks from -50% to +500%
            factor = random.uniform(0.5, 6.0)
        else:
            # Normal mode: mild deterioration/improvement
            factor = random.uniform(0.8, 3.0)
        
        current_pd = round(min(initial_pd * factor, 0.9999), 4)

        maturity_years = random.randint(1, 10)

        # EIR between 1% and 5%
        eir = round(random.uniform(0.01, 0.05), 4)

        lgd = 0.45

        stage = ""  # left blank to be calculated later

        rows.append(
            {
                "Loan_ID": loan_id,
                "Sector": sector,
                "Principal": principal,
                "Initial_PD": initial_pd,
                "Current_PD": current_pd,
                "Maturity_Years": maturity_years,
                "EIR": eir,
                "LGD": lgd,
                "Stage": stage,
            }
        )

    # Stress mode: force 2% of portfolio into default (PD > 50%)
    if stress:
        n_defaults = max(1, int(n * 0.02))
        default_indices = random.sample(range(len(rows)), n_defaults)
        for idx in default_indices:
            rows[idx]["Current_PD"] = round(random.uniform(0.51, 0.99), 4)

    return rows


def save_csv(rows, out_file="ifrs9_portfolio.csv"):
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
    ]
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def main():
    parser = argparse.ArgumentParser(description="Generate IFRS9 synthetic portfolio CSV.")
    parser.add_argument("--n", type=int, default=500, help="number of loans to generate (default 500)")
    parser.add_argument("--out", type=str, default="data/ifrs9_portfolio.csv", help="output CSV filename")
    parser.add_argument("--seed", type=int, default=42, help="random seed (default 42)")
    parser.add_argument("--stress", action="store_true", help="apply credit shocks (higher volatility + 2%% defaults)")
    args = parser.parse_args()

    rows = generate_portfolio(n=args.n, seed=args.seed, stress=args.stress)
    save_csv(rows, out_file=args.out)
    mode = "STRESS" if args.stress else "NORMAL"
    print(f"Wrote {len(rows)} loans to {args.out} [{mode} mode]")


if __name__ == "__main__":
    main()
