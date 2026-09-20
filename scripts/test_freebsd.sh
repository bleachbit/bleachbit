#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# Run BleachBit `make tests` inside a transient FreeBSD 15 virtual machine.
#
# What this script does:
#   1. Downloads a FreeBSD 15.1-RELEASE amd64 cloud-init qcow2 image (cached).
#   2. Builds a NoCloud seed ISO that injects an SSH public key and a small
#      bootstrap user-data script.
#   3. Boots the image under QEMU/KVM with a port-forwarded SSH (host:2222 ->
#      guest:22). A snapshot qcow2 is used so the downloaded image stays
#      read-only and the VM is ephemeral.
#   4. Copies the BleachBit source tree into the VM via scp (tar stream).
#   5. Bootstraps bash, then runs scripts/install-deps.sh --dev inside the VM
#      to install FreeBSD package dependencies (single source of truth shared
#      with Linux/macOS).
#   6. Runs `make tests` (or $TEST_TARGET) and relays its exit code.
#   7. Tears down the VM and removes temp files, unless the VM is being
#      persisted for reuse (KEEP_VM=1 or SKIP_INSTALL=1), in which case the
#      snapshot, seed ISO, SSH key, and VM metadata are kept in $CACHE_DIR/vm.
#
# Fast iteration: run once with KEEP_VM=1 to build and persist a VM, then
# repeat with SKIP_INSTALL=1 (and optionally TEST_TARGET="python3 -m unittest
# tests.TestSpecial -v") to skip the download, package install, and full
# test suite, re-syncing only the source tree and re-running the test.
#
# A persisted VM is only reusable under the configuration it was created with:
# the same FREEBSD_IMAGE, an intact SSH keypair/seed ISO pair, and the same
# CACHE_DIR with the base image still present. The script refuses to reuse a
# VM when any of these no longer match; remove $CACHE_DIR/vm to rebuild from
# scratch.
#
# The persisted snapshot ($CACHE_DIR/vm/disk.qcow2) is a copy-on-write overlay
# over the cached base image: it stores only the changes and reads everything
# else from the base image file. Keep CACHE_DIR stable and keep the base image
# while a persisted VM exists; deleting or replacing the base image (or moving
# CACHE_DIR) makes the snapshot unusable.
#
# GTK is not installed: the VM has no display server (-display none, no
# DISPLAY/WAYLAND_DISPLAY), so bleachbit.GtkShim.is_gtk_available() returns
# False and all GUI tests self-skip. Only the headless test suite runs.
#
# Usage:
#   ./scripts/test_freebsd.sh
#
# Environment overrides:
#   FREEBSD_VERSION   FreeBSD release version (default: 15.1)
#   FREEBSD_IMAGE     qcow2 base filename (default:
#                     FreeBSD-15.1-RELEASE-amd64-BASIC-CLOUDINIT-ufs.qcow2)
#   FREEBSD_URL       Full download URL (overrides the constructed one)
#   SSH_PORT          host port forwarded to guest:22 (default: 2222)
#   VM_MEM            VM RAM in MB (default: 4096)
#   VM_CPUS           VM vCPUs (default: 2)
#   VM_DISK           extra qcow2 size to grow the image, e.g. 10G (default: 8G)
#   SSH_USER          login user inside the image (default: freebsd)
#   KEEP_VM           if "1", persist the VM (snapshot qcow2, seed ISO, SSH
#                     key) in a stable directory under CACHE_DIR so a later
#                     run can reuse it. Implies a stable WORK_DIR.
#   SKIP_INSTALL      if "1", reuse a persisted VM (see KEEP_VM) and skip the
#                     install-deps.sh --dev block, going straight to copying
#                     the source tree and running tests. Requires that a VM
#                     was previously persisted with KEEP_VM=1. Implies a
#                     stable WORK_DIR.
#   TEST_TARGET       command to run instead of `make tests` (e.g.
#                     "python3 -m unittest tests.TestSpecial -v"). Useful for
#                     fast iteration on a single test module.
#   SKIP_DOWNLOAD     if "1", reuse an already-downloaded image in CACHE_DIR
#   CACHE_DIR         where to store the downloaded image and persisted VM
#                     (default: $HOME/.cache/bleachbit-vm); keep it stable
#                     while a persisted VM exists (see note above)
#
# Requires on the Ubuntu host:
#   qemu-system-x86_64, qemu-img, xorriso, ssh, scp, and /dev/kvm (recommended;
#   falls back to TCG if KVM is unavailable).

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
FREEBSD_VERSION="${FREEBSD_VERSION:-15.1}"
FREEBSD_IMAGE="${FREEBSD_IMAGE:-FreeBSD-${FREEBSD_VERSION}-RELEASE-amd64-BASIC-CLOUDINIT-ufs.qcow2}"
FREEBSD_URL="${FREEBSD_URL:-https://download.freebsd.org/releases/VM-IMAGES/${FREEBSD_VERSION}-RELEASE/amd64/Latest/${FREEBSD_IMAGE}.xz}"
SSH_PORT="${SSH_PORT:-2222}"
VM_MEM="${VM_MEM:-4096}"
VM_CPUS="${VM_CPUS:-2}"
VM_DISK="${VM_DISK:-8G}"
SSH_USER="${SSH_USER:-freebsd}"
KEEP_VM="${KEEP_VM:-0}"
SKIP_DOWNLOAD="${SKIP_DOWNLOAD:-0}"
CACHE_DIR="${CACHE_DIR:-$HOME/.cache/bleachbit-vm}"
SKIP_INSTALL="${SKIP_INSTALL:-0}"
TEST_TARGET="${TEST_TARGET:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

