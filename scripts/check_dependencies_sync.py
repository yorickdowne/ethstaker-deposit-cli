#!/usr/bin/env python3
"""Verify that the pip lockfiles match uv.lock and satisfy pyproject.toml.

The runtime/executable path installs from the pinned, hashed lockfiles
(requirements.txt, requirements_test.txt), while the library metadata lives in
pyproject.toml and uses >= floor ranges. This check ensures the two never
silently diverge:

  1. Every dependency declared in pyproject.toml must appear in the
     corresponding lockfile.
  2. Every pin in those lockfiles must satisfy the range declared in
     pyproject.toml (so the locked set is always installable given the
     declared ranges).
  3. Each lockfile must list the same packages, pins and markers as the
     `uv export` output for uv.lock, and its hashes must be a superset of
     that output's, so transitive pins cannot drift between uv.lock and the
     requirements files. Extra hashes are allowed because Dependabot adds
     hashes for wheels that uv.lock omits (e.g. Python versions excluded by
     requires-python). `--locked` also fails if uv.lock is stale relative
     to pyproject.toml.

Run with --write to regenerate both lockfiles from uv.lock, --lock to run
`uv lock` first, or --upgrade [PKG ...] to run `uv lock --upgrade` (or
--upgrade-package for each PKG) first. --upgrade ignores Dependabot's
cooldown and takes the newest releases.

If uv is not installed, check 3 is skipped with a warning, unless the CI
environment variable is set, in which case it is an error.

Build-only requirements under build_configs/* are intentionally not checked,
as they are independent of pyproject.toml.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess  # noqa: S404
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MARKER_RE = re.compile(r"\s*;\s*.*$")
CONSTRAINT_RE = re.compile(r"^([^<>=!~;]+)\s*(.*)$")
VERSION_OP_RE = re.compile(r"^(==|!=|<=|>=|<|>|~=|===)?\s*([0-9][A-Za-z0-9._*+-]*)$")

UV_EXPORT = [
    "uv",
    "export",
    "--locked",
    "--no-dev",
    "--no-emit-project",
    "--no-header",
    "--no-annotate",
    "--format",
    "requirements.txt",
]
# pip is pulled in by pip-audit; pinning it would make `pip install -r` try to replace itself.
EXPORTS = {
    "requirements.txt": [],
    "requirements_test.txt": ["--extra", "test", "--no-emit-package", "pip"],
}


def normalize(name: str) -> str:
    """PEP 503 normalisation: lowercase and replace runs of -/_. with -."""
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_deps(entries: list[str]) -> dict[str, list[tuple[str, str]]]:
    """Return {dep_name: [(op, version), ...]} for a list of dep specifiers."""
    declared: dict[str, list[tuple[str, str]]] = {}
    for entry in entries:
        entry = MARKER_RE.sub("", entry).strip()
        match = CONSTRAINT_RE.match(entry)
        if not match:
            continue
        name = normalize(match.group(1).strip())
        spec = match.group(2).strip()
        constraints = declared.setdefault(name, [])
        if not spec:
            continue
        vm = VERSION_OP_RE.match(spec)
        if vm:
            constraints.append((vm.group(1) or "==", vm.group(2)))
    return declared


def parse_pyproject_deps() -> tuple[dict[str, list[tuple[str, str]]], dict[str, list[tuple[str, str]]]]:
    """Return (runtime_deps, test_deps) as {name: [(op, version), ...]}."""
    with (ROOT / "pyproject.toml").open("rb") as f:
        data = tomllib.load(f)
    project = data["project"]
    runtime = parse_deps(list(project.get("dependencies", [])))
    test = parse_deps(list(project.get("optional-dependencies", {}).get("test", [])))
    return runtime, test


def parse_lockfile(path: Path) -> dict[str, str]:
    """Return {dep_name: pinned_version} from a pip lockfile."""
    pins: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "-r", "--")):
            continue
        if line.startswith("-"):
            continue
        if "==" not in line:
            continue
        name, _, version = line.partition("==")
        name = normalize(name.strip())
        version = version.split("\\")[0].strip().split(";")[0].strip()
        pins[name] = version
    return pins


def version_tuple(v: str) -> tuple:
    nums = re.split(r"[^0-9]+", v)
    parts = []
    for n in nums:
        try:
            parts.append(int(n))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def satisfied(op: str | None, wanted: str, pinned: str) -> bool:
    """Check whether `pinned` satisfies `op wanted`."""
    if op is None or op == "==":
        return pinned == wanted
    if op == ">=":
        return version_tuple(pinned) >= version_tuple(wanted)
    if op == ">":
        return version_tuple(pinned) > version_tuple(wanted)
    if op == "<=":
        return version_tuple(pinned) <= version_tuple(wanted)
    if op == "<":
        return version_tuple(pinned) < version_tuple(wanted)
    if op == "!=":
        return pinned != wanted
    if op == "~=":
        return version_tuple(pinned)[:2] == version_tuple(wanted)[:2] and version_tuple(
            pinned
        ) >= version_tuple(wanted)
    if op == "===":
        return pinned == wanted
    return False


def check(declared: dict[str, list[tuple[str, str]]], pins: dict[str, str], label: str) -> list[str]:
    errors: list[str] = []
    for name, constraints in sorted(declared.items()):
        if name not in pins:
            errors.append(f"{label}: dependency '{name}' declared in pyproject.toml is missing from the lockfile")
            continue
        pinned = pins[name]
        for op, wanted in constraints:
            if not satisfied(op, wanted, pinned):
                errors.append(
                    f"{label}: pinned {name}=={pinned} does not satisfy '{name} {op} {wanted}' from pyproject.toml"
                )
    return errors


def uv_export(extra_args: list[str]) -> str:
    result = subprocess.run(  # noqa: S603
        UV_EXPORT + extra_args, cwd=ROOT, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise RuntimeError(f"`{' '.join(UV_EXPORT + extra_args)}` failed:\n{result.stderr.strip()}")
    return result.stdout


def parse_requirements(text: str) -> dict[str, tuple[str, str, set[str]]]:
    """Return {dep_name: (version, marker, hashes)} from hashed requirements text."""
    reqs: dict[str, tuple[str, str, set[str]]] = {}
    hashes: set[str] = set()
    for line in text.splitlines():
        if line[:1].isalnum():
            spec, _, marker = line.split("--hash=")[0].rstrip(" \\").partition(";")
            dep, _, version = spec.partition("==")
            hashes = set()
            reqs[normalize(dep.strip())] = (version.strip(), marker.strip(), hashes)
        hashes.update(tok.removeprefix("--hash=") for tok in line.split() if tok.startswith("--hash="))
    return reqs


def check_export(name: str, extra_args: list[str]) -> list[str]:
    expected = parse_requirements(uv_export(extra_args))
    actual = parse_requirements((ROOT / name).read_text())
    errors: list[str] = []
    for dep in sorted(expected.keys() | actual.keys()):
        if dep not in actual:
            errors.append(f"{name}: {dep} is in uv.lock but missing from the lockfile")
            continue
        if dep not in expected:
            errors.append(f"{name}: {dep} is in the lockfile but not in uv.lock")
            continue
        version, marker, hashes = actual[dep]
        want_version, want_marker, want_hashes = expected[dep]
        if version != want_version:
            errors.append(f"{name}: {dep} pinned {version}, uv.lock has {want_version}")
            continue
        if marker != want_marker:
            errors.append(f"{name}: {dep}=={version} marker {marker!r}, uv.lock has {want_marker!r}")
        if missing := want_hashes - hashes:
            errors.append(f"{name}: {dep}=={version} is missing {len(missing)} hash(es) from uv.lock")
        if extra := hashes - want_hashes:
            print(f"note: {name}: {dep}=={version} has {len(extra)} hash(es) not in uv.lock (allowed)", file=sys.stderr)
    return errors


def uv_lock(extra_args: list[str]) -> None:
    cmd = ["uv", "lock", *extra_args]
    result = subprocess.run(cmd, cwd=ROOT, check=False)  # noqa: S603
    if result.returncode != 0:
        raise RuntimeError(f"`{' '.join(cmd)}` failed")


def write_exports() -> int:
    for name, extra_args in EXPORTS.items():
        (ROOT / name).write_text(uv_export(extra_args))
        print(f"Wrote {name}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="regenerate the lockfiles from uv.lock")
    mode.add_argument("--lock", action="store_true", help="run `uv lock`, then --write")
    mode.add_argument(
        "--upgrade",
        nargs="*",
        metavar="PKG",
        help="run `uv lock --upgrade` (or --upgrade-package for each PKG), then --write; ignores Dependabot's cooldown",
    )
    args = parser.parse_args()

    have_uv = shutil.which("uv") is not None
    if args.write or args.lock or args.upgrade is not None:
        if not have_uv:
            print("error: uv is required for --write, --lock and --upgrade", file=sys.stderr)
            return 1
        try:
            if args.lock:
                uv_lock([])
            elif args.upgrade is not None:
                uv_lock([arg for pkg in args.upgrade for arg in ("--upgrade-package", pkg)] or ["--upgrade"])
            return write_exports()
        except RuntimeError as err:
            print(f"error: {err}", file=sys.stderr)
            return 1

    runtime, test = parse_pyproject_deps()
    errors: list[str] = []
    if have_uv:
        for name, extra_args in EXPORTS.items():
            try:
                errors.extend(check_export(name, extra_args))
            except RuntimeError as err:
                errors.append(str(err))
    elif os.environ.get("CI"):
        errors.append("uv is not installed; cannot compare the lockfiles against uv.lock")
    else:
        print("warning: uv is not installed; skipping comparison against uv.lock", file=sys.stderr)
    errors.extend(check(runtime, parse_lockfile(ROOT / "requirements.txt"), "requirements.txt"))
    errors.extend(check(test, parse_lockfile(ROOT / "requirements_test.txt"), "requirements_test.txt"))
    if errors:
        for err in errors:
            print(f"error: {err}", file=sys.stderr)
        print(
            "\nUpdate uv.lock (uv lock) and regenerate the lockfiles with "
            "`python scripts/check_dependencies_sync.py --write`.",
            file=sys.stderr,
        )
        return 1
    print("OK: lockfiles match uv.lock and satisfy pyproject.toml.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
