# IFRS 9 Expected Credit Loss (ECL) Modeling Engine

## Overview
This repository contains a full-stack Python implementation of an IFRS 9 compliant impairment engine. It automates the transition between credit stages and calculates expected losses under multiple macroeconomic scenarios.

## Key Features
* **Three-Stage Transition Model:** Automated classification based on SICR (Significant Increase in Credit Risk) logic.
* **Forward-Looking Overlays:** Probability-weighted ECL across Base, Optimistic, and Downturn scenarios.
* **Lifetime Projection:** Calculation of cumulative PD and discounted cash flow (DCF) loss estimations for Stage 2 & 3 assets.
* **Stress Testing:** Integrated pipeline to simulate systematic credit degradation and portfolio migration.

## Technical Stack
* **Language:** Python 3.x
* **Libraries:** Pandas, NumPy, Plotly (Visualization), Argparse (CLI)
* **Standards:** IFRS 9, Basel III alignment

## Project Structure
```
IFRS9-ECL-Engine/
├── data/                       # Data files (inputs & outputs)
│   ├── ifrs9_portfolio.csv     # Generated loan portfolio
│   └── ifrs9_results.csv       # ECL results with Stage assignments
├── src/                        # Source code modules
│   ├── __init__.py             # Package initializer
│   ├── ifrs9_data.py           # Portfolio generator with credit volatility
│   ├── ecl_engine.py           # Stage assignment & discounted ECL computation
│   └── ifrs9_viz.py            # Interactive Plotly dashboard & charts
├── .gitignore                  # Git ignore rules
├── LICENSE                     # MIT License
├── main.py                     # CLI orchestration script
├── README.md                   # This file
└── requirements.txt            # Python dependencies
```

## Installation & Usage

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run a standard calculation
```bash
python main.py
```

### 3. Execute a regulatory stress test
```bash
python main.py --stress
```

## Model Methodology

### 1. SICR Threshold
Assets transition from Stage 1 to Stage 2 if the ratio `Current_PD / Initial_PD` exceeds **3.0**. Stage 3 is triggered at a `PD > 50%`.

| Stage | Condition | ECL Horizon |
|-------|-----------|-------------|
| 1 | No SICR | 12-month |
| 2 | PD ratio > 3.0 | Lifetime |
| 3 | PD > 50% (Default) | Lifetime |

### 2. ECL Formula
The engine computes the probability-weighted average:

$$ECL = \sum_{i} w_i \times (PD_i \times LGD \times EAD \times DF)$$

Where $DF$ is the Discount Factor: $\frac{1}{(1 + EIR)^t}$

### 3. Scenario Weights
| Scenario | PD Multiplier | Weight |
|----------|---------------|--------|
| Optimistic | 0.80 | 30% |
| Base | 1.00 | 40% |
| Downturn | 1.50 | 30% |

## Results & Analytics

The model outputs a full compliance report (`ifrs9_results.csv`) and generates visual insights into:

* **Portfolio migration** (Stage 1 → Stage 2 → Stage 3)
* **Provisions coverage ratio** by industrial sector
* **Sensitivity analysis** of the "Cliff Effect" during stress scenarios

### Output Files
| File | Description |
|------|-------------|
| `data/ifrs9_portfolio.csv` | Generated loan portfolio |
| `data/ifrs9_results.csv` | ECL results with Stage assignments |
| `ifrs9_dashboard.html` | Full interactive Plotly dashboard |
| `chart_sunburst.html` | Sector/Stage breakdown visualization |
| `chart_ecl_comparison.html` | Base vs Downturn comparison |
| `chart_kpi.html` | Key performance indicators |

## Sample Output

### Normal Mode
```
Stage 1: 499 loans
Stage 2: 1 loans
Stage 3: 0 loans
Total ECL: 5,305,550
```

### Stress Mode
```
Stage 1: 226 loans
Stage 2: 264 loans
Stage 3: 10 loans
Total ECL: 31,167,572
```

## License
MIT License

## Author
Carlo - Risk Analytics

---
*Built for regulatory compliance and credit risk management.*
