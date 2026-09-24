from uvr.utils.notifications import send_notification


def test_send_notification_executes_safely():
    # Should not raise any unhandled exceptions
    result = send_notification("UVR Test", "Test notification content")
    assert isinstance(result, bool)
