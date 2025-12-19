#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# This script aggregates FIO benchmark results stored as JSON files and
# produces a summarized CSV report.
#
# It:
# - Reads all FIO JSON output files from a results directory
# - Aggregates bandwidth, IOPS, and latency metrics across multiple jobs
# - Computes average values per (target, test) combination
# - Writes a sorted CSV summary suitable for comparison and reporting
#
# The script is intended to be used together with an automated FIO test suite
# to compare storage performance across different targets (e.g. SAN vs NAS).
# -----------------------------------------------------------------------------

import json, glob, os, statistics, csv

RESULT_DIR = os.environ.get("RESULT_DIR", "./results")
OUT_CSV = os.environ.get("OUT_CSV", "./fio_summary.csv")

def parse_file(path):
    with open(path, "r") as f:
        data = json.load(f)
        print("Parsing", path)

    # Sum over all jobs (numjobs)
    read_kb = sum(j["read"]["bw"] for j in data["jobs"])
    write_kb = sum(j["write"]["bw"] for j in data["jobs"])
    read_iops = sum(j["read"]["iops"] for j in data["jobs"])
    write_iops = sum(j["write"]["iops"] for j in data["jobs"])

    # Latency (usec) as the average across jobs
    # (a weighted average would be more accurate; here we use the arithmetic mean)
    read_lat = [
        j["read"]["clat_ns"]["mean"] / 1000.0 if j["read"]["clat_ns"]["mean"] else 0
        for j in data["jobs"]
    ]
    write_lat = [
        j["write"]["clat_ns"]["mean"] / 1000.0 if j["write"]["clat_ns"]["mean"] else 0
        for j in data["jobs"]
    ]
    read_lat_u = statistics.fmean([x for x in read_lat if x > 0]) if any(read_lat) else 0
    write_lat_u = statistics.fmean([x for x in write_lat if x > 0]) if any(write_lat) else 0

    return {
        "read_mb_s": read_kb / 1024.0,
        "write_mb_s": write_kb / 1024.0,
        "read_iops": read_iops,
        "write_iops": write_iops,
        "read_lat_us": read_lat_u,
        "write_lat_us": write_lat_u,
    }

# Collect result files
rows = {}
for path in glob.glob(os.path.join(RESULT_DIR, "*.json")):
    base = os.path.basename(path)
    # Format: <target>__<test>__run<nr>__<timestamp>.json
    try:
        target, test, runpart = base.split("__", 3)
    except ValueError as e:
        print(e)
        continue
    key = (target, test)
    rows.setdefault(key, []).append(parse_file(path))

# Compute averages per (target, test)
agg = []
for (target, test), vals in rows.items():
    def mean(k): 
        return statistics.fmean(v[k] for v in vals) if vals else 0.0

    agg.append({
        "target": target,
        "test": test,
        "n_runs": len(vals),
        "read_mb_s_avg": round(mean("read_mb_s"), 1),
        "write_mb_s_avg": round(mean("write_mb_s"), 1),
        "read_iops_avg": round(mean("read_iops"), 1),
        "write_iops_avg": round(mean("write_iops"), 1),
        "read_lat_us_avg": round(mean("read_lat_us"), 1),
        "write_lat_us_avg": round(mean("write_lat_us"), 1),
    })

# Write CSV, sorted by target and test
agg.sort(key=lambda x: (x["target"], x["test"]))
with open(OUT_CSV, "w", newline="") as f:
    w = csv.DictWriter(
        f,
        fieldnames=list(agg[0].keys()) if agg else [
            "target", "test", "n_runs",
            "read_mb_s_avg", "write_mb_s_avg",
            "read_iops_avg", "write_iops_avg",
            "read_lat_us_avg", "write_lat_us_avg",
        ],
    )
    w.writeheader()
    w.writerows(agg)

print(f"Wrote {OUT_CSV} with {len(agg)} aggregated rows.")
