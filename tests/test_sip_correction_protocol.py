"""Locks for the SiP correction protocol. These tests do not score 2010 or 2011-2014."""
import argparse
import importlib.util
import json
import math
from datetime import date
from pathlib import Path

import numpy as np
import pytest

from parallax.empirical import SIZE_BUCKET_EDGES, SipTask

ROOT = Path(__file__).resolve().parents[1]
ROUND = {0.5, 1, 2, 3, 4, 5, 6, 7, 7.5, 8, 10, 12, 14, 15, 16, 20, 21, 24, 28, 30, 35, 40, 50, 60, 70, 80, 100}
CANDIDATES = [
    "recent-2006", "recent-2007", "recent-2008",
    "shrink-k30", "shrink-k100", "round-by-bucket",
    "edges-pow2", "edges-coarse",
]


def load_mod():
    path = ROOT / "scripts" / "sip_correction_search.py"
    spec = importlib.util.spec_from_file_location("sip_correction_search", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def task(tid, when, est, act):
    return SipTask(tid, "summary", "Development", "sub", "P", "B", est, act, when)


def test_protocol_file_is_locked():
    mod = load_mod()
    protocol = mod.load_protocol()
    mod.require_protocol(protocol)
    assert [c["id"] for c in protocol["candidates"]] == CANDIDATES
    assert set(protocol["round_hours"]) == ROUND
    assert protocol["shipped_edges"] == list(SIZE_BUCKET_EDGES)
    assert protocol["no_jev"] is True
    assert protocol["integrity_check"]["n_validation"] == 557
    assert protocol["integrity_check"]["size_only_mae_rounded_3dp"] == 8.189
    assert protocol["integrity_check"]["human_mae_rounded_3dp"] == 8.738


def test_decide_promotion_gates_and_ties():
    mod = load_mod()
    assert mod.decide_promotion([
        {"id": "a", "mae": 1.0, "coverage_p10_p90": 74.9, "ci_low": 1.0},
        {"id": "b", "mae": 1.2, "coverage_p10_p90": 80.0, "ci_low": 0.1},
    ], 2.0, 75) == "b"
    assert mod.decide_promotion([
        {"id": "a", "mae": 1.0, "coverage_p10_p90": 80.0, "ci_low": 0.0},
    ], 2.0, 75) is None
    assert mod.decide_promotion([
        {"id": "a", "mae": 2.0, "coverage_p10_p90": 80.0, "ci_low": 0.1},
    ], 2.0, 75) is None
    assert mod.decide_promotion([
        {"id": "a", "mae": 1.0, "coverage_p10_p90": 80.0, "ci_low": 0.1},
        {"id": "b", "mae": 1.0, "coverage_p10_p90": 90.0, "ci_low": 0.4},
    ], 2.0, 75) == "a"
    assert mod.decide_promotion([
        {"id": "a", "mae": 1.5, "coverage_p10_p90": 80.0, "ci_low": 0.2},
        {"id": "b", "mae": 1.0, "coverage_p10_p90": 80.0, "ci_low": 0.1},
    ], 2.0, 75) == "b"


def test_integrity_check_uses_rounded_published_baselines():
    mod = load_mod()
    protocol = mod.load_protocol()
    good = {"size_only": {"n": 557, "mae": 8.1894}, "human": {"mae": 8.7376}}
    bad = {"size_only": {"n": 557, "mae": 8.189}, "human": {"mae": 9.0}}
    assert mod.integrity_ok(good, protocol)
    assert not mod.integrity_ok(bad, protocol)


def test_shrink_blend_matches_the_frozen_formula():
    mod = load_mod()
    train = [task("p0", date(2009, 1, 1), 2, 2) for _ in range(3)]
    train.append(task("p3", date(2009, 1, 1), 10, 20))
    predict = mod.fit_shrink(train, k=30, edges=[4, 8, 20, 50], min_cases=1)
    got = predict(task("q", date(2010, 6, 1), 10, 1))
    assert math.isclose(got[1], 10 * (1 * 2 + 30 * 1) / 31)
    qp90 = float(np.quantile(np.array([1.0, 1.0, 1.0, 2.0]), 0.9))
    assert math.isclose(got[2], 10 * (1 * 2 + 30 * qp90) / 31)
    assert got[0] <= got[1] <= got[2]


def test_shipped_edges_match_size_only():
    mod = load_mod()
    protocol = mod.load_protocol()
    train = [task(f"s{i}", date(2009, 1, 1), 10, 15) for i in range(40)]
    train += [task(f"a{i}", date(2009, 1, 1), 3, 3) for i in range(40)]
    train += [task(f"b{i}", date(2009, 1, 1), 100, 50) for i in range(5)]
    pred = mod.fit_predictor({"id": "x", "kind": "size-buckets", "edges": [4.0, 8.0, 20.0, 50.0]}, train, protocol)
    base = mod.size_only_predictor(train)
    for estimate in (3, 10, 100):
        probe = task("p", date(2010, 6, 1), estimate, 1)
        assert np.allclose(pred(probe), base(probe))


def test_round_split_uses_the_subset_when_it_is_large_enough():
    mod = load_mod()
    protocol = mod.load_protocol()
    train = [task(f"r{i}", date(2009, 1, 1), 10, 20) for i in range(30)]
    train += [task(f"o{i}", date(2009, 1, 1), 9, 9) for i in range(30)]
    pred = mod.fit_predictor({"id": "round-by-bucket", "kind": "round-by-bucket"}, train, protocol)
    round_probe = task("pr", date(2010, 6, 1), 10, 1)
    odd_probe = task("po", date(2010, 6, 1), 9, 1)
    assert math.isclose(pred(round_probe)[1], 20)
    assert math.isclose(pred(odd_probe)[1], 9)


def test_recent_window_drops_older_rows_and_keeps_a_full_window():
    mod = load_mod()
    protocol = mod.load_protocol()
    old = [task(f"o{i}", date(2005, 6, 1), 10, 10) for i in range(40)]
    new = [task(f"n{i}", date(2008, 6, 1), 10, 20) for i in range(40)]
    spec = {"id": "recent-2006", "kind": "recent-window", "start": "2006-01-01"}
    pred = mod.fit_predictor(spec, old + new, protocol)
    probe = task("p", date(2010, 6, 1), 10, 1)
    assert math.isclose(pred(probe)[1], 20)
    base = mod.size_only_predictor(old + new)
    assert not math.isclose(base(probe)[1], pred(probe)[1])
    same = mod.fit_predictor(spec, new, protocol)
    assert np.allclose(same(probe), mod.size_only_predictor(new)(probe))


def test_split_for_select_never_returns_the_holdout():
    mod = load_mod()
    tasks = [
        task("a", date(2009, 6, 1), 10, 10),
        task("b", date(2010, 6, 1), 10, 10),
        task("c", date(2011, 6, 1), 10, 10),
    ]
    train, val = mod.split_for_select(tasks)
    assert [t.task_id for t in train] == ["a"]
    assert [t.task_id for t in val] == ["b"]
    holdout_train, holdout = mod.split_for_test(tasks)
    assert [t.task_id for t in holdout_train] == ["a", "b"]
    assert [t.task_id for t in holdout] == ["c"]


def test_published_2010_baseline_is_reproduced_without_scoring_candidates():
    mod = load_mod()
    protocol = mod.load_protocol()
    train, val = mod.split_for_select(mod.load_sip_tasks())
    assert val and all(t.estimated_on < mod.HOLDOUT_CUTOFF for t in train + val)
    human, _ = mod.score_tasks(val, None, human=True)
    size, _ = mod.score_tasks(val, mod.size_only_predictor(train))
    assert mod.integrity_ok({"human": human, "size_only": size}, protocol)


def test_untracked_path_is_not_a_committed_protocol():
    mod = load_mod()
    assert not mod.committed_and_clean(ROOT / "datasets" / "eval" / "not-a-protocol.json")


def test_test_command_does_not_load_the_holdout_when_nothing_was_promoted(tmp_path, monkeypatch):
    mod = load_mod()
    choice = {
        "protocol": "sip_correction_protocol_v1",
        "protocol_sha256": mod.protocol_sha256(),
        "promoted": None,
    }
    path = tmp_path / "choice.json"
    path.write_text(json.dumps(choice), encoding="utf-8")

    def boom(*_args, **_kwargs):
        raise AssertionError("load_sip_tasks was called")

    monkeypatch.setattr(mod, "load_sip_tasks", boom)
    ns = argparse.Namespace(
        choice=path,
        result=tmp_path / "result.json",
        journal=tmp_path / "journal.jsonl",
        no_journal=True,
    )
    assert mod.cmd_test(ns) == 2
    assert not ns.result.exists()


def test_require_protocol_rejects_an_extra_candidate():
    mod = load_mod()
    protocol = mod.load_protocol()
    protocol["candidates"] = list(protocol["candidates"]) + [{"id": "assignee", "kind": "hierarchical"}]
    with pytest.raises(SystemExit):
        mod.require_protocol(protocol)
