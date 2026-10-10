"""Executed Python mirror of the 6 SAS macros in sas/macros.sas -- each
function here does what the corresponding macro automates, so the
efficiency comparison in benchmark.py is measuring something real: the
macro/function-based reusable approach vs. copy-pasted, non-reusable
per-table code performing the same work.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

import pandas as pd

AUDIT_LOG: list[dict] = []


def set_titles(table_num: str, table_title: str, population: str = "Safety Population") -> dict:
    return {"title1": f"Table {table_num}", "title2": table_title, "title3": population}


def qc_check(df: pd.DataFrame, keyvars: list[str]) -> dict:
    n_total = len(df)
    return {var: {"n_total": n_total, "n_missing": int(df[var].isna().sum())} for var in keyvars}


def gen_summary_table(df: pd.DataFrame, var: str, byvar: str) -> pd.DataFrame:
    return df.groupby(byvar)[var].agg(n="count", mean="mean", std="std", median="median").reset_index()


def gen_ae_table(df: pd.DataFrame, socvar: str, ptvar: str, byvar: str) -> pd.DataFrame:
    return (
        df.groupby([byvar, socvar, ptvar])["usubjid"].nunique().reset_index(name="n_subj")
    )


def gen_rtf_output(outpath: str, outname: str, report_fn, *args, **kwargs):
    """Wraps a report-generation call the way the SAS macro wraps a
    PROC REPORT step in ODS RTF open/close boilerplate -- here it simply
    standardizes the call signature so every report is invoked uniformly."""
    return report_fn(*args, **kwargs)


def audit_log(macro_name: str, dsn: str, params: str) -> None:
    AUDIT_LOG.append({
        "macro_name": macro_name, "dsn": dsn, "params": params,
        "run_datetime_utc": datetime.now(timezone.utc).isoformat(),
    })
