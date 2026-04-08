# Megaline Prepaid Plan Statistical Analysis

Statistical data analysis comparing Megaline's two prepaid plans — **Surf** and **Ultimate** — across 500 customers to determine which plan generates more revenue and whether the observed difference is statistically significant.

**Portfolio write-up:** [Megaline Prepaid Plan SDA — Which Plan Wins?](https://viet-in-tech.github.io/megaline-sda-analysis.html)

**TripleTen Data Science Program · Sprint 5 — Statistical Data Analysis**

---

## What's in This Repo

| File | Description |
|------|-------------|
| `megaline_sda.ipynb` | Full statistical analysis notebook |

## Plans Compared

| Plan | Monthly Fee | Included Minutes | Included Messages | Included Data |
|------|------------|-----------------|-------------------|--------------|
| Surf | Lower | 500 min | 50 SMS | 15 GB |
| Ultimate | Higher | 3,000 min | 1,000 SMS | 30 GB |

Overage charges apply when a customer exceeds their included allowances.

## Overview

The business question: which plan actually brings in more revenue? This project aggregates monthly usage data per user, calculates revenue (base fee + overages), and applies hypothesis testing to validate whether the revenue difference between plans is statistically significant.

## Methodology

1. **Data cleaning** — handle missing values, fix data types, remove duplicates
2. **Feature engineering** — compute monthly revenue per user (base + overage minutes, messages, data)
3. **EDA** — visualize usage distributions and revenue by plan
4. **Hypothesis test** — two-sample t-test (H₀: mean revenue is equal across plans; α = 0.05)

## Key Finding

The lower-priced **Surf plan generates higher average revenue** than the premium Ultimate plan — driven by consistent overage charges. A two-sample t-test confirms the difference is statistically significant (p < 0.05).

## Tech Stack

- Python 3 · pandas · NumPy
- matplotlib · seaborn
- scipy.stats (ttest_ind)
- Jupyter Notebook

## Project Status

✅ Approved — TripleTen Data Science Program, Sprint 5
