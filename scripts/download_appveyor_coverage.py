#!/usr/bin/env python3
"""Download a .coverage artifact from an AppVeyor build.

This replaces the unmaintained appveyor-artifacts package. Last release
was May 2016
https://pypi.org/project/appveyor-artifacts/#history

It failed when AppVeyor returned a "starting" job status (VM provisioning).

Usage of the replacement:
    python scripts/download_appveyor_coverage.py -o OWNER -n REPO -c COMMIT [-m]

The .coverage file is downloaded to the current directory.  When `-m` is
given, Windows paths inside the file are rewritten to Linux paths so that
`coverage combine` can merge it with a Linux .coverage file.
"""

import argparse
import os
import re
import sys
import time

import requests

API_PREFIX = "https://ci.appveyor.com/api"
SLEEP_SEC = 10  # seconds between polls
QUEUE_TIMEOUT_SEC = 120  # how long to wait for the build to appear in history (s)
BUILD_TIMEOUT_SEC = 1800  # how long to wait for the build to finish (s)
API_TIMEOUT_SEC = 30
REGEX_MANGLE = re.compile(r'"(C:\\\\projects\\\\(?:(?!": \[).)+)')
BAD_STATUSES = {"failed", "cancelled", "cancelling"}
MAX_READ_SIZE_BYTES = 52428800

def query_api(endpoint):
    """Query the AppVeyor REST API and return parsed JSON."""
    url = API_PREFIX + endpoint
    for attempt in range(3):
        try:
            response = requests.get(
                url, headers={"content-type": "application/json"}, timeout=API_TIMEOUT_SEC
            )
            response.raise_for_status()
            return response.json()
        except (requests.exceptions.RequestException, ValueError) as exc:
            if attempt == 2:
                raise
            print(f"Network error, retrying in 1s: {exc}")
            time.sleep(1)


def find_build_version(owner, repo, commit):
    """Return the AppVeyor build version for *commit*, or ``None``."""
    endpoint = f"/projects/{owner}/{repo}/history?recordsNumber=10"
    data = query_api(endpoint)
    for build in data.get("builds", []):
        if build.get("commitId") == commit:
            return build["version"]
    return None


def wait_for_build(owner, repo, build_version):
    """Poll until the build finishes and return the list of job IDs."""
    endpoint = f"/projects/{owner}/{repo}/build/{build_version}"
    deadline = time.time() + BUILD_TIMEOUT_SEC
    while time.time() < deadline:
        data = query_api(endpoint)
        jobs = data["build"]["jobs"]
        statuses = {job["status"] for job in jobs}

        if statuses & BAD_STATUSES:
            bad = [j for j in jobs if j["status"] in BAD_STATUSES]
            raise RuntimeError(f"AppVeyor job(s) did not succeed: {bad}")

        if statuses == {"success"}:
            print(f"Build successful. Found {len(jobs)} job(s).")
            return [job["jobId"] for job in jobs]

        if "running" in statuses:
            print("Waiting for job(s) to finish...")
        elif "starting" in statuses:
            print("Waiting for VM to start...")
        elif "queued" in statuses:
            print("Waiting for all jobs to start...")
        else:
            print(f"Waiting (statuses: {sorted(statuses)})...")
        time.sleep(SLEEP_SEC)
    raise RuntimeError("Timed out waiting for AppVeyor build to finish.")


def download_coverage_artifact(job_id):
    """Download the .coverage artifact from *job_id* into the cwd."""
    artifacts = query_api(f"/buildjobs/{job_id}/artifacts")
    target = None
    for artifact in artifacts:
        if os.path.basename(artifact["fileName"]) == ".coverage":
            target = artifact
            break
    if target is None:
        available = [a["fileName"] for a in artifacts]
        raise RuntimeError(f"No .coverage artifact. Available: {available}")

    download_url = (
        f"{API_PREFIX}/buildjobs/{job_id}/artifacts/{target['fileName']}"
    )
    response = requests.get(download_url, stream=True, timeout=API_TIMEOUT_SEC)
    response.raise_for_status()
    with open(".coverage", "wb") as handle:
        for chunk in response.iter_content(8192):
            handle.write(chunk)
    size = os.path.getsize(".coverage")
    print(f"Downloaded .coverage ({size} bytes)")


def mangle_coverage():
    """Rewrite Windows paths in .coverage to Linux paths.

    Only applies to the legacy text format (starts with `!coverage.py:`);
    SQLite-based .coverage files (coverage >= 5.0) are left untouched because
    `coverage combine` handles path remapping internally for those.
    """
    with open(".coverage", "rb") as handle:
        if handle.read(13) != b"!coverage.py:":
            print(".coverage is SQLite format; skipping path mangling.")
            return
        handle.seek(0)
        contents = handle.read(MAX_READ_SIZE_BYTES).decode("utf-8")

    for windows_path in set(REGEX_MANGLE.findall(contents)):
        unix_relative = windows_path.replace("\\\\", "/").split("/", 3)[-1]
        unix_absolute = os.path.abspath(unix_relative)
        if not os.path.isfile(unix_absolute):
            raise RuntimeError(f"No such file after path conversion: {unix_absolute}")
        contents = contents.replace(windows_path, unix_absolute)

    with open(".coverage", "w", encoding="utf-8") as handle:
        handle.write(contents)
    print("Mangled Windows paths to Linux paths.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download .coverage artifact from AppVeyor."
    )
    parser.add_argument("-o", "--owner", required=True, help="Repository owner.")
    parser.add_argument("-n", "--repo", required=True, help="Repository name.")
    parser.add_argument("-c", "--commit", required=True, help="Git commit SHA.")
    parser.add_argument(
        "-m",
        "--mangle",
        action="store_true",
        help="Rewrite Windows paths to Linux paths.",
    )
    args = parser.parse_args()

    # Wait for the build to appear in AppVeyor's history.
    build_version = None
    deadline = time.time() + QUEUE_TIMEOUT_SEC
    while time.time() < deadline:
        build_version = find_build_version(args.owner, args.repo, args.commit)
        if build_version:
            break
        print("Waiting for job to be queued...")
        time.sleep(SLEEP_SEC)
    if not build_version:
        raise RuntimeError("Timed out waiting for job to be queued or build not found.")
    print(f"Found build version: {build_version}")

    job_ids = wait_for_build(args.owner, args.repo, build_version)

    for job_id in job_ids:
        try:
            download_coverage_artifact(job_id)
            if args.mangle:
                mangle_coverage()
            return 0
        except RuntimeError as exc:
            print(f"Job {job_id}: {exc}")
    raise RuntimeError("No .coverage artifact found in any job.")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
