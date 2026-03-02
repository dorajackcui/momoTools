import argparse
import subprocess
import sys


RESTRICTED_PREFIXES = (
    "tests/_private_data/",
)

ALLOWED_PATHS = {
    "tests/_private_data/README.md",
}


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        check=False,
        capture_output=True,
        text=True,
    )


def _normalize_paths(raw: str) -> list[str]:
    return [line.strip().replace("\\", "/") for line in raw.splitlines() if line.strip()]


def _is_restricted(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if normalized in ALLOWED_PATHS:
        return False
    return any(normalized.startswith(prefix) for prefix in RESTRICTED_PREFIXES)


def _collect_staged_paths() -> list[str]:
    result = _run_git(["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    if result.returncode != 0:
        return []
    return _normalize_paths(result.stdout)


def _collect_push_paths(stdin_payload: str) -> list[str]:
    blocked: list[str] = []
    lines = [line.strip() for line in stdin_payload.splitlines() if line.strip()]
    for line in lines:
        parts = line.split()
        if len(parts) < 2:
            continue
        old_sha, new_sha = parts[0], parts[1]
        if set(new_sha) == {"0"}:
            continue

        if set(old_sha) == {"0"}:
            result = _run_git(["ls-tree", "-r", "--name-only", new_sha])
        else:
            result = _run_git(["diff", "--name-only", "--diff-filter=ACMR", old_sha, new_sha])

        if result.returncode != 0:
            continue

        blocked.extend(_normalize_paths(result.stdout))
    return blocked


def _print_blocked(blocked_paths: list[str]) -> int:
    unique_blocked = sorted({path for path in blocked_paths if _is_restricted(path)})
    if not unique_blocked:
        return 0

    sys.stderr.write("ERROR: Private test data detected. Commit/Push blocked.\n")
    sys.stderr.write("The following paths are forbidden:\n")
    for path in unique_blocked:
        sys.stderr.write(f"  - {path}\n")
    sys.stderr.write("Move them outside repo or keep them under ignored local-only workflow.\n")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("pre-commit", "pre-push"), required=True)
    args = parser.parse_args()

    if args.mode == "pre-commit":
        return _print_blocked(_collect_staged_paths())

    stdin_payload = sys.stdin.read()
    return _print_blocked(_collect_push_paths(stdin_payload))


if __name__ == "__main__":
    raise SystemExit(main())