mkdir -p "$CACHE_DIR"
CACHED_XZ="$CACHE_DIR/${FREEBSD_IMAGE}.xz"
CACHED_IMG="$CACHE_DIR/$FREEBSD_IMAGE"

# log/err are defined early so the WORK_DIR guard below can use them.
log() { echo "[freebsd-test] $*"; }
err() { echo "[freebsd-test] ERROR: $*" >&2; }

# A stable WORK_DIR (under CACHE_DIR) is used whenever the user wants the VM
# to persist across invocations (KEEP_VM=1 or SKIP_INSTALL=1). Otherwise use a
# throwaway mktemp directory that the trap cleans up.
if [[ "$SKIP_INSTALL" == "1" || "$KEEP_VM" == "1" ]]; then
    WORK_DIR="$CACHE_DIR/vm"
    mkdir -p "$WORK_DIR"
else
    WORK_DIR="$(mktemp -d -t bleachbit-freebsd-XXXXXX)"
fi
SNAPSHOT_IMG="$WORK_DIR/disk.qcow2"
SEED_ISO="$WORK_DIR/seed.iso"
SSH_KEY="$WORK_DIR/id_ed25519"
SSH_PUB="$WORK_DIR/id_ed25519.pub"
VM_LOG="$WORK_DIR/vm.log"
VM_PIDFILE="$WORK_DIR/vm.pid"
VM_META="$WORK_DIR/vm.meta"
DEPS_MARKER="$WORK_DIR/deps-installed"

# REUSE_VM=1 means a persisted snapshot already exists in WORK_DIR and we can
# boot it directly instead of creating a fresh one off the base image.
REUSE_VM=0
if [[ -f "$SNAPSHOT_IMG" ]]; then
    REUSE_VM=1
fi

# A persisted snapshot is tied to the base image it was created from. Refuse
# to reuse it for a different image (e.g. after FREEBSD_VERSION changed),
# which would silently test the wrong release.
if [[ "$REUSE_VM" == "1" ]]; then
    if [[ ! -f "$VM_META" ]]; then
        err "Persisted VM in $WORK_DIR has no $VM_META marker."
        err "Remove $WORK_DIR to rebuild the VM, or restore the marker."
        exit 1
    fi
    stored_image="$(sed -n 's/^FREEBSD_IMAGE=//p' "$VM_META" 2>/dev/null)" || true
    if [[ -z "$stored_image" || "$stored_image" != "$FREEBSD_IMAGE" ]]; then
        err "Persisted VM in $WORK_DIR was created with image: ${stored_image:-unknown}"
        err "but FREEBSD_IMAGE is now: $FREEBSD_IMAGE"
        err "Remove $WORK_DIR (e.g. 'rm -rf \"$WORK_DIR\"') to rebuild the VM"
        err "for the new image, or set FREEBSD_IMAGE=$stored_image to reuse it."
        exit 1
    fi
fi

