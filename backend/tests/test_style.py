from app.posting.style import CaptionStyle


def test_save_and_load_round_trip(tmp_path):
    path = tmp_path / "style.json"
    style = CaptionStyle(tone_notes="Casual and warm.", example_captions=["One", "Two"])
    style.save(path)

    loaded = CaptionStyle.load(path)
    assert loaded.tone_notes == "Casual and warm."
    assert loaded.example_captions == ["One", "Two"]


def test_load_missing_file_returns_defaults(tmp_path):
    style = CaptionStyle.load(tmp_path / "does_not_exist.json")
    assert style.tone_notes == ""
    assert style.example_captions == []
