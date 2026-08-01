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
#   6. Runs `make tests` and relays its exit code.
#   7. Tears down the VM and removes all temp files (unless KEEP_VM=1).
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
#   KEEP_VM           if "1", keep the snapshot qcow2 and seed ISO on exit
#   SKIP_DOWNLOAD     if "1", reuse an already-downloaded image in CACHE_DIR
#   CACHE_DIR         where to store the downloaded image (default:
#                     $HOME/.cache/bleachbit-vm)
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

mkdir -p "$CACHE_DIR"
CACHED_XZ="$CACHE_DIR/${FREEBSD_IMAGE}.xz"
CACHED_IMG="$CACHE_DIR/$FREEBSD_IMAGE"

WORK_DIR="$(mktemp -d -t bleachbit-freebsd-XXXXXX)"
SNAPSHOT_IMG="$WORK_DIR/disk.qcow2"
SEED_ISO="$WORK_DIR/seed.iso"
SSH_KEY="$WORK_DIR/id_ed25519"
SSH_PUB="$WORK_DIR/id_ed25519.pub"
VM_LOG="$WORK_DIR/vm.log"
VM_PIDFILE="$WORK_DIR/vm.pid"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
log() { echo "[freebsd-test] $*"; }
err() { echo "[freebsd-test] ERROR: $*" >&2; }

cleanup() {
    local rc=$?
    local pid=""
    [[ -f "$VM_PIDFILE" ]] && pid="$(cat "$VM_PIDFILE" 2>/dev/null || true)"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
        log "Shutting down VM (pid $pid)"
        kill "$pid" 2>/dev/null || true
        # Wait briefly, then force.
        for _ in $(seq 1 20); do
            kill -0 "$pid" 2>/dev/null || break
            sleep 0.5
        done
        kill -9 "$pid" 2>/dev/null || true
    fi
    if [[ "$KEEP_VM" == "1" ]]; then
        log "KEEP_VM=1: leaving $WORK_DIR intact"
    else
        rm -rf "$WORK_DIR"
    fi
    exit "$rc"
}
trap cleanup EXIT INT TERM

ssh_opts=(
    -i "$SSH_KEY"
    -o IdentitiesOnly=yes
    -o StrictHostKeyChecking=no
    -o UserKnownHostsFile=/dev/null
    -o LogLevel=ERROR
    -o ConnectTimeout=10
    -p "$SSH_PORT"
)

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
# SSH keypair
# ---------------------------------------------------------------------------
log "Generating ephemeral SSH keypair"
ssh-keygen -q -t ed25519 -N "" -f "$SSH_KEY" -C bleachbit-freebsd-test

# ---------------------------------------------------------------------------
# Cloud-init NoCloud seed: meta-data + user-data, packed into an ISO
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Create a snapshot qcow2 backed by the cached image, then grow it
# ---------------------------------------------------------------------------
log "Creating snapshot qcow2 backed by $CACHED_IMG"
qemu-img create -f qcow2 -F qcow2 -b "$CACHED_IMG" "$SNAPSHOT_IMG"
# Grow the virtual size so pkg install + source tree fit comfortably.
qemu-img resize "$SNAPSHOT_IMG" "+$VM_DISK"

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
log "Waiting for SSH on localhost:$SSH_PORT (this can take a few minutes)"
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
# Install dependencies and run `make tests` inside the VM
# ---------------------------------------------------------------------------
# Delegate to scripts/install-deps.sh --dev, which bootstraps Bash and shares
# one dependency list with Linux and macOS. GTK is intentionally not installed:
# the VM has no display server, so is_gtk_available() returns False and GUI
# tests self-skip.
log "Installing FreeBSD dependencies and running tests inside the VM"
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

ssh "${ssh_opts[@]}" "root@localhost" "sh -s" <<<"$REMOTE_SCRIPT"
rc=$?
if [[ $rc -ne 0 ]]; then
    err "FreeBSD dependency installation failed (exit $rc)"
    exit $rc
fi

# Run `make tests` as the freebsd user (normal HOME, non-root file ownership).
log "Running make tests as $SSH_USER"
TEST_SCRIPT=$(cat <<'REMOTE'
set -eu
cd ~/bleachbit
echo "[vm] running: gmake tests"
MAKE=gmake PYTHON=python3
export MAKE PYTHON
if ! $MAKE tests; then
    echo "[vm] make tests FAILED" >&2
    exit 1
fi
echo "[vm] make tests PASSED"
REMOTE
)

if ssh "${ssh_opts[@]}" "${SSH_USER}@localhost" "sh -s" <<<"$TEST_SCRIPT"; then
    log "make tests PASSED in FreeBSD VM"
    exit_code=0
else
    rc=$?
    err "make tests FAILED in FreeBSD VM (exit $rc)"
    exit_code=$rc
fi

# Cleanup runs via the trap.
exit "$exit_code"