if [[ "$SKIP_INSTALL" == "1" ]]; then
    if [[ "$REUSE_VM" != "1" ]]; then
        err "SKIP_INSTALL=1 requires an existing persisted VM in $WORK_DIR."
        err "Run ./scripts/test_freebsd.sh with KEEP_VM=1 first to create one."
        exit 1
    fi
    if [[ ! -f "$DEPS_MARKER" ]]; then
        err "SKIP_INSTALL=1, but dependencies were never installed successfully"
        err "in this persisted VM (missing $DEPS_MARKER)."
        err "Run ./scripts/test_freebsd.sh with KEEP_VM=1 to complete the"
        err "dependency installation, or remove $WORK_DIR to rebuild."
        exit 1
    fi
fi

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
ssh_opts=(
    -i "$SSH_KEY"
    -o IdentitiesOnly=yes
    -o StrictHostKeyChecking=no
    -o UserKnownHostsFile=/dev/null
    -o LogLevel=ERROR
    -o ConnectTimeout=10
    -p "$SSH_PORT"
)

cleanup() {
    local rc=$?
    local pid=""
    local persist=0
    [[ "$KEEP_VM" == "1" || "$SKIP_INSTALL" == "1" ]] && persist=1
    [[ -f "$VM_PIDFILE" ]] && pid="$(cat "$VM_PIDFILE" 2>/dev/null || true)"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
        if [[ "$persist" == "1" ]]; then
            # The snapshot outlives this run, so power the guest down cleanly
            # instead of killing QEMU (which is like yanking the plug and can
            # leave the root filesystem dirty for the next boot). The tests
            # are already done at this point, so a poweroff is safe. Fall back
            # to kill if the guest does not exit promptly.
            log "Requesting graceful VM shutdown (pid $pid)"
            ssh "${ssh_opts[@]}" "root@localhost" "shutdown -p now" 2>/dev/null || true
            for _ in $(seq 1 40); do
                kill -0 "$pid" 2>/dev/null || break
                sleep 0.5
            done
        fi
        if kill -0 "$pid" 2>/dev/null; then
            log "Shutting down VM (pid $pid)"
            kill "$pid" 2>/dev/null || true
            # Wait briefly, then force.
            for _ in $(seq 1 20); do
                kill -0 "$pid" 2>/dev/null || break
                sleep 0.5
            done
            kill -9 "$pid" 2>/dev/null || true
        fi
    fi
    # Only wipe WORK_DIR when it's a throwaway mktemp dir. The stable dir
    # ($CACHE_DIR/vm) is used by KEEP_VM=1 and SKIP_INSTALL=1 and must survive
    # so the VM can be reused on a later run.
    if [[ "$persist" == "1" ]]; then
        log "Leaving persisted VM intact in $WORK_DIR"
    else
        rm -rf "$WORK_DIR"
    fi
    exit "$rc"
}
trap cleanup EXIT INT TERM

# ---------------------------------------------------------------------------
# Preflight checks
# ---------------------------------------------------------------------------
for bin in qemu-system-x86_64 qemu-img xorriso ssh scp; do
    if ! command -v "$bin" >/dev/null 2>&1; then
        err "missing required binary: $bin"
        exit 1
    fi
done

ACCEL=tcg
if [[ -w /dev/kvm ]]; then
    ACCEL=kvm
else
    log "WARNING: /dev/kvm not writable; falling back to TCG (slow)."
fi

# ---------------------------------------------------------------------------
# Download (and cache) the FreeBSD image
# ---------------------------------------------------------------------------
if [[ ! -f "$CACHED_IMG" ]]; then
    if [[ "$SKIP_DOWNLOAD" == "1" ]]; then
        err "SKIP_DOWNLOAD=1 but $CACHED_IMG is missing."
        err "Note: a persisted VM snapshot also needs this base image as its"
        err "backing file, so it must stay cached while the VM is kept."
        exit 1
    fi
    if [[ ! -f "$CACHED_XZ" ]]; then
        log "Downloading $FREEBSD_URL"
        wget -c -O "$CACHED_XZ" "$FREEBSD_URL"
    fi
    log "Decompressing $CACHED_XZ"
    # xz -dk writes the output next to the .xz file (same dir, name minus .xz),
    # which is exactly $CACHED_IMG, so no mv is needed.
    xz -dk -T0 "$CACHED_XZ"
