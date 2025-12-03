#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: `./docker/build.sh <distro>`

This script tests BleachBit and builds packages insider a container.

Run this script from the host, not inside a container.

Supported distributions:
  debian    - run `make tests` and build .deb packages on Debian
  fedora    - run `make tests` and build RPM/SRPM packages on Fedora
  opensuse  - run `make tests` and build RPM/SRPM packages on openSUSE

Optional environment overrides:
  FEDORA_VERSION   Set Fedora macro used by the spec file
  SUSE_VERSION     Set openSUSE suse_version macro

Artifacts are written to `./docker-artifacts/<distro>` on the host.
EOF
}

if [[ $# -ne 1 ]]; then
    usage >&2
    exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: Docker CLI is required" >&2
    exit 1
fi

DISTRO=$1
ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
DOCKER_DIR="$ROOT_DIR/docker"
ARTIFACT_ROOT="$ROOT_DIR/docker-artifacts" # cleaned by `make clean`
mkdir -p "$ARTIFACT_ROOT"

HOME_IN_CONTAINER=/tmp/home # used by BleachBit, dnf, etc.
RUN_ENV=(--env HOME="$HOME_IN_CONTAINER" --env DISTRO_NAME="$DISTRO")
if [[ -n "${SKIP_TESTS:-}" ]]; then
    RUN_ENV+=(--env SKIP_TESTS="$SKIP_TESTS")
fi
USER_ID=$(id -u)
GROUP_ID=$(id -g)
IMAGE=""
DOCKERFILE=""

case "$DISTRO" in
    debian)
        IMAGE=bleachbit-build:debian
        DOCKERFILE="$DOCKER_DIR/Dockerfile.debian"
        ;;
    fedora)
        IMAGE=bleachbit-build:fedora
        DOCKERFILE="$DOCKER_DIR/Dockerfile.fedora"
        FEDORA_VERSION=${FEDORA_VERSION:-43}
        RUN_ENV+=(--env FEDORA_VERSION="$FEDORA_VERSION")
        ;;
    opensuse)
        IMAGE=bleachbit-build:opensuse
        DOCKERFILE="$DOCKER_DIR/Dockerfile.opensuse"
        SUSE_VERSION=${SUSE_VERSION:-1699}
        RUN_ENV+=(--env SUSE_VERSION="$SUSE_VERSION")
        ;;
    *)
        echo "ERROR: unsupported distro '$DISTRO'" >&2
        usage >&2
        exit 1
        ;;
esac

CONTAINER_CMD=$(cat <<'EOF'
set -euo pipefail
bash /work/docker/inside_container.sh
EOF
)

if [[ ! -f "$DOCKERFILE" ]]; then
    echo "ERROR: missing $DOCKERFILE" >&2
    exit 1
fi

ARTIFACT_DIR="$ARTIFACT_ROOT/$DISTRO"
mkdir -p "$ARTIFACT_DIR"

DOCKER_BUILD_CONTEXT="$DOCKER_DIR"

echo "[docker] Building image $IMAGE from $(basename "$DOCKERFILE")" >&2
docker build --pull -f "$DOCKERFILE" -t "$IMAGE" "$DOCKER_BUILD_CONTEXT"

echo "[docker] Running build and tests inside $IMAGE" >&2
docker run --rm \
    --user "$USER_ID:$GROUP_ID" \
    -v "$ROOT_DIR":/work:ro \
    -v "$ARTIFACT_DIR":/artifacts \
    "${RUN_ENV[@]}" \
    "$IMAGE" bash -lc "$CONTAINER_CMD"

echo "Artifacts saved to $ARTIFACT_DIR" >&2
