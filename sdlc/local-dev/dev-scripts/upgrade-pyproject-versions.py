import argparse
import glob
import http.client
import json
import logging
import os
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from urllib import error, parse

logger = logging.getLogger(__name__)

try:
    from packaging.version import InvalidVersion, Version
except ImportError:  # pragma: no cover - exercised only when packaging is unavailable.
    InvalidVersion = None
    Version = None


SIMPLE_VERSION_SPEC_PATTERN = re.compile(
    r"^(?P<operator>\^|~=|~|===|==|>=|<=|>|<|=)?(?P<version>[A-Za-z0-9.!+_-]+)$"
)
PEP508_DEP_PATTERN = re.compile(
    r"^(?P<name>[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?)"
    r"(?P<extras>\[[^\]]*\])?"
    r"(?P<spec>[^;@]*)?"
)
UNSUPPORTED_SPEC_TOKENS = (",", ";", " ", "@", "*")
SKIPPED_DEPENDENCY_NAMES = {"python"}
PYPI_TIMEOUT_SECONDS = 10.0
PYPI_HOST = "pypi.org"


@dataclass(frozen=True)
class DependencyUpdate:
    pyproject_path: str
    section_name: str
    dependency_name: str
    old_spec: str  # full PEP 508 string, e.g. "pydantic>=2.12.5"
    new_spec: str  # updated PEP 508 string, e.g. "pydantic>=3.0.0"


def find_pyproject_files(project_dir: str) -> list[str]:
    """Find all pyproject.toml files sorted by nesting level (shallowest first)."""
    toml_files = glob.glob(
        os.path.join(project_dir, "**", "pyproject.toml"), recursive=True
    )
    return sorted(toml_files, key=lambda file_path: file_path.count(os.sep))


def iter_uv_dependency_sections(parsed_toml: dict) -> list[tuple[str, list]]:
    """Return uv/PEP 508 dependency sections as (section_name, dep_list) pairs.

    Reads [project].dependencies and all groups under [dependency-groups].
    """
    sections: list[tuple[str, list]] = []

    project = parsed_toml.get("project", {})
    deps = project.get("dependencies")
    if isinstance(deps, list):
        sections.append(("project.dependencies", deps))

    dep_groups = parsed_toml.get("dependency-groups", {})
    if isinstance(dep_groups, dict):
        for group_name, group_deps in dep_groups.items():
            if isinstance(group_deps, list):
                sections.append((f"dependency-groups.{group_name}", group_deps))

    return sections


def normalize_distribution_name(package_name: str) -> str:
    """Normalize a package name for PyPI lookups."""
    return re.sub(r"[-_.]+", "-", package_name).lower()


def parse_pep508_dep(dep_string: str) -> tuple[str, str, str] | None:
    """Parse a PEP 508 dependency string into (name, extras, version_spec).

    Returns None if the string cannot be parsed.
    Examples:
        "pydantic>=2.12.5"        -> ("pydantic", "", ">=2.12.5")
        "pymongo[srv]>=4.16.0"    -> ("pymongo", "[srv]", ">=4.16.0")
        "new-python-app-core"     -> ("new-python-app-core", "", "")
    """
    match = PEP508_DEP_PATTERN.match(dep_string.strip())
    if not match:
        return None
    name = match.group("name")
    extras = match.group("extras") or ""
    spec = (match.group("spec") or "").strip()
    return name, extras, spec


def parse_version_spec(spec: str) -> tuple[str, str] | None:
    """Parse a simple version specifier while preserving its operator.

    Examples of supported specs include "^1.2.3", "~=2.0", "==3.1.4", and "4.5.6".
    Complex constraints like ">=1,<2" are skipped because they cannot be safely
    rewritten without changing semantics.
    """
    stripped_spec = spec.strip()
    if not stripped_spec:
        return None

    if any(token in stripped_spec for token in UNSUPPORTED_SPEC_TOKENS):
        return None

    match = SIMPLE_VERSION_SPEC_PATTERN.fullmatch(stripped_spec)
    if not match:
        return None

    return match.group("operator") or "", match.group("version")


def is_stable_release(version_string: str) -> bool:
    """Return True when a version string represents a stable release."""
    if Version is not None:
        try:
            parsed_version = Version(version_string)
        except InvalidVersion:
            return False

        return not parsed_version.is_prerelease and not parsed_version.is_devrelease

    normalized_version = version_string.lstrip("vV")
    return (
        re.search(
            r"(?:a|b|rc|alpha|beta|pre|preview|dev)\d*",
            normalized_version,
            re.IGNORECASE,
        )
        is None
    )