else
    log "Using cached image $CACHED_IMG"
fi

# ---------------------------------------------------------------------------
# SSH keypair + NoCloud seed ISO (a matched set)
# ---------------------------------------------------------------------------
# The seed ISO embeds the public key, so the keypair and seed ISO must stay
# in sync: reuse both together, or rebuild both together. When a persisted VM
# is reused but one of them is missing, the key baked into the VM on first
# boot is unrecoverable without SSH access, so fail with a clear error.
KEY_PRESENT=0
[[ -f "$SSH_KEY" && -f "$SSH_PUB" ]] && KEY_PRESENT=1
SEED_PRESENT=0
[[ -f "$SEED_ISO" ]] && SEED_PRESENT=1

if [[ "$KEY_PRESENT" == "1" && "$SEED_PRESENT" == "1" ]]; then
    log "Reusing SSH keypair and seed ISO from $WORK_DIR"
elif [[ "$REUSE_VM" == "1" ]]; then
    err "Persisted VM found, but its SSH keypair or seed ISO is missing"
    err "(expected $SSH_KEY and $SEED_ISO)."
    err "The key injected into the VM on first boot is unrecoverable without"
    err "SSH access, so the VM cannot be reused."
    err "Remove $WORK_DIR (e.g. 'rm -rf \"$WORK_DIR\"') to rebuild the VM,"
    err "or restore the missing file(s)."
    exit 1
else
    # Fresh VM: generate a matched keypair and seed ISO together.
    log "Generating SSH keypair"
    ssh-keygen -q -t ed25519 -N "" -f "$SSH_KEY" -C bleachbit-freebsd-test

    INSTANCE_ID="bleachbit-$(date +%s)"

    # user-data: add SSH key for the freebsd user and grow root filesystem.
    # The base image uses `nuageinit` (FreeBSD's built-in cloud-init alternative)
    # to process the NoCloud seed. It handles ssh_authorized_keys and growpart.
    # Root access is obtained via `su root -c` (freebsd is in wheel, and su
    # works without a password when root's password is `*`).
    cat >"$WORK_DIR/user-data" <<EOF
#cloud-config
instance-id: $INSTANCE_ID
ssh_authorized_keys:
  - $(cat "$SSH_PUB")
growpart:
  mode: auto
  devices: ['/']
  ignore_growoff: true
EOF

    cat >"$WORK_DIR/meta-data" <<EOF
instance-id: $INSTANCE_ID
local-hostname: bleachbit-freebsd
EOF

    log "Building NoCloud seed ISO with xorriso"
    xorriso -as mkisofs -V cidata -rock -joliet -no-emul-boot \
        -o "$SEED_ISO" "$WORK_DIR/meta-data" "$WORK_DIR/user-data"
fi

# ---------------------------------------------------------------------------
# Create a snapshot qcow2 backed by the cached image, then grow it
# ---------------------------------------------------------------------------
if [[ "$REUSE_VM" == "1" ]]; then
    log "Reusing existing VM disk $SNAPSHOT_IMG"
    # disk.qcow2 is a copy-on-write overlay: unchanged blocks are read from
    # the base image whose absolute path is recorded in the snapshot. Verify
    # that path still matches the cache, so a CACHE_DIR change or a deleted
    # base image fails clearly here instead of with a cryptic qemu error (or
    # worse, silent corruption if the base image was replaced).
    backing="$(qemu-img info "$SNAPSHOT_IMG" 2>/dev/null | sed -n 's/^backing file: //p')" || true
    if [[ -z "$backing" || "$backing" != "$CACHED_IMG" ]]; then
        err "Persisted VM $SNAPSHOT_IMG expects backing image: ${backing:-<none>}"
        err "but the current cache holds: $CACHED_IMG"
        err "Keep CACHE_DIR stable and keep the base image around, or remove"
        err "$WORK_DIR to rebuild the VM from scratch."
        exit 1
    fi
else
    log "Creating snapshot qcow2 backed by $CACHED_IMG"
    qemu-img create -f qcow2 -F qcow2 -b "$CACHED_IMG" "$SNAPSHOT_IMG"
    # Grow the virtual size so pkg install + source tree fit comfortably.
    qemu-img resize "$SNAPSHOT_IMG" "+$VM_DISK"
    # Record which base image this snapshot was created from, so a later run
    # with a different FREEBSD_IMAGE (e.g. another FREEBSD_VERSION) is refused
    # instead of silently reusing the wrong VM.
    echo "FREEBSD_IMAGE=$FREEBSD_IMAGE" >"$VM_META"
