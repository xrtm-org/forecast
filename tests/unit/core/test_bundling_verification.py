from xrtm.forecast.core.bundling import ManifestBundler
from xrtm.forecast.core.schemas.graph import BaseGraphState
from xrtm.forecast.core.verification import SovereigntyVerifier


def _hashed_state() -> BaseGraphState:
    state = BaseGraphState(
        subject_id="subject-1",
        node_reports={"analysis": {"score": 0.72}},
        execution_trace=["research", "analysis"],
        cycle_count=2,
        context={"source": "unit-test"},
    )
    state.state_hash = state.compute_hash()
    return state


def test_manifest_bundle_emits_execution_trace_and_compat_alias() -> None:
    manifest = ManifestBundler.bundle(_hashed_state())

    assert manifest["execution_trace"] == ["research", "analysis"]
    assert manifest["execution_path"] == ["research", "analysis"]


def test_verifier_accepts_execution_trace_without_execution_path() -> None:
    manifest = ManifestBundler.bundle(_hashed_state())
    manifest.pop("execution_path")

    success, errors = SovereigntyVerifier.verify_manifest(manifest)

    assert success is True
    assert errors == []
