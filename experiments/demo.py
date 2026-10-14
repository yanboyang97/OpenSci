#!/usr/bin/env python3
"""Synthetic toy study only; stdlib, no network, no confidential data."""
import argparse
import csv
import json
import random
import statistics
from pathlib import Path

def simulate(seed: int, samples: int, trials: int = 100) -> tuple[list[dict], dict]:
    rng = random.Random(seed)
    rows = []
    for scenario, fraction in (("clean", 0.0), ("contaminated", 0.1)):
        for trial in range(trials):
            xs = [rng.gauss(0, 1) + (8.0 if rng.random() < fraction else 0.0)
                  for _ in range(samples)]
            rows.append({"scenario": scenario, "trial": trial,
                         "mean_error_sq": statistics.mean(xs) ** 2,
                         "median_error_sq": statistics.median(xs) ** 2})
    metrics = {}
    for scenario in ("clean", "contaminated"):
        subset = [r for r in rows if r["scenario"] == scenario]
        for estimator in ("mean", "median"):
            metrics[f"{scenario}_{estimator}_mse"] = statistics.mean(
                r[f"{estimator}_error_sq"] for r in subset)
    return rows, metrics

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--outdir", required=True, type=Path)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--samples", type=int, default=100)
    p.add_argument("--trials", type=int, default=100)
    a = p.parse_args()
    if not 10 <= a.samples <= 100000 or not 2 <= a.trials <= 1000 or a.samples*a.trials > 10000000:
        p.error("sample/trial budget exceeded")
    a.outdir.mkdir(parents=True, exist_ok=True)
    rows, metrics = simulate(a.seed, a.samples, a.trials)
    with (a.outdir / "trials.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    (a.outdir / "metrics.json").write_text(json.dumps(metrics, indent=2)+"\n", encoding="utf-8")
    print("SYNTHETIC DEMO ONLY — no real-data claim.")
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    main()