fi

# ---------------------------------------------------------------------------
# Boot the VM
# ---------------------------------------------------------------------------
log "Booting FreeBSD VM (accel=$ACCEL, ${VM_MEM}M, ${VM_CPUS} cpus, ssh -> :$SSH_PORT)"
qemu-system-x86_64 \
    -accel "$ACCEL" \
    -m "$VM_MEM" \
    -smp "$VM_CPUS" \
    -drive file="$SNAPSHOT_IMG",if=virtio,format=qcow2 \
    -drive file="$SEED_ISO",if=virtio,format=raw,readonly=on,media=cdrom \
    -netdev user,id=net0,hostfwd=tcp::${SSH_PORT}-:22 \
    -device virtio-net-pci,netdev=net0 \
    -display none \
    -serial file:"$VM_LOG" \
    -pidfile "$VM_PIDFILE" \
    >"$VM_LOG" 2>&1 &

QEMU_PID=$!
# qemu writes the pidfile slightly later than fork; ensure it exists.
for _ in $(seq 1 20); do
    [[ -f "$VM_PIDFILE" ]] && break
    sleep 0.5
done

# ---------------------------------------------------------------------------
# Wait for SSH (freebsd user) to come up
# ---------------------------------------------------------------------------
log "Waiting for SSH on localhost:$SSH_PORT (started at $(date '+%H:%M:%S'), this can take a few minutes)"
SSH_READY=0
for _ in $(seq 1 120); do
    if ssh "${ssh_opts[@]}" "${SSH_USER}@localhost" true 2>/dev/null; then
        SSH_READY=1
        break
    fi
    if ! kill -0 "$QEMU_PID" 2>/dev/null; then
        err "QEMU exited before SSH became ready. Last serial output:"
        tail -n 80 "$VM_LOG" >&2 || true
        exit 1
    fi
    sleep 5
done
if [[ "$SSH_READY" != "1" ]]; then
    err "Timed out waiting for SSH. Last serial output:"
    tail -n 80 "$VM_LOG" >&2 || true
    exit 1
fi
log "Freebsd SSH is up"

# ---------------------------------------------------------------------------
# Get root access: the freebsd user is in wheel, and `su root -c 'cmd'`
# works without a password on FreeBSD when root's password is `*` (locked
# for direct login but su from wheel is allowed via PAM).
# ---------------------------------------------------------------------------
log "Verifying root access via su"
if ! ssh "${ssh_opts[@]}" "${SSH_USER}@localhost" "su root -c 'whoami'" 2>&1 | grep -q '^root$'; then
    err "su root -c 'whoami' did not return 'root'. Cannot get root access."
    exit 1
fi
log "Root access via su works (no password needed)"

# Helper: run a command as root in the VM via su (no password needed).
vm_root() {
    ssh "${ssh_opts[@]}" "${SSH_USER}@localhost" "su root -c '$1'"
}

# ---------------------------------------------------------------------------
# Set up root SSH access for easier batch commands
# ---------------------------------------------------------------------------
log "Setting up root SSH access"

# Pipe the public key through stdin to avoid quoting issues with the key
# content (which contains spaces).
cat "$SSH_PUB" | ssh "${ssh_opts[@]}" "${SSH_USER}@localhost" \
    "su root -c 'mkdir -p /root/.ssh && cat > /root/.ssh/authorized_keys && chmod 600 /root/.ssh/authorized_keys'"

# Enable PermitRootLogin with keys only. Use a heredoc to avoid quoting issues.
ssh "${ssh_opts[@]}" "${SSH_USER}@localhost" 'su root -c "grep -q ^PermitRootLogin /etc/ssh/sshd_config && sed -i \"\" \"s/^PermitRootLogin.*/PermitRootLogin prohibit-password/\" /etc/ssh/sshd_config || echo PermitRootLogin prohibit-password >> /etc/ssh/sshd_config"'

vm_root "service sshd restart"
sleep 3