def version_sort_key(version_string: str) -> Version | tuple[tuple[int, ...], int]:
    """Build a best-effort sorting key for release versions."""
    if Version is not None:
        return Version(version_string)

    normalized_version = version_string.lstrip("vV")
    version_without_local = normalized_version.split("+", maxsplit=1)[0]
    main_version, _, post_release = version_without_local.partition(".post")
    parts = tuple(int(part) for part in re.findall(r"\d+", main_version))
    post_number = int(post_release) if post_release.isdigit() else -1
    return parts, post_number


def select_latest_release(
    release_versions: list[str], include_prereleases: bool = False
) -> str | None:
    """Select the latest release version from a list of release strings."""
    eligible_versions = [
        version
        for version in release_versions
        if include_prereleases or is_stable_release(version)
    ]
    if not eligible_versions:
        return None

    return max(eligible_versions, key=version_sort_key)


def fetch_pypi_package_metadata(
    normalized_name: str, timeout_seconds: float = PYPI_TIMEOUT_SECONDS
) -> dict:
    """Fetch package metadata from PyPI using an explicit HTTPS connection."""
    connection = http.client.HTTPSConnection(PYPI_HOST, timeout=timeout_seconds)
    request_path = f"/pypi/{parse.quote(normalized_name)}/json"

    try:
        connection.request("GET", request_path)
        response = connection.getresponse()
        if response.status != http.client.OK:
            raise error.HTTPError(
                url=f"https://{PYPI_HOST}{request_path}",
                code=response.status,
                msg=response.reason,
                hdrs=response.headers,
                fp=None,
            )

        return json.loads(response.read().decode("utf-8"))
    finally:
        connection.close()


def fetch_latest_stable_version(
    package_name: str,
    version_cache: dict[str, str | None],
    include_prereleases: bool = False,
    timeout_seconds: float = PYPI_TIMEOUT_SECONDS,
) -> str | None:
    """Fetch the latest stable package version from PyPI, using a cache per package."""
    normalized_name = normalize_distribution_name(package_name)
    if normalized_name in version_cache:
        return version_cache[normalized_name]

    try:
        payload = fetch_pypi_package_metadata(normalized_name, timeout_seconds)
    except (
        error.HTTPError,
        error.URLError,
        http.client.HTTPException,
        OSError,
        TimeoutError,
        json.JSONDecodeError,
    ) as exc:
        logger.error("Failed to fetch package metadata for %s: %s", package_name, exc)
        version_cache[normalized_name] = None
        return None

    release_versions = [
        release_version
        for release_version, files in payload.get("releases", {}).items()
        if files and not all(file_entry.get("yanked", False) for file_entry in files)
    ]

    latest_version = select_latest_release(
        release_versions, include_prereleases=include_prereleases
    )

    if latest_version is None:
        fallback_version = payload.get("info", {}).get("version")
        if fallback_version and (
            include_prereleases or is_stable_release(fallback_version)
        ):
            latest_version = fallback_version

    version_cache[normalized_name] = latest_version
    return latest_version


def collect_dependency_updates(
    pyproject_path: str,
    version_cache: dict[str, str | None],
    include_prereleases: bool = False,
    timeout_seconds: float = PYPI_TIMEOUT_SECONDS,
) -> list[DependencyUpdate]:
    """Collect dependency updates needed for a specific pyproject.toml file."""
    pyproject_text = Path(pyproject_path).read_text(encoding="utf-8")
    parsed_toml = tomllib.loads(pyproject_text)

    updates: list[DependencyUpdate] = []

    for section_name, dep_list in iter_uv_dependency_sections(parsed_toml):
        for dep_item in dep_list:
            if not isinstance(dep_item, str):
                continue  # skip {include-group = "..."} and other non-string entries

            parsed = parse_pep508_dep(dep_item)
            if parsed is None:
                continue

            name, extras, current_spec = parsed

            if name.lower() in SKIPPED_DEPENDENCY_NAMES:
                continue

            if not current_spec:
                continue  # workspace reference or bare package name — no version to update

            parsed_spec = parse_version_spec(current_spec)
            if parsed_spec is None:
                continue

            operator, current_version = parsed_spec
            latest_version = fetch_latest_stable_version(
                name,
                version_cache,
                include_prereleases=include_prereleases,
                timeout_seconds=timeout_seconds,
            )
            if latest_version is None or latest_version == current_version:
                continue

            new_spec = f"{operator}{latest_version}"
            new_dep_string = f"{name}{extras}{new_spec}"

            updates.append(
                DependencyUpdate(
                    pyproject_path=pyproject_path,
                    section_name=section_name,
                    dependency_name=name,
                    old_spec=dep_item.strip(),
                    new_spec=new_dep_string,
                )
            )

    return updates


