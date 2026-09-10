# Growth Experiment Builder

An AI-assisted portfolio prototype that turns a public user-level A/B testing dataset into a decision workflow: validate data, estimate conversion lift, test statistical significance, explore segments, calculate sample size, save experiment history, and export a reusable review.

> This is a portfolio project built from a public Kaggle dataset. It is not a production experiment conducted for RED or another employer.

## Why I built it

Growth work is more than reading dashboards. A useful workflow should connect an ambiguous question to a falsifiable hypothesis, a statistical decision, and a well-scoped next experiment. This prototype demonstrates that loop in one small product.

## Features

- CSV schema and uniqueness validation
- Treatment/control conversion comparison
- Two-proportion z-test, confidence interval, absolute and relative lift
- Exploratory diagnostics by exposure band, weekday, and hour
- Sample-size planning using baseline conversion, MDE, alpha, and power
- Experiment cards with primary metric, guardrails, and stop rule
- Local SQLite experiment log
- One-click Markdown review export
- Works locally without an API key

## Dataset

Source: [Marketing A/B Testing by Favio Vaz on Kaggle](https://www.kaggle.com/datasets/faviovaz/marketing-ab-testing)

The portfolio analysis uses 588,101 unique user records with experiment group, conversion outcome, total ad exposure, highest-exposure weekday, and highest-exposure hour. The original index column is removed during loading. No rows are missing required values.

The original CSV is intentionally not redistributed in this public repository. Download `marketing_AB.csv` from the linked Kaggle page and either upload it in the app or place it under `data/`. Without it, the interface automatically loads a clearly labeled deterministic synthetic dataset so the product can still be explored.

The `ad` group is treated as treatment and `psa` as control. The dataset documents exposure and conversion rather than a complete product lifecycle funnel, so this project does **not** invent activation, retention, or sharing events.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Run tests

```bash
pip install pytest
pytest -q
```

## Analytical choices

- The primary comparison uses a two-sided two-proportion z-test.
- Confidence intervals use an unpooled standard error; the hypothesis test uses a pooled standard error under the null.
- Segment analysis is explicitly labeled exploratory to avoid post-hoc significance fishing.
- Rollout language requires positive lift and statistical significance, but the interface also warns that business and guardrail metrics must be checked.
- Sample size uses the normal approximation for two independent proportions.

## Project structure

```text
growth_experiment_builder/
├── app.py                  # Streamlit product interface
├── analysis.py             # Reusable statistics and reporting logic
├── storage.py              # SQLite experiment history
├── data/                   # Optional local Kaggle CSV (not redistributed)
├── tests/test_analysis.py  # Core behavior and schema checks
├── requirements.txt
└── README.md
```

## AI-assisted development disclosure

I defined the product scope, experiment workflow, analytical decisions, and validation criteria. Codex assisted with implementation, debugging, documentation, and test scaffolding. I reviewed the statistical logic and can explain the data schema, z-test, confidence interval, MDE, segmentation caveats, and product trade-offs.

## Possible next iterations

1. Connect an LLM endpoint to convert structured results into editable experiment reviews, with deterministic fallback.
2. Add multiple-testing correction when comparing many pre-registered segments.
3. Add cost-per-conversion and experience guardrails when an appropriate dataset is available.
4. Deploy a public demo after replacing local SQLite with a hosted store.

## Resume-ready description

**AI Growth Experiment Builder | Independent project**

- Built a Streamlit experimentation prototype with Codex using 588K public user-level A/B test records; implemented automated schema checks, treatment/control conversion comparison, lift estimation, 95% confidence intervals, and significance testing.
- Developed exploratory segmentation by exposure, weekday, and hour, plus an MDE/power-based sample-size planner; converted analytical outputs into reusable experiment cards and Markdown reviews.
- Added SQLite experiment history and documented data limitations, guardrails, and post-hoc analysis risks, completing a small end-to-end workflow from problem definition to decision and next-test design.

## License

Code is released under the MIT License. Dataset usage remains subject to its source terms on Kaggle.
