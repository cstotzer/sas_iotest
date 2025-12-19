#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# This script runs a configurable FIO benchmark test suite against multiple
# target directories (e.g. different storage backends).
#
# It:
# - Loads configuration from a .env file
# - Optionally sets the CPU governor to "performance"
# - Optionally drops OS caches before each run
# - Executes multiple FIO test profiles and repeated runs per target
# - Writes all results as JSON files to a central results directory
#
# The script is intended for repeatable storage performance testing and
# comparison (e.g. SAN vs NAS, old vs new hardware).
# -----------------------------------------------------------------------------

# declare -A TARGETS=()

# Load configuration
if [[ -f ".env" ]]; then
  # shellcheck disable=SC1091
  source ".env"
else
  echo "Please create .env from env.sample."
  exit 1
fi

mkdir -p "${RESULT_DIR}"

# Optional: set CPU governor
maybe_set_governor() {
  if [[ "${SET_PERFORMANCE_GOVERNOR}" == "true" ]] && [[ -w /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]]; then
    echo "Setting CPU governor to performance"
    for g in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do echo performance | sudo tee "$g" >/dev/null; done
  fi
}

# Optional: drop caches
drop_caches() {
  if [[ "${DROP_CACHES}" == "true" ]] && [[ -w /proc/sys/vm/drop_caches ]]; then
    echo "Dropping caches..."
    sudo sh -c "sync; echo 3 > /proc/sys/vm/drop_caches"
  fi
}

# Check prerequisites
command -v fio >/dev/null || { echo "fio not found"; exit 2; }

maybe_set_governor

env | sort

mkdir -p "${IOTEST_DIR}/work" && cd "${IOTEST_DIR}/work"

# Test runs
for target in "${!TARGETS[@]}"; do
  dir="${TARGETS[$target]}"
  echo "Checking target directory: $dir"
  [[ -d "$dir" ]] || { echo "Target directory missing: $dir"; exit 3; }

  echo ">>> Target: $target -> $dir"
  for test in "${TESTS[@]}"; do
    echo "  -> Test: $test"
    for run in $(seq 1 "${RUNS}"); do
      ts=$(date +"%Y%m%d_%H%M%S")
      out="${RESULT_DIR}/${target}__${test}__run${run}.json"
      echo "     Run ${run}/${RUNS} -> ${out}"

      drop_caches

      SIZE_GB=${SIZE_GB} \
      NUMJOBS=${NUMJOBS} \
      IODEPTH=${IODEPTH} \
      NUMJOBS=${NUMJOBS} \
      RUNTIME=${RUNTIME} \
      RAMP_TIME=${RAMP_TIME} \
      fio ${IOTEST_DIR}/fio/global.fio \
        ${IOTEST_DIR}/fio/${test}.fio \
        --filename="${dir}/fio_${test}.dat" \
        --output="${out}" \
        --output-format=json
      # Do not delete the test file afterwards so different rw patterns can use identical data blocks.
    done
  done
done

cd -

echo
echo "All runs completed. Raw data is located at: ${RESULT_DIR}"
