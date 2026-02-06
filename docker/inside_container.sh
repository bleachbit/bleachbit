#!/bin/bash
# Run this script from inside the Docker container.
set -euo pipefail

if [[ -z "${DISTRO_NAME:-}" ]]; then
    echo "ERROR: DISTRO_NAME environment variable is not set" >&2
    exit 1
fi

# if /artifacts does not exist, fail
if [[ ! -d /artifacts ]]; then
    echo "ERROR: /artifacts does not exist. Are you in the container?" >&2
    exit 1
fi

TMP_SRC=/tmp/src

# BleachBit and other software expect HOME.
setup_home() {
    mkdir -p "$HOME"
    if [[ ! -f "$HOME/.profile" ]]; then
        install -m 644 /dev/null "$HOME/.profile"
    fi
}

prepare_source() {
    rm -rf "$TMP_SRC"
    cp -a /work/. "$TMP_SRC"
    cd "$TMP_SRC"
}

run_optional_tests() {
    if [[ -z "${SKIP_TESTS:-}" ]]; then
        make tests
    else
        echo "SKIP_TESTS is set, so skipping `make tests`."
    fi
}

copy_tree() {
    local src=$1
    local dest=$2
    if [[ -d $src ]]; then
        mkdir -p "$dest"
        cp -a "$src/." "$dest/"
    fi
}

prep_redhat() {
    run_optional_tests
    python3 setup.py sdist --dist-dir /tmp/dist
    rpmdev-setuptree
    shopt -s nullglob
    for archive in /tmp/dist/bleachbit-*.tar.gz; do
        cp -a "$archive" "$HOME/rpmbuild/SOURCES/"
    done
    cp -a bleachbit.spec "$HOME/rpmbuild/SPECS/"
}

setup_home
prepare_source
mkdir -p /artifacts

case "$DISTRO_NAME" in
    debian)
        run_optional_tests
        pushd debian >/dev/null
        ln -sf debian.rules rules
        ln -sf debian.control control
        ln -sf debian.changelog changelog
        popd >/dev/null
        dpkg-buildpackage -us -uc -b
        cd /tmp
        shopt -s nullglob
        for artifact in bleachbit_*; do
            cp -a "$artifact" /artifacts/
        done
        ;;
    py314-pytest)
        if [[ -n "${SKIP_TESTS:-}" ]]; then
            echo "SKIP_TESTS is set, so skipping pytest." >&2
            exit 0
        fi
        xvfb-run -a python -m pytest -q \
            tests/TestGUI.py \
            tests/TestGuiChaff.py
        ;;
    fedora)
        prep_redhat
        rpmbuild -ba "$HOME/rpmbuild/SPECS/bleachbit.spec" \
            --define "fedora_version ${FEDORA_VERSION}" \
            --define "is_redhat_family 1"
        copy_tree "$HOME/rpmbuild/RPMS" /artifacts/RPMS
        copy_tree "$HOME/rpmbuild/SRPMS" /artifacts/SRPMS
        ;;
    opensuse)
        prep_redhat
        rpmbuild -ba "$HOME/rpmbuild/SPECS/bleachbit.spec" \
            --define "is_opensuse 1" \
            --define "suse_version ${SUSE_VERSION}"
        copy_tree "$HOME/rpmbuild/RPMS" /artifacts/RPMS
        copy_tree "$HOME/rpmbuild/SRPMS" /artifacts/SRPMS
        ;;
    *)
        echo "ERROR: unsupported DISTRO_NAME '$DISTRO_NAME'" >&2
        exit 1
        ;;
esac