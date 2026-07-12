#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# Install BleachBit's Linux and macOS dependencies for running from source
# and (optionally) for development, testing, and packaging.
#
# Usage:
#   ./scripts/install-deps.sh            # runtime deps only
#   ./scripts/install-deps.sh --dev      # runtime + build/test/packaging deps
#   ./scripts/install-deps.sh --venv     # runtime deps + create a Python venv
#   ./scripts/install-deps.sh --dev --venv
#   ./scripts/install-deps.sh --help
#
# --venv creates a virtual environment (default ./.venv, override with
# VENV_DIR=/path) and installs pure-Python dependencies into it via pip.
# On Linux, native libraries (GTK, GObject introspection, etc.) are still
# installed via the system package manager because PyGObject cannot be
# pip-installed reliably. On macOS, GTK/GObject is ignored and only the
# venv is used.
#
# Distro is auto-detected from /etc/os-release; macOS is detected via uname.
# Supported families:
#   debian  (Debian, Ubuntu, Mint, etc.)          -> apt
#   fedora  (Fedora, RHEL, Alma, CentOS, etc.)    -> dnf
#   opensuse (Tumbleweed, Leap)                   -> zypper
#   arch    (Arch, Manjaro, etc.)                 -> pacman
#   macos   (macOS)                               -> pip in venv
#
# This Bash script works similarly to:
#   - .github/workflows/test_ubuntu.yaml
#   - bleachbit.spec
#   - debian/debian.control
#   - docker/Dockerfile.*
#   - requirements.txt
#
# This Bash script installs optional dependencies.

set -euo pipefail

MODE="runtime"
VENV=0
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="${VENV_DIR:-$REPO_ROOT/.venv}"

usage() {
    cat <<'EOF'
Usage: ./scripts/install-deps.sh [--dev] [--venv] [--help]

  (no flag)   Install runtime dependencies (enough to run from source).
  --dev       Also install build, test, lint, and packaging tools.
  --venv      Create a Python virtualenv (.venv) and install pure-Python
              deps into it with pip. On Linux, native libs are still
              installed via the system package manager. On macOS, GTK/
              GObject is ignored and --venv is used. Override the location
              with VENV_DIR=/path/to/venv.
  --help      Show this help.

Distro is auto-detected from /etc/os-release; macOS is detected via uname.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dev)  MODE="dev"; shift ;;
        --venv) VENV=1; shift ;;
        --help|-h) usage; exit 0 ;;
        *) echo "ERROR: unknown argument '$1'" >&2; usage >&2; exit 2 ;;
    esac
done

# Detect distribution family from /etc/os-release, or macOS via uname.
detect_distro() {
    if [[ "$(uname -s)" == "Darwin" ]]; then
        echo "macos"
        return
    fi
    if [[ ! -r /etc/os-release ]]; then
        echo "ERROR: /etc/os-release not found; cannot detect distribution." >&2
        echo "       This script supports Debian, Fedora, openSUSE, Arch, and macOS." >&2
        exit 1
    fi
    # shellcheck disable=SC1091
    . /etc/os-release
    case "${ID:-}:${ID_LIKE:-}" in
        debian:*|*:*debian*|ubuntu:*|linuxmint:*|pop:*|elementary:*) echo "debian" ;;
        fedora:*|*:*fedora*|rhel:*|centos:*|almalinux:*|rocky:*|ol:*) echo "fedora" ;;
        opensuse*:*|suse:*|*:suse*) echo "opensuse" ;;
        arch:*|*:arch*|manjaro:*|endeavouros:*|garuda:*|cachyos:*) echo "arch" ;;
        *)
            echo "ERROR: unsupported distribution (ID='${ID:-}', ID_LIKE='${ID_LIKE:-}')." >&2
            echo "       Supported: debian, fedora, opensuse, arch, macos." >&2
            exit 1
            ;;
    esac
}

# --- Debian family (apt) -----------------------------------------------------
install_debian() {
    local runtime=(
        gir1.2-gtk-3.0
        gir1.2-notify-0.7
        libgtk-3-0
        python3
        python3-gi
        python3-setuptools
        xdg-utils
    )
    local runtime_pip=(
        python3-chardet
        python3-distro
        python3-psutil
        python3-requests
    )
    local dev=(
        build-essential
        debhelper
        desktop-file-utils
        devscripts
        dh-python
        dos2unix
        fakeroot
        gettext
        libxml2-utils
        lintian
        locales
        python3-pip
        shellcheck
        appstream
    )
    local dev_pip=(
        python3-autopep8
        python3-pyflakes
        python3-pytest
        python3-pytest-xdist
        pylint
    )
    if [[ "$VENV" == 1 ]]; then
        runtime+=(python3-venv)
    fi
    echo "[debian] apt-get update"
    sudo apt-get update
    echo "[debian] installing runtime deps"
    sudo apt-get install -y --no-install-recommends "${runtime[@]}"
    if [[ "$VENV" == 0 ]]; then
        sudo apt-get install -y --no-install-recommends "${runtime_pip[@]}"
    fi
    if [[ "$MODE" == "dev" ]]; then
        echo "[debian] installing dev/test/packaging deps"
        sudo apt-get install -y --no-install-recommends "${dev[@]}"
        if [[ "$VENV" == 0 ]]; then
            sudo apt-get install -y --no-install-recommends "${dev_pip[@]}"
        fi
    fi
}

