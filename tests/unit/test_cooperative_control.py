"""Tests for cooperative pause/cancel control in model loops."""

import inspect
import threading

import pytest

from uvr.models import demucs as demucs_mod
from uvr.models import mdx as mdx_mod
from uvr.models import mdxc as mdxc_mod
from uvr.models import vr as vr_mod
from uvr.models.base import ControlCancelled, check_control


def test_cancel_event_aborts():
    ev = threading.Event()
    ev.set()
    with pytest.raises(ControlCancelled):
        check_control(None, ev)


def test_no_events_is_noop():
    assert check_control(None, None) is None


def test_pause_blocks_until_cleared():
    pause = threading.Event()
    pause.set()
    done = threading.Event()

    def runner():
        check_control(pause, None)
        done.set()

    thread = threading.Thread(target=runner)
    thread.start()
    assert done.wait(timeout=0.5) is False
    pause.clear()
    assert done.wait(timeout=2.0) is True
    thread.join()


def test_cancel_wins_over_pause():
    pause = threading.Event()
    cancel = threading.Event()
    pause.set()
    cancel.set()
    with pytest.raises(ControlCancelled):
        check_control(pause, cancel)


def test_all_model_loops_check_control():
    for mod in (vr_mod, mdx_mod, demucs_mod, mdxc_mod):
        assert "check_control(" in inspect.getsource(mod), mod.__name__
