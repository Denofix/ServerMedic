import tomllib
from pathlib import Path


def test_both_vercel_dependency_detectors_use_the_same_pinned_backend_packages():
    root = Path(__file__).resolve().parents[2]
    requirements = root.joinpath("backend/requirements.txt").read_text()
    pins = [
        line.strip()
        for line in requirements.splitlines()
        if line and not line[0].isspace() and not line.startswith("#")
    ]
    project = tomllib.loads(root.joinpath("backend/pyproject.toml").read_text())
    assert project["project"]["dependencies"] == pins
    assert root.joinpath("requirements.txt").read_text() == requirements
