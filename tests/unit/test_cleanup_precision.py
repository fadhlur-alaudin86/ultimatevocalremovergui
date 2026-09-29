"""Tests for precise partial-file cleanup (no collateral deletion)."""

from uvr.core.service import InferenceService


def test_cleanup_keeps_unrelated_same_prefix_files(tmp_path):
    (tmp_path / "out_(Vocals).wav").touch()
    (tmp_path / "out_final.wav").touch()
    svc = InferenceService(run_fn=lambda spec, pause, cancel: None, autostart=False)
    try:
        svc._cleanup_partials(str(tmp_path), "out")
        assert not (tmp_path / "out_(Vocals).wav").exists()
        assert (tmp_path / "out_final.wav").exists()
    finally:
        svc.stop()
