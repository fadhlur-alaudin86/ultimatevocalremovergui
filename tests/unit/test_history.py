import csv

from uvr.core.history import HistoryManager


def test_history_manager_lifecycle(tmp_path):
    history_file = tmp_path / "test_history.json"
    manager = HistoryManager(str(history_file))

    assert len(manager.get_records()) == 0

    record = manager.add_entry(
        task_id=1,
        process_method="VR Arch",
        model_name="5_HP-Karaoke-UVR",
        input_files=["song.mp3"],
        export_path="/exports",
        duration_seconds=12.5,
        status="Completed",
    )
    assert record["task_id"] == 1
    assert len(manager.get_records()) == 1

    # Test CSV export
    csv_file = tmp_path / "export.csv"
    assert manager.export_csv(str(csv_file)) is True
    assert csv_file.exists()

    with open(csv_file, encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 1
        assert reader[0]["model_name"] == "5_HP-Karaoke-UVR"
        assert reader[0]["status"] == "Completed"

    # Test clear
    manager.clear()
    assert len(manager.get_records()) == 0
