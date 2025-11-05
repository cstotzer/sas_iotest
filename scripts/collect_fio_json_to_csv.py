#!/usr/bin/env python3
import json, glob, os, statistics, csv

RESULT_DIR = os.environ.get("RESULT_DIR", "./results")
OUT_CSV = os.environ.get("OUT_CSV", "./fio_summary.csv")

def parse_file(path):
    with open(path, "r") as f:
        data = json.load(f)
    # Summiere über alle Jobs (numjobs)
    read_kb = sum(j["read"]["bw"] for j in data["jobs"])
    write_kb = sum(j["write"]["bw"] for j in data["jobs"])
    read_iops = sum(j["read"]["iops"] for j in data["jobs"])
    write_iops = sum(j["write"]["iops"] for j in data["jobs"])
    # Latenz (usec) als durchschnitt über jobs (gewichtet wäre noch besser; hier arithm. Mittel)
    read_lat = [j["read"]["clat_ns"]["mean"]/1000.0 if j["read"]["clat_ns"]["mean"] else 0 for j in data["jobs"]]
    write_lat = [j["write"]["clat_ns"]["mean"]/1000.0 if j["write"]["clat_ns"]["mean"] else 0 for j in data["jobs"]]
    read_lat_u = statistics.fmean([x for x in read_lat if x>0]) if any(read_lat) else 0
    write_lat_u = statistics.fmean([x for x in write_lat if x>0]) if any(write_lat) else 0
    return {
        "read_mb_s": read_kb/1024.0,
        "write_mb_s": write_kb/1024.0,
        "read_iops": read_iops,
        "write_iops": write_iops,
        "read_lat_us": read_lat_u,
        "write_lat_us": write_lat_u
    }

# Dateien einsammeln
rows = {}
for path in glob.glob(os.path.join(RESULT_DIR, "*.json")):
    base = os.path.basename(path)
    # Format: <target>__<test>__run<nr>__<timestamp>.json
    try:
        target, test, runpart, _ = base.split("__", 3)
    except ValueError:
        continue
    key = (target, test)
    rows.setdefault(key, []).append(parse_file(path))

# Mittelwerte pro (target,test)
agg = []
for (target, test), vals in rows.items():
    def mean(k): return statistics.fmean(v[k] for v in vals) if vals else 0.0
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

# CSV schreiben, sortiert
agg.sort(key=lambda x:(x["target"], x["test"]))
with open(OUT_CSV, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(agg[0].keys()) if agg else [
        "target","test","n_runs","read_mb_s_avg","write_mb_s_avg",
        "read_iops_avg","write_iops_avg","read_lat_us_avg","write_lat_us_avg"
    ])
    w.writeheader()
    w.writerows(agg)

print(f"Wrote {OUT_CSV} with {len(agg)} aggregated rows.")