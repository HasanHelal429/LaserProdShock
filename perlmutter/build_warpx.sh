#!/bin/bash -l
# Build the warpx-cda 1D CUDA binary on Perlmutter, at a pinned commit.
#
#   perlmutter/build_warpx.sh
#
# One binary, unlike KinShock2020's A/B: every P5 leg is full PIC driven by the
# ray-tracing deposition operator, so there is nothing to bisect on the binary.
#
# The heavy lifting is upstream's: Tools/machines/perlmutter-nersc/ carries the module
# set, AMREX_CUDA_ARCH=8.0 (A100) and an installer for boost/adios2/blaspp/lapackpp.
# Run install_gpu_dependencies.sh ONCE before the first build; idempotent but slow.

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[[ -f "$HERE/site.conf" ]] || { echo "create $HERE/site.conf from site.conf.example" >&2; exit 1; }
set +u
# shellcheck disable=SC1090
source "$HERE/site.conf"
set -u

[[ -n "${MY_PROFILE:-}" ]] || {
    echo "build: sourcing the WarpX Perlmutter profile"
    # shellcheck disable=SC1090
    source "$HOME/perlmutter_gpu_warpx.profile"
}
: "${AMREX_CUDA_ARCH:?the WarpX profile did not load - check \$HOME/perlmutter_gpu_warpx.profile}"

cd "$WARPX_SRC"
# Detached HEAD on purpose: this is a build tree, not a working branch, and it makes the
# binary's provenance a SHA rather than "whatever the branch was that day" -- which is
# exactly how a fork-only input went unnoticed for 27 runs in the sibling project.
git fetch --all --tags
git checkout --detach "$WARPX_COMMIT"

cmake -S . -B "$WARPX_BUILD" \
    -DWarpX_DIMS=1 -DWarpX_COMPUTE=CUDA \
    -DAMReX_CUDA_ARCH="${AMREX_CUDA_ARCH}" \
    -DWarpX_MPI=ON -DWarpX_MPI_THREAD_MULTIPLE=ON \
    -DWarpX_PRECISION=DOUBLE -DWarpX_OPENPMD=ON \
    -DWarpX_EB=ON -DWarpX_QED=ON -DWarpX_FFT=OFF \
    -DWarpX_APP=ON -DWarpX_LIB=ON -DWarpX_PYTHON=OFF \
    -DCMAKE_BUILD_TYPE=Release
cmake --build "$WARPX_BUILD" -j 16

BIN="$(ls "$WARPX_BUILD"/bin/warpx.1d* 2>/dev/null | head -1)"
echo "--- built: $BIN"
echo "--- provenance: $WARPX_COMMIT ($(git rev-parse --short HEAD))"

# THE CHECK THAT MATTERS. A binary predating a deck's flag IGNORES it silently -- WarpX
# never queries the key and says nothing. That cost 4.6 h once on chablis. Every input
# key P5 depends on is grepped for here, at build time, so a missing one is found before
# a 20-hour run rather than after it.
echo "--- input keys this build implements:"
# Extract ONCE: this binary is ~0.5 GB and the old loop ran `strings` twice per key.
#
# Two traps, both of which made this check useless the first time it ran on Perlmutter:
#  1. `strings ... | grep -q` under `set -o pipefail` reports FAILURE even on a match --
#     grep -q exits at the first hit, strings dies of SIGPIPE, and the pipeline returns
#     141. Every key came back MISSING. Grep a saved file instead of a pipe.
#  2. `grep -x` cannot match here. The constant pool packs literals back-to-back with no
#     NUL between them (`..._distribution_t` runs straight into `VelocityProperti`), so a
#     whole-line match never succeeds. Substring is the only sound test.
_KEYDUMP="$(mktemp "${TMPDIR:-/tmp}/warpx_keys.XXXXXX")"
trap 'rm -f "$_KEYDUMP"' EXIT
strings "$BIN" > "$_KEYDUMP" 2>/dev/null || true
for key in laser_deposition ray_cfl temperature_mode coulomb_log_mode \
           min_macroparticles_per_cell maxwellian_u_std_distribution_type \
           maxwellian_u_mean_distribution_type parse_density_function; do
    if grep -qF -- "$key" "$_KEYDUMP"; then
        echo "      OK      $key"
    else
        echo "      UNPROVEN $key   <-- not found as a contiguous literal."
        echo "               NOT proof of absence: check the source, then confirm with"
        echo "               make_inputs.py --verify seconds after launch."
    fi
done
echo
echo "The lifted-IC legs (corona_profile: flash_table) need the last three: the density,"
echo "temperature and drift profiles are all emitted as parser functions."