# --- Fedora / RHEL family (dnf) ----------------------------------------------
install_fedora() {
    local runtime=(
        gobject-introspection
        gtk3
        libnotify
        python3
        python3-gobject
        python3-setuptools
        xdg-utils
    )
    local runtime_pip=(
        python3-chardet
        python3-distro
        python3-psutil
        python3-requests
    )
    local dev=(
        desktop-file-utils
        dos2unix
        fdupes
        findutils
        gettext
        glibc-langpack-en
        libxml2
        make
        patch
        python3-pip
        ShellCheck
        appstream
        redhat-rpm-config
        rpm-build
        rpmdevtools
        tar
        which
        xz
    )
    local dev_pip=(
        python3-autopep8
        python3-pyflakes
        python3-pytest
        python3-pytest-xdist
        pylint
    )
    # skip dnf update: focus on just the installation.
    echo "[fedora] installing runtime deps"
    sudo dnf install -y --setopt=install_weak_deps=False "${runtime[@]}"
    if [[ "$VENV" == 0 ]]; then
        sudo dnf install -y --setopt=install_weak_deps=False "${runtime_pip[@]}"
    fi
    if [[ "$MODE" == "dev" ]]; then
        echo "[fedora] installing dev/test/packaging deps"
        sudo dnf install -y --setopt=install_weak_deps=False "${dev[@]}"
        if [[ "$VENV" == 0 ]]; then
            sudo dnf install -y --setopt=install_weak_deps=False "${dev_pip[@]}"
        fi
    fi
    sudo dnf clean all
}

# --- openSUSE family (zypper) ------------------------------------------------
detect_opensuse_python_prefix() {
    local candidates=()
    local candidate
    if command -v python3 >/dev/null 2>&1; then
        candidates+=("$(python3 -c 'import sys; print("python%d%d" % sys.version_info[:2])')")
    fi
    candidates+=(python313 python312 python311 python310 python39 python3)
    for candidate in "${candidates[@]}"; do
        if zypper --non-interactive info --type package "${candidate}-gobject" >/dev/null 2>&1; then
            echo "$candidate"
            return
        fi
    done
    echo "ERROR: could not find an openSUSE Python GObject package." >&2
    exit 1
}

install_opensuse() {
    echo "[opensuse] zypper refresh"
    sudo zypper --non-interactive refresh
    local py
    py="$(detect_opensuse_python_prefix)"
    echo "[opensuse] using Python package prefix: $py"
    local runtime=(
        gobject-introspection
        gtk3
        libnotify
        python3
        "${py}-gobject"
        "${py}-gobject-Gdk"
        "${py}-setuptools"
        update-desktop-files
        xdg-utils
    )
    local runtime_pip=(
        "${py}-chardet"
        "${py}-psutil"
        "${py}-requests"
    )
    # distro is a tiny pure-Python module not always packaged on openSUSE.
    local runtime_pip_extra=("${py}-distro")
    local dev=(
        desktop-file-utils
        dos2unix
        fdupes
        gettext-tools
        libxml2-tools
        make
        "${py}-pip"
        "${py}-sqlite-utils"
        "${py}-xml"
        python-rpm-macros
        rpm-build
        rpmdevtools
        ShellCheck
        timezone
    )
    local dev_pip=(
        "${py}-pytest"
        "${py}-pytest-xdist"
    )
    # Lint tools on openSUSE are packaged differently; install via pip
    # in dev mode if the system packages are unavailable.
    echo "[opensuse] installing runtime deps"
    sudo zypper --non-interactive install --no-recommends "${runtime[@]}"
    if [[ "$VENV" == 0 ]]; then
        sudo zypper --non-interactive install --no-recommends "${runtime_pip[@]}"
        # distro module: install if available, else it comes via pip/venv.
        sudo zypper --non-interactive install --no-recommends "${runtime_pip_extra[@]}" || true
    fi
    if [[ "$MODE" == "dev" ]]; then
        echo "[opensuse] installing dev/test/packaging deps"
        sudo zypper --non-interactive install --no-recommends "${dev[@]}"
        if [[ "$VENV" == 0 ]]; then
            sudo zypper --non-interactive install --no-recommends "${dev_pip[@]}" || true
            # pylint/pyflakes/autopep8 may not be in the main repos;
            # fall back to pip --user for the lint tooling used by `make pretty`/`make lint`.
            if ! command -v pylint >/dev/null 2>&1; then
                echo "[opensuse] installing lint tools via pip --user"
                pip install --user --break-system-packages pylint pyflakes autopep8 || \
                    pip install --user pylint pyflakes autopep8
            fi
        fi
    fi
    sudo zypper clean --all
}

