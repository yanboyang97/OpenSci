# Estimator Comparison Protocol

## Synthetic experiment protocol

The Estimator Comparison protocol (record identifier `synthetic-v1`) applies to `demo` with public data; the task binds this file's SHA-256. Compare sample-mean and sample-median mean-squared error for the uncontaminated normal location 0. The contaminated mixture mean is 0.8, but the estimand remains 0; this cannot establish that the median better estimates the mixture mean. The proposed hypothesis is higher mean efficiency under clean normal data and higher median robustness under the specified contamination, not a verified real-world finding.

- Clean observations are N(0,1).
- Contaminated observations independently receive an added 8 with probability 0.1.
- Within a trial, both estimators use the same sample; scenarios use distinct samples.
- Defaults are seed=42, samples=100 and trials=100; approved parameters control the actual run.
- Python random.Random generates clean then contaminated scenarios in fixed continuous order; exact Python version is fingerprinted.
- The statistical unit is the trial, with trials rows per scenario. The dataset definition digest is a generator-definition hash, not a raw-data-file hash.

Each row records mean_error_sq and median_error_sq relative to 0. metrics.json stores average squared error for each estimator/scenario, four metrics total. Validation checks row counts, unique trial IDs, finite nonnegative metrics and CSV/JSON recomputation consistency. Software acceptance does not require either estimator to win.

Current code computes no confidence intervals, p-values or significance claims. A formal comparison should prespecify paired losses d_i = mean_error_sq_i - median_error_sq_i by scenario, report their mean and Monte Carlo standard error with a chosen interval method, and assess contamination/sample-size/offset sensitivity. Review, commit and approve the implementation, repetitions and stopping rule separately. Do not cherry-pick seeds, portray selected reruns as prespecified, or extrapolate to real medical/engineering/business data.

The adapter uses no GPU and declares one CPU thread; samples×trials is bounded by 10,000,000, with two actual scenarios. The executor enforces timeout; compute_budget is a human record, not a billing cap. Protocol/generator/parameter/dependency/node changes require a new run and approval; preserve old failures. Before real research, add data permission/version, split/leakage checks, preprocessing, statistical units, primary/secondary metrics, baselines/ablations, sample-size rationale, multiplicity, missing/outlier handling, uncertainty, hardware/drivers, compute fairness, stopping and protocol deviations.
