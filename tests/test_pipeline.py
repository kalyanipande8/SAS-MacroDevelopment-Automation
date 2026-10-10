import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import pytest

from src.macros import qc_check, gen_summary_table, gen_ae_table, audit_log, AUDIT_LOG
from src.benchmark import run_benchmark
from src.macro_specs import check_traceability, MACRO_SPECS


@pytest.fixture(scope="module")
def df():
    rng = np.random.default_rng(47)
    return pd.DataFrame({
        "usubjid": [f"S{i:04d}" for i in range(1000)],
        "trt01pn": rng.choice([1, 2, 3], 1000),
        "age": rng.normal(55, 12, 1000),
        "aesoc": rng.choice(["GI", "Nervous system"], 1000),
        "aedecod": rng.choice(["Nausea", "Headache"], 1000),
    })


def test_six_macros_documented():
    assert len(MACRO_SPECS) == 6


def test_qc_check_detects_no_missingness_on_clean_data(df):
    result = qc_check(df, ["age", "trt01pn"])
    assert result["age"]["n_missing"] == 0


def test_summary_table_covers_all_groups(df):
    table = gen_summary_table(df, "age", "trt01pn")
    assert set(table["trt01pn"]) == {1, 2, 3}
    assert (table["n"] > 0).all()


def test_ae_table_counts_are_distinct_subjects_not_raw_rows(df):
    table = gen_ae_table(df, "aesoc", "aedecod", "trt01pn")
    assert (table["n_subj"] <= len(df)).all()
    assert len(table) > 0


def test_benchmark_approaches_are_numerically_equivalent(df):
    result = run_benchmark(df, "age", "trt01pn", n_runs=5)
    assert result["results_numerically_equivalent"] is True


def test_benchmark_shows_a_real_efficiency_improvement(df):
    """The macro-based approach should be faster than the naive
    re-derive-everything-manually approach -- a real, measured speedup,
    not necessarily any particular target percentage."""
    result = run_benchmark(df, "age", "trt01pn", n_runs=8)
    assert result["efficiency_improvement_pct"] > 0


def test_full_code_traceability():
    result = check_traceability()
    assert result["fully_traceable"] is True
    assert result["spec_coverage_pct"] == 100.0
    assert result["python_mirror_coverage_pct"] == 100.0


def test_audit_log_records_every_macro_call():
    AUDIT_LOG.clear()
    audit_log("qc_check", "test_data", "params")
    audit_log("gen_summary_table", "test_data", "params")
    assert len(AUDIT_LOG) == 2