# --- Arch family (pacman) ----------------------------------------------------
install_arch() {
    local runtime=(
        gtk3
        gobject-introspection
        libnotify
        python
        python-gobject
        python-setuptools
        xdg-utils
    )
    local runtime_pip=(
        python-chardet
        python-distro
        python-psutil
        python-requests
    )
    local dev=(
        appstream
        base-devel
        desktop-file-utils
        dos2unix
        gettext
        libxml2
        python-pip
        shellcheck
    )
    local dev_pip=(
        python-autopep8
        python-pyflakes
        python-pytest
        python-pytest-xdist
        pylint
    )
    # no `pacman -Sy` to avoid partial upgrade.
    # no `pacman -Syu` to avoid full upgrade that user may not want now.
    echo "[arch] installing runtime deps"
    sudo pacman -S --needed --noconfirm "${runtime[@]}"
    if [[ "$VENV" == 0 ]]; then
        sudo pacman -S --needed --noconfirm "${runtime_pip[@]}"
    fi
    if [[ "$MODE" == "dev" ]]; then
        echo "[arch] installing dev/test/lint deps"
        sudo pacman -S --needed --noconfirm "${dev[@]}"
        if [[ "$VENV" == 0 ]]; then
            sudo pacman -S --needed --noconfirm "${dev_pip[@]}"
        fi
    fi
}

# --- macOS (no native package manager; use pip in a venv) --------------------
install_macos() {
    echo "[macos] using pip in a venv (GTK/GObject is not installed on macOS)"
    if ! command -v python3 >/dev/null 2>&1; then
        echo "ERROR: python3 is required but not found." >&2
        echo "       Install the Xcode Command Line Tools or Python from python.org." >&2
        exit 1
    fi
    if ! python3 -m venv -h >/dev/null 2>&1; then
        echo "ERROR: python3 venv module is required but not available." >&2
        exit 1
    fi
    if [[ "$MODE" == "dev" ]]; then
        echo "[macos] dev/test/lint Python deps will be installed via venv"
    fi
}

setup_venv() {
    local req_file="$REPO_ROOT/requirements.txt"
    echo "[venv] creating virtual environment in $VENV_DIR"
    if [[ -d "$VENV_DIR" ]]; then
        echo "[venv] $VENV_DIR already exists; reusing it"
    else
        python3 -m venv "$VENV_DIR"
    fi
    # shellcheck disable=SC1091
    . "$VENV_DIR/bin/activate"
    pip install --upgrade pip setuptools
    echo "[venv] installing runtime Python deps from $req_file"
    pip install -r "$req_file"
    if [[ "$MODE" == "dev" ]]; then
        echo "[venv] installing dev/test/lint Python deps"
        pip install pylint pyflakes autopep8 pytest pytest-xdist
    fi
}

main() {
    local distro
    distro="$(detect_distro)"
    if [[ "$distro" == "macos" && "$VENV" == 0 ]]; then
        echo "[macos] defaulting to --venv"
        VENV=1
    fi
    echo "Detected distribution family: $distro"
    echo "Mode: $MODE"
    if [[ "$VENV" == 1 ]]; then
        echo "Virtualenv: $VENV_DIR"
    fi
    case "$distro" in
        debian)   install_debian   ;;
        fedora)   install_fedora   ;;
        opensuse) install_opensuse ;;
        arch)     install_arch     ;;
        macos)    install_macos    ;;
        *) echo "ERROR: unsupported distro '$distro'" >&2; exit 1 ;;
    esac
    if [[ "$VENV" == 1 ]]; then
        setup_venv
    fi
    echo
    echo "Done. You can now run BleachBit from source:"
    if [[ "$distro" != "macos" ]]; then
        echo "  make -C po local   # build translations"
    fi
    if [[ "$VENV" == 1 ]]; then
        echo "  . '$VENV_DIR/bin/activate'"
    fi
    echo "  python3 bleachbit.py"
    if [[ "$distro" == "macos" ]]; then
        echo "  (macOS uses the command-line interface; GTK/GObject is not installed)"
    fi
    if [[ "$MODE" == "dev" ]]; then
        echo
        echo "And run the test suite:"
        echo "  make tests"
    fi
}

main
