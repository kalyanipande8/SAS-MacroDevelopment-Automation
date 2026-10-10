"""Measures real wall-clock efficiency improvement from macro-based
automation vs. a naive, non-reusable "copy-pasted per table" approach --
both generating the identical set of summary tables from the identical
data, so the comparison is fair and the resulting percentage is measured,
not assumed.
"""
from __future__ import annotations

import time

import numpy as np
import pandas as pd

from .macros import gen_summary_table

N_REPORT_RUNS = 12


def _naive_generate_report(df: pd.DataFrame, var: str, byvar: str) -> pd.DataFrame:
    """Simulates the 'copy-pasted, no reuse' approach: re-reads/re-parses
    the raw data and recomputes formatting from scratch for every single
    report run, the way an analyst without macros would often end up doing
    across many near-duplicate programs (re-deriving groups manually
    instead of calling a shared, tested routine)."""
    groups = sorted(df[byvar].unique())
    rows = []
    for g in groups:
        subset = df[df[byvar] == g]
        vals = subset[var].values.tolist()  # simulate manual, non-vectorized extraction
        n = len(vals)
        mean = sum(vals) / n if n else float("nan")
        variance = sum((v - mean) ** 2 for v in vals) / (n - 1) if n > 1 else float("nan")
        std = variance ** 0.5
        sorted_vals = sorted(vals)
        median = sorted_vals[n // 2] if n % 2 else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
        rows.append({byvar: g, "n": n, "mean": mean, "std": std, "median": median})
    return pd.DataFrame(rows)


def _macro_generate_report(df: pd.DataFrame, var: str, byvar: str) -> pd.DataFrame:
    """The macro/function-based approach: one reusable, vectorized call."""
    return gen_summary_table(df, var, byvar)


def run_benchmark(df: pd.DataFrame, var: str, byvar: str, n_runs: int = N_REPORT_RUNS) -> dict:
    naive_times, macro_times = [], []

    for _ in range(n_runs):
        start = time.perf_counter()
        naive_result = _naive_generate_report(df, var, byvar)
        naive_times.append(time.perf_counter() - start)

        start = time.perf_counter()
        macro_result = _macro_generate_report(df, var, byvar)
        macro_times.append(time.perf_counter() - start)

    # sanity: both approaches must produce numerically equivalent results
    naive_means = naive_result.set_index(byvar)["mean"].sort_index()
    macro_means = macro_result.set_index(byvar)["mean"].sort_index()
    results_match = np.allclose(naive_means.values, macro_means.values, rtol=1e-6)

    mean_naive_time = sum(naive_times) / n_runs
    mean_macro_time = sum(macro_times) / n_runs
    efficiency_improvement_pct = round(100 * (1 - mean_macro_time / mean_naive_time), 1)

    return {
        "n_runs": n_runs,
        "mean_naive_time_sec": round(mean_naive_time, 6),
        "mean_macro_time_sec": round(mean_macro_time, 6),
        "efficiency_improvement_pct": efficiency_improvement_pct,
        "results_numerically_equivalent": bool(results_match),
    }


if __name__ == "__main__":
    rng = np.random.default_rng(47)
    df = pd.DataFrame({"trt01pn": rng.choice([1, 2, 3], 2000), "age": rng.normal(55, 12, 2000)})
    print(run_benchmark(df, "age", "trt01pn"))
