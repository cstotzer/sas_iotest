#!/usr/bin/env bash
set -euo pipefail

# Lade Konfiguration
if [[ -f ".env" ]]; then
  # shellcheck disable=SC1091
  source ".env"
else
  echo "Bitte .env aus env.sample erstellen."
  exit 1
fi

mkdir -p "${RESULT_DIR}"

declare -A TARGETS=()
[[ -n "${SAN_PROJECT_DIR:-}" ]] && TARGETS[san_project]="$SAN_PROJECT_DIR"
[[ -n "${NAS_PROJECT_DIR:-}" ]] && TARGETS[nas_project]="$NAS_PROJECT_DIR"
# SASWORK optional
if [[ -n "${SASWORK_DIR:-}" ]]; then
  TARGETS[saswork]="$SASWORK_DIR"
fi

TESTS=("seq_read" "seq_write" "rand_read" "rand_write" "mixed_70_30")

# Optional: CPU-Governor setzen
maybe_set_governor() {
  if [[ "${SET_PERFORMANCE_GOVERNOR}" == "true" ]] && [[ -w /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]]; then
    echo "Setze CPU-Governor auf performance"
    for g in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do echo performance | sudo tee "$g" >/dev/null; done
  fi
}

# Optional: Caches droppen
drop_caches() {
  if [[ "${DROP_CACHES}" == "true" ]] && [[ -w /proc/sys/vm/drop_caches ]]; then
    echo "Dropping caches..."
    sudo sh -c "sync; echo 3 > /proc/sys/vm/drop_caches"
  fi
}

# Vorbedingungen prüfen
command -v fio >/dev/null || { echo "fio nicht gefunden"; exit 2; }

maybe_set_governor

# Läufe
for target in "${!TARGETS[@]}"; do
  dir="${TARGETS[$target]}"
  [[ -d "$dir" ]] || { echo "Zielverzeichnis fehlt: $dir"; exit 3; }

  echo ">>> Ziel: $target -> $dir"
  for test in "${TESTS[@]}"; do
    echo "  -> Test: $test"
    for run in $(seq 1 "${RUNS}"); do
      ts=$(date +"%Y%m%d_%H%M%S")
      out="${RESULT_DIR}/${target}__${test}__run${run}__${ts}.json"
      echo "     Run ${run}/${RUNS} -> ${out}"

      drop_caches

      fio fio/global.fio \
        fio/${test}.fio \
        --filename="${dir}/fio_${test}.dat" \
        --directory="${dir}" \
        --size="${SIZE_GB}G" \
        --runtime="${RUNTIME}" \
        --ramp_time="${RAMP_TIME}" \
        --numjobs="${NUMJOBS}" \
        --iodepth="${IODEPTH}" \
        --output="${out}" \
        --output-format=json
      # Testfile danach nicht löschen, damit verschiedene rw-Pattern identische Datenblöcke nutzen können.
    done
  done
done

echo
echo "Alle Läufe abgeschlossen. Rohdaten liegen unter: ${RESULT_DIR}"
echo "Optional: ./scripts/quick_summary.sh  ODER  python3 ./scripts/collect_fio_json_to_csv.py"
