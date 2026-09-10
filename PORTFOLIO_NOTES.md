# Portfolio talking points

## 30-second introduction

I noticed that many growth dashboards stop at metric display, so I built a small experimentation workflow around public user-level A/B test data. With Codex assisting implementation, I turned 588,101 records into a Streamlit prototype that validates data, compares conversion, tests significance, diagnoses segments, plans sample size, saves experiment history in SQLite, and exports the next experiment brief. I deliberately avoided fabricating retention fields that the source data does not contain.

## What the result means

- Treatment conversion rate: 2.55%
- Control conversion rate: 1.79%
- Absolute lift: +0.77 percentage points
- Relative lift: +43.09%
- Two-sided p-value: 1.71e-13
- 95% confidence interval for absolute lift: +0.60 to +0.94 percentage points

The treatment produced a statistically reliable positive difference in this dataset. A production rollout would still need cost, complaint, negative-feedback, and experience guardrails.

## What I personally decided

- Chose a user-level experiment dataset instead of unrelated sales data.
- Defined the primary metric, treatment/control interpretation, and rollout rule.
- Required schema and user-uniqueness validation.
- Kept segment analysis exploratory to avoid post-hoc significance fishing.
- Added sample-size planning and an experiment log so the project forms a workflow rather than a one-off chart.
- Documented AI assistance and data limitations rather than presenting the project as a real employer experiment.

## Likely interview questions

### Why use a two-proportion z-test?

The outcome is binary and the groups are independent with large samples, so the normal approximation is appropriate for testing the difference between two conversion proportions.

### Why are the groups so imbalanced?

The source dataset contains far more treatment users than PSA users. The test incorporates the actual group sizes, but the imbalance should be discussed as a design limitation rather than hidden.

### Why not call this a full growth funnel?

The data only supports exposure and conversion. Activation, retention, recall, and sharing are not present, so adding them would create fictional evidence. The architecture can accept a richer schema later.

### Where is the AI-native part?

I used Codex across scoping, implementation, debugging, tests, and documentation, while retaining ownership of the business question and analytical decisions. The resulting product is a functioning tool with reproducible code, not a prompt-only output.

### What would you improve next?

Add a genuine multi-step event dataset, pre-registered segment comparisons with multiple-testing correction, cost and experience guardrails, and an optional LLM layer that drafts—but does not decide—the experiment review.
