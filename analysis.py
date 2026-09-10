from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm


REQUIRED_COLUMNS = {
    "user id",
    "test group",
    "converted",
    "total ads",
    "most ads day",
    "most ads hour",
}

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


@dataclass(frozen=True)
class ExperimentResult:
    treatment: str
    control: str
    treatment_users: int
    control_users: int
    treatment_conversions: int
    control_conversions: int
    treatment_rate: float
    control_rate: float
    absolute_lift: float
    relative_lift: float
    z_score: float
    p_value: float
    ci_low: float
    ci_high: float
    significant: bool

    def as_dict(self) -> dict:
        return asdict(self)


def load_data(path_or_buffer) -> pd.DataFrame:
    df = pd.read_csv(path_or_buffer)
    df = df.drop(columns=["Unnamed: 0"], errors="ignore")
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
    if df["user id"].duplicated().any():
        raise ValueError("Each user must appear only once in this experiment dataset.")
    df = df.copy()
    df["converted"] = df["converted"].astype(bool)
    df["most ads hour"] = pd.to_numeric(df["most ads hour"], errors="raise").astype(int)
    df["total ads"] = pd.to_numeric(df["total ads"], errors="raise")
    return df


def two_proportion_test(
    df: pd.DataFrame,
    treatment: str = "ad",
    control: str = "psa",
    alpha: float = 0.05,
) -> ExperimentResult:
    t = df[df["test group"] == treatment]["converted"]
    c = df[df["test group"] == control]["converted"]
    if t.empty or c.empty:
        raise ValueError("Both treatment and control groups need at least one record.")

    n_t, n_c = len(t), len(c)
    x_t, x_c = int(t.sum()), int(c.sum())
    p_t, p_c = x_t / n_t, x_c / n_c
    pooled = (x_t + x_c) / (n_t + n_c)
    pooled_se = sqrt(max(pooled * (1 - pooled) * (1 / n_t + 1 / n_c), 0))
    z = (p_t - p_c) / pooled_se if pooled_se else 0.0
    p_value = float(2 * norm.sf(abs(z)))

    unpooled_se = sqrt(p_t * (1 - p_t) / n_t + p_c * (1 - p_c) / n_c)
    critical = float(norm.ppf(1 - alpha / 2))
    difference = p_t - p_c
    relative = difference / p_c if p_c else np.nan
    return ExperimentResult(
        treatment=treatment,
        control=control,
        treatment_users=n_t,
        control_users=n_c,
        treatment_conversions=x_t,
        control_conversions=x_c,
        treatment_rate=p_t,
        control_rate=p_c,
        absolute_lift=difference,
        relative_lift=relative,
        z_score=z,
        p_value=p_value,
        ci_low=difference - critical * unpooled_se,
        ci_high=difference + critical * unpooled_se,
        significant=p_value < alpha,
    )


def segment_performance(df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    if dimension not in {"most ads day", "most ads hour", "exposure band"}:
        raise ValueError("Unsupported segment dimension.")
    working = df.copy()
    group_col = dimension
    if dimension == "exposure band":
        bins = [-np.inf, 5, 20, 50, 100, np.inf]
        labels = ["1–5", "6–20", "21–50", "51–100", "100+"]
        working[group_col] = pd.cut(working["total ads"], bins=bins, labels=labels)

    summary = (
        working.groupby([group_col, "test group"], observed=True)["converted"]
        .agg(users="size", conversions="sum", conversion_rate="mean")
        .reset_index()
    )
    pivot = summary.pivot(index=group_col, columns="test group", values="conversion_rate")
    if {"ad", "psa"}.issubset(pivot.columns):
        lift = (pivot["ad"] - pivot["psa"]).rename("absolute_lift")
        summary = summary.merge(lift, left_on=group_col, right_index=True, how="left")
    else:
        summary["absolute_lift"] = np.nan
    return summary


def minimum_sample_size(baseline: float, relative_mde: float, alpha: float = 0.05, power: float = 0.8) -> int:
    if not 0 < baseline < 1:
        raise ValueError("Baseline conversion must be between 0 and 1.")
    if relative_mde <= 0:
        raise ValueError("Relative MDE must be greater than zero.")
    target = min(baseline * (1 + relative_mde), 0.999999)
    delta = target - baseline
    p_bar = (baseline + target) / 2
    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(power)
    numerator = (
        z_alpha * sqrt(2 * p_bar * (1 - p_bar))
        + z_beta * sqrt(baseline * (1 - baseline) + target * (1 - target))
    ) ** 2
    return int(np.ceil(numerator / delta**2))


def build_report(result: ExperimentResult, hypothesis: str, decision_rule: str) -> str:
    direction = "increased" if result.absolute_lift >= 0 else "decreased"
    decision = "supports rollout consideration" if result.significant and result.absolute_lift > 0 else "does not yet support rollout"
    return f"""# Growth Experiment Review

## Hypothesis
{hypothesis}

## Result
- Treatment: **{result.treatment}** ({result.treatment_users:,} users)
- Control: **{result.control}** ({result.control_users:,} users)
- Treatment conversion: **{result.treatment_rate:.2%}**
- Control conversion: **{result.control_rate:.2%}**
- Absolute lift: **{result.absolute_lift:+.2%}**
- Relative lift: **{result.relative_lift:+.2%}**
- 95% confidence interval: **[{result.ci_low:+.2%}, {result.ci_high:+.2%}]**
- Two-sided p-value: **{result.p_value:.4g}**

## Decision
Conversion {direction}; under the stated decision rule, this experiment **{decision}**.

Decision rule: {decision_rule}

## Recommended follow-up
1. Check whether lift is consistent across exposure bands, day of week, and hour of day.
2. Validate guardrail metrics before scaling; conversion alone cannot identify experience or cost trade-offs.
3. Pre-register the primary metric and sample size for the next experiment.
4. Treat segment findings as exploratory unless they were specified before analysis.

## Data note
This is a portfolio prototype based on a public Kaggle marketing A/B testing dataset. It is not a production experiment conducted for RED or another employer.
"""


def default_data_path() -> Path:
    return Path(__file__).resolve().parent / "data" / "marketing_AB.csv"


def demo_data(seed: int = 27, users: int = 12000) -> pd.DataFrame:
    """Create a deterministic synthetic dataset for the public demo."""
    rng = np.random.default_rng(seed)
    group = rng.choice(["ad", "psa"], size=users, p=[0.8, 0.2])
    converted = rng.random(users) < np.where(group == "ad", 0.027, 0.018)
    return pd.DataFrame(
        {
            "user id": np.arange(1, users + 1),
            "test group": group,
            "converted": converted,
            "total ads": np.maximum(1, rng.negative_binomial(3, 0.15, size=users)),
            "most ads day": rng.choice(DAY_ORDER, size=users),
            "most ads hour": rng.integers(0, 24, size=users),
        }
    )
