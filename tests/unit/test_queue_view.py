"""Tests for queue view selection -> service wiring."""

from flet_gui.pages.queue import (
    on_pause_selected,
    on_play_selected,
    on_stop_all,
    on_stop_selected,
    selected_ids,
)


class FakeService:
    def __init__(self):
        self.paused = []
        self.resumed = []
        self.cancelled = []
        self.cancelled_all = 0

    def pause(self, ids):
        self.paused.extend(ids)

    def resume(self, ids):
        self.resumed.extend(ids)

    def cancel(self, ids):
        self.cancelled.extend(ids)

    def cancel_all(self):
        self.cancelled_all += 1


class FakeCheckbox:
    def __init__(self, job_id, value):
        self.data = job_id
        self.value = value


def test_stop_selected_calls_cancel_with_ids():
    fake = FakeService()
    on_stop_selected(fake, [2, 3])
    assert fake.cancelled == [2, 3]


def test_play_selected_calls_resume_with_ids():
    fake = FakeService()
    on_play_selected(fake, [1])
    assert fake.resumed == [1]


def test_pause_selected_calls_pause_with_ids():
    fake = FakeService()
    on_pause_selected(fake, [4, 5])
    assert fake.paused == [4, 5]


def test_stop_all_calls_cancel_all():
    fake = FakeService()
    on_stop_all(fake)
    assert fake.cancelled_all == 1


def test_selected_ids_reads_checked_boxes():
    boxes = [FakeCheckbox(1, True), FakeCheckbox(2, False), FakeCheckbox(3, True)]
    assert selected_ids(boxes) == [1, 3]
