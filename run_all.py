"""End-to-end: run the 6-macro Python mirror against simulated data, run
the real efficiency benchmark, and verify code traceability."""
import json
import os

import numpy as np
import pandas as pd

from src.macros import qc_check, gen_summary_table, gen_ae_table, audit_log, AUDIT_LOG
from src.benchmark import run_benchmark
from src.macro_specs import check_traceability, MACRO_SPECS

os.makedirs("data", exist_ok=True)
os.makedirs("results", exist_ok=True)

print("=== Simulating analysis dataset ===")
rng = np.random.default_rng(47)
df = pd.DataFrame({
    "usubjid": [f"S{i:04d}" for i in range(2000)],
    "trt01pn": rng.choice([1, 2, 3], 2000),
    "age": rng.normal(55, 12, 2000),
    "aesoc": rng.choice(["GI", "Nervous system", "General"], 2000),
    "aedecod": rng.choice(["Nausea", "Headache", "Fatigue"], 2000),
})
df.to_csv("data/analysis_data.csv", index=False)

print("\n=== Exercising the 6 macros (Python mirror) ===")
qc_result = qc_check(df, ["age", "trt01pn"])
audit_log("qc_check", "analysis_data", "keyvars=age,trt01pn")
print("QC check:", qc_result)

summary_table = gen_summary_table(df, "age", "trt01pn")
audit_log("gen_summary_table", "analysis_data", "var=age,byvar=trt01pn")
print("Summary table:\n", summary_table)

ae_table = gen_ae_table(df, "aesoc", "aedecod", "trt01pn")
audit_log("gen_ae_table", "analysis_data", "socvar=aesoc,ptvar=aedecod,byvar=trt01pn")
print(f"AE table: {len(ae_table)} rows")

print(f"\nAudit log entries: {len(AUDIT_LOG)}")

print("\n=== Real efficiency benchmark (macro-based vs. naive per-table code) ===")
benchmark = run_benchmark(df, "age", "trt01pn", n_runs=12)
print(benchmark)

print("\n=== Code traceability check ===")
traceability = check_traceability()
print(traceability)

summary = {
    "n_macros": len(MACRO_SPECS),
    "efficiency_improvement_pct": benchmark["efficiency_improvement_pct"],
    "results_numerically_equivalent": benchmark["results_numerically_equivalent"],
    "traceability_spec_coverage_pct": traceability["spec_coverage_pct"],
    "traceability_mirror_coverage_pct": traceability["python_mirror_coverage_pct"],
    "fully_traceable": traceability["fully_traceable"],
}
with open("results/summary.json", "w") as f:
    json.dump(summary, f, indent=2)
pd.DataFrame(AUDIT_LOG).to_csv("results/macro_audit_log.csv", index=False)

print("\n=== Summary ===")
print(json.dumps(summary, indent=2))