# Verify root SSH works.
if ssh "${ssh_opts[@]}" "root@localhost" true 2>/dev/null; then
    log "Root SSH is up"
else
    err "Root SSH verification failed after setup."
    exit 1
fi

# ---------------------------------------------------------------------------
# Stream the BleachBit source tree into the VM
# ---------------------------------------------------------------------------
# Use a directory under the freebsd user's home (writable without sudo).
REMOTE_DIR="bleachbit"
log "Copying BleachBit source tree to VM (~/$REMOTE_DIR)"
tar -C "$REPO_ROOT" --exclude='.git' --exclude='__pycache__' \
    --exclude='*.pyc' --exclude='*.egg-info' --exclude='dist' \
    --exclude='build' --exclude='docker-artifacts' --exclude='.venv' \
    -czf - . \
    | ssh "${ssh_opts[@]}" "${SSH_USER}@localhost" \
        "mkdir -p ~/'$REMOTE_DIR' && tar -C ~/'$REMOTE_DIR' -xzf -"

# ---------------------------------------------------------------------------
# Install dependencies inside the VM (skipped when SKIP_INSTALL=1)
# ---------------------------------------------------------------------------
# Delegate to scripts/install-deps.sh --dev, which bootstraps Bash and shares
# one dependency list with Linux and macOS. GTK is intentionally not installed:
# the VM has no display server, so is_gtk_available() returns False and GUI
# tests self-skip.
if [[ "$SKIP_INSTALL" == "1" ]]; then
    log "SKIP_INSTALL=1: skipping dependency installation"
else
    log "Installing FreeBSD dependencies inside the VM"
    # Run the bootstrap as root via `sh -s` because Bash is not installed yet on
    # the base image. The installer starts with a POSIX sh bootstrap and then
    # re-execs itself with Bash for the test toolchain and runtime Python deps.
    REMOTE_SCRIPT=$(cat <<'REMOTE'
set -eu

export ASSUME_ALWAYS_YES=yes

echo "[vm] bootstrapping pkg"
pkg bootstrap -y

echo "[vm] pkg update"
pkg update -q

# Delegate the rest to the shared dependency installer. Run as root (we have
# root SSH), so install_freebsd() can run pkg. ~freebsd expands to the freebsd
# user's home, where the source tree was copied.
echo "[vm] running install-deps.sh --dev"
exec sh ~freebsd/bleachbit/scripts/install-deps.sh --dev
REMOTE
)

    ssh "${ssh_opts[@]}" "root@localhost" "sh -s" <<<"$REMOTE_SCRIPT" \
        || { rc=$?; err "FreeBSD dependency installation failed (exit $rc)"; exit $rc; }
    # Record success so a later SKIP_INSTALL=1 run knows the VM is fully
    # provisioned and never reuses a half-installed snapshot.
    touch "$DEPS_MARKER"
fi

# Run tests as the freebsd user (normal HOME, non-root file ownership).
# TEST_TARGET overrides the default `make tests` so a single test module can
# be re-run quickly during iteration.
if [[ -n "$TEST_TARGET" ]]; then
    RUN_CMD="$TEST_TARGET"
    LOG_LABEL="$TEST_TARGET"
else
    RUN_CMD="gmake tests"
    LOG_LABEL="make tests"
fi
log "Running $LOG_LABEL as $SSH_USER"
# Unquoted heredoc so $RUN_CMD expands locally; the rest contains no $ that
# needs to reach the remote shell verbatim. MAKE/PYTHON are exported so the
# default `gmake tests` invocation finds GNU make and python3 on FreeBSD.
TEST_SCRIPT=$(cat <<REMOTE
set -eu
cd ~/bleachbit
export MAKE=gmake PYTHON=python3
echo "[vm] running: $RUN_CMD"
if ! $RUN_CMD; then
    echo "[vm] test command FAILED" >&2
    exit 1
fi
echo "[vm] test command PASSED"
REMOTE
)

if ssh "${ssh_opts[@]}" "${SSH_USER}@localhost" "sh -s" <<<"$TEST_SCRIPT"; then
    log "$LOG_LABEL PASSED in FreeBSD VM"
    exit_code=0
else
    rc=$?
    err "$LOG_LABEL FAILED in FreeBSD VM (exit $rc)"
    exit_code=$rc
fi

# Cleanup runs via the trap.
exit "$exit_code"