def apply_updates_to_pyproject_text(
    pyproject_text: str, updates: list[DependencyUpdate]
) -> str:
    """Apply dependency updates by replacing quoted PEP 508 strings in place."""
    for update in updates:
        pyproject_text = pyproject_text.replace(
            f'"{update.old_spec}"', f'"{update.new_spec}"'
        ).replace(f"'{update.old_spec}'", f"'{update.new_spec}'")
    return pyproject_text


def update_pyproject_file(
    pyproject_path: str,
    version_cache: dict[str, str | None],
    include_prereleases: bool = False,
    dry_run: bool = False,
    timeout_seconds: float = PYPI_TIMEOUT_SECONDS,
) -> list[DependencyUpdate]:
    """Update a pyproject.toml file in place and return applied updates."""
    pyproject_text = Path(pyproject_path).read_text(encoding="utf-8")
    updates = collect_dependency_updates(
        pyproject_path,
        version_cache,
        include_prereleases=include_prereleases,
        timeout_seconds=timeout_seconds,
    )
    if not updates:
        return []

    updated_text = apply_updates_to_pyproject_text(pyproject_text, updates)
    if not dry_run and updated_text != pyproject_text:
        Path(pyproject_path).write_text(updated_text, encoding="utf-8")

    return updates


def update_project_pyprojects(
    project_dir: str,
    include_prereleases: bool = False,
    dry_run: bool = False,
    timeout_seconds: float = PYPI_TIMEOUT_SECONDS,
) -> list[DependencyUpdate]:
    """Update every nested pyproject.toml file under the given project directory."""
    version_cache: dict[str, str | None] = {}
    all_updates: list[DependencyUpdate] = []

    pyproject_files = find_pyproject_files(project_dir)
    if not pyproject_files:
        logger.info("No pyproject.toml files found in %s.", project_dir)
        return all_updates

    for pyproject_path in pyproject_files:
        logger.info("Checking dependency versions in %s...", pyproject_path)
        file_updates = update_pyproject_file(
            pyproject_path,
            version_cache,
            include_prereleases=include_prereleases,
            dry_run=dry_run,
            timeout_seconds=timeout_seconds,
        )

        if not file_updates:
            logger.info("  No updates needed.")
            continue

        action = "Would update" if dry_run else "Updated"
        for update in file_updates:
            logger.info(
                "  %s %s: %s -> %s",
                action,
                update.dependency_name,
                update.old_spec,
                update.new_spec,
            )
        all_updates.extend(file_updates)

    return all_updates


def build_argument_parser() -> argparse.ArgumentParser:
    """Create the command-line parser for the update script."""
    parser = argparse.ArgumentParser(
        description=(
            "Recursively find pyproject.toml files, fetch the latest stable package "
            "versions from PyPI, and update uv/PEP 508 dependency version specs in "
            "place without changing the existing operator (for example >= or ~=)."
        )
    )
    parser.add_argument(
        "project_dir",
        type=str,
        help="Path to the root directory containing pyproject.toml files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report changes without writing them back to disk.",
    )
    parser.add_argument(
        "--include-prereleases",
        action="store_true",
        help="Allow prerelease versions when no stable release filtering is desired.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=PYPI_TIMEOUT_SECONDS,
        help="HTTP timeout for each PyPI request. Defaults to 10 seconds.",
    )
    return parser


def main() -> int:
    """Run the command-line interface."""
    args = build_argument_parser().parse_args()
    all_updates = update_project_pyprojects(
        args.project_dir,
        include_prereleases=args.include_prereleases,
        dry_run=args.dry_run,
        timeout_seconds=args.timeout_seconds,
    )

    if not all_updates:
        logger.info("No dependency updates were applied.")
        return 0

    if args.dry_run:
        logger.info("Dry run complete. %d update(s) found.", len(all_updates))
    else:
        logger.info("Finished. Applied %d update(s).", len(all_updates))
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    raise SystemExit(main())
