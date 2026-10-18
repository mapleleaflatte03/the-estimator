"""Persistence failures must not create fictitious successful projects or learning."""
import json

import pytest

from parallax.schemas import ActualWork, CalibrationState, Project
from parallax.storage import StorageError, StorageRepository


def test_failed_initial_write_rolls_back_in_memory(tmp_path):
    # A regular file cannot be used as the parent directory of the store.
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")
    repo = StorageRepository(blocker / "store.json")
    with pytest.raises(StorageError, match="could not be saved"):
        repo.save_project(Project(project_id="P1", title="Trial", brief_text="Build a portal"))
    assert repo.list_projects() == []


def test_failed_update_restores_last_durable_state(tmp_path, monkeypatch):
    path = tmp_path / "store.json"
    repo = StorageRepository(path)
    repo.save_project(Project(project_id="P1", title="Original", brief_text="Build a portal"))
    original = json.loads(path.read_text(encoding="utf-8"))

    def fail_replace(_source, _target):
        raise OSError("disk full")

    from pathlib import Path
    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(StorageError):
        repo.save_project(Project(project_id="P2", title="Unsaved", brief_text="Build a report"))
    assert [p.project_id for p in repo.list_projects()] == ["P1"]
    assert json.loads(path.read_text(encoding="utf-8")) == original


def test_corrupt_store_is_not_replaced_with_empty_state(tmp_path):
    path = tmp_path / "store.json"
    path.write_text('{"projects": [', encoding="utf-8")
    with pytest.raises(StorageError, match="could not be loaded"):
        StorageRepository(path)
    assert path.read_text(encoding="utf-8") == '{"projects": ['


def test_failed_outcome_commit_keeps_actuals_and_calibration_together(tmp_path, monkeypatch):
    path = tmp_path / "store.json"
    repo = StorageRepository(path)
    repo.save_project(Project(project_id="P1", title="Trial", brief_text="Build a portal"))

    def fail_replace(_source, _target):
        raise OSError("disk full")

    from pathlib import Path
    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(StorageError):
        repo.commit_actuals(
            ActualWork(actual_id="A1", project_id="P1", version_id="v1", actual_hours=40),
            [], CalibrationState(multiplier=1.5),
        )
    assert repo.get_actuals("P1") == []
    assert repo.get_calibration().multiplier == 1.0
    assert repo.get_project("P1").status == "intake"
