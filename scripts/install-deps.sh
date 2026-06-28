#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# Install BleachBit's Linux dependencies for running from source
# and (optionally) for development, testing, and packaging.
#
# Usage:
#   ./scripts/install-deps.sh            # runtime deps only
#   ./scripts/install-deps.sh --dev      # runtime + build/test/packaging deps
#   ./scripts/install-deps.sh --help
#
# Distro is auto-detected from /etc/os-release. Supported families:
#   debian  (Debian, Ubuntu, Mint, etc.)          -> apt
#   fedora  (Fedora, RHEL, Alma, CentOS, etc.)    -> dnf
#   opensuse (Tumbleweed, Leap)                   -> zypper
#   arch    (Arch, Manjaro, etc.)                 -> pacman
#
# This Bash script works similarly to:
#   - .github/workflows/test_ubuntu.yaml
#   - bleachbit.spec
#   - debian/debian.control
#   - docker/Dockerfile.*

set -euo pipefail

MODE="runtime"

usage() {
    cat <<'EOF'
Usage: ./scripts/install-deps.sh [--dev] [--help]

  (no flag)   Install runtime dependencies (enough to run from source).
  --dev       Also install build, test, lint, and packaging tools.
  --help      Show this help.

Distro is auto-detected from /etc/os-release.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dev)  MODE="dev"; shift ;;
        --help|-h) usage; exit 0 ;;
        *) echo "ERROR: unknown argument '$1'" >&2; usage >&2; exit 2 ;;
    esac
done

# Detect distribution family from /etc/os-release.
detect_distro() {
    if [[ ! -r /etc/os-release ]]; then
        echo "ERROR: /etc/os-release not found; cannot detect distribution." >&2
        echo "       This script supports Debian, Fedora, openSUSE, and Arch families." >&2
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
            echo "       Supported: debian, fedora, opensuse, arch." >&2
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
        python3-chardet
        python3-gi
        python3-psutil
        python3-requests
        python3-setuptools
        xdg-utils
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
        python3-autopep8
        python3-pip
        python3-pyflakes
        pylint
        shellcheck
        appstream
    )
    echo "[debian] apt-get update"
    sudo apt-get update
    echo "[debian] installing runtime deps"
    sudo apt-get install -y --no-install-recommends "${runtime[@]}"
    if [[ "$MODE" == "dev" ]]; then
        echo "[debian] installing dev/test/packaging deps"
        sudo apt-get install -y --no-install-recommends "${dev[@]}"
    fi
}

# --- Fedora / RHEL family (dnf) ----------------------------------------------
install_fedora() {
    local runtime=(
        gobject-introspection
        gtk3
        libnotify
        python3
        python3-chardet
        python3-gobject
        python3-psutil
        python3-requests
        python3-setuptools
        xdg-utils
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
        python3-autopep8
        python3-pip
        python3-pyflakes
        pylint
        ShellCheck
        appstream
        redhat-rpm-config
        rpm-build
        rpmdevtools
        tar
        which
        xz
    )
    # skip dnf update: focus on just the installation.
    echo "[fedora] installing runtime deps"
    sudo dnf install -y --setopt=install_weak_deps=False "${runtime[@]}"
    if [[ "$MODE" == "dev" ]]; then
        echo "[fedora] installing dev/test/packaging deps"
        sudo dnf install -y --setopt=install_weak_deps=False "${dev[@]}"
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
        "${py}-chardet"
        "${py}-gobject"
        "${py}-gobject-Gdk"
        "${py}-psutil"
        "${py}-requests"
        "${py}-setuptools"
        update-desktop-files
        xdg-utils
    )
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
    # Lint tools on openSUSE are packaged differently; install via pip
    # in dev mode if the system packages are unavailable.
    echo "[opensuse] installing runtime deps"
    sudo zypper --non-interactive install --no-recommends "${runtime[@]}"
    if [[ "$MODE" == "dev" ]]; then
        echo "[opensuse] installing dev/test/packaging deps"
        sudo zypper --non-interactive install --no-recommends "${dev[@]}"
        # pylint/pyflakes/autopep8 may not be in the main repos;
        # fall back to pip --user for the lint tooling used by `make pretty`/`make lint`.
        if ! command -v pylint >/dev/null 2>&1; then
            echo "[opensuse] installing lint tools via pip --user"
            pip install --user --break-system-packages pylint pyflakes autopep8 || \
                pip install --user pylint pyflakes autopep8
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
        python-chardet
        python-gobject
        python-psutil
        python-requests
        python-setuptools
        xdg-utils
    )
    local dev=(
        appstream
        base-devel
        desktop-file-utils
        dos2unix
        gettext
        libxml2
        python-autopep8
        python-pip
        python-pyflakes
        pylint
        shellcheck
    )
    # no `pacman -Sy` to avoid partial upgrade.
    # no `pacman -Syu` to avoid full upgrade that user may not want now.
    echo "[arch] installing runtime deps"
    sudo pacman -S --needed --noconfirm "${runtime[@]}"
    if [[ "$MODE" == "dev" ]]; then
        echo "[arch] installing dev/test/lint deps"
        sudo pacman -S --needed --noconfirm "${dev[@]}"
    fi
}

main() {
    local distro
    distro="$(detect_distro)"
    echo "Detected distribution family: $distro"
    echo "Mode: $MODE"
    case "$distro" in
        debian)   install_debian   ;;
        fedora)   install_fedora   ;;
        opensuse) install_opensuse ;;
        arch)     install_arch     ;;
        *) echo "ERROR: unsupported distro '$distro'" >&2; exit 1 ;;
    esac
    echo
    echo "Done. You can now run BleachBit from source:"
    echo "  make -C po local   # build translations"
    echo "  python3 bleachbit.py"
    if [[ "$MODE" == "dev" ]]; then
        echo
        echo "And run the test suite:"
        echo "  make tests"
    fi
}

main
