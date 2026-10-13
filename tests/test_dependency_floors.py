from __future__ import annotations

from pathlib import Path
import re
import tomllib

from packaging.requirements import Requirement
from packaging.version import Version

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Response serialization passes ``fallback=`` to ``TypeAdapter.dump_python``,
# which Pydantic accepts from 2.11.0.
PYDANTIC_SERIALIZER_FLOOR = Version("2.11.0")


def _declared_pydantic_floor() -> Version:
    project = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]
    requirement = next(
        Requirement(dependency)
        for dependency in project["dependencies"]
        if Requirement(dependency).name == "pydantic"
    )
    return Version(next(spec.version for spec in requirement.specifier if spec.operator == ">="))


def test_declared_pydantic_floor_supports_serializer_fallback() -> None:
    # Given the Pydantic lower bound declared in the package metadata
    declared = _declared_pydantic_floor()

    # Then no installable Pydantic release lacks serializer ``fallback``
    assert declared >= PYDANTIC_SERIALIZER_FLOOR


def test_minimum_dependencies_job_installs_declared_pydantic_floor() -> None:
    # Given the CI workflow that runs the suite against the declared floors
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "ci-test.yml").read_text(encoding="utf-8")

    # When the pinned Pydantic installs are collected
    pins = [Version(pin) for pin in re.findall(r'"pydantic==([^"]+)"', workflow)]

    # Then the job installs exactly the declared Pydantic floor
    assert pins == [_declared_pydantic_floor()]
