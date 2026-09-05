import json
from datetime import datetime

from app.events.stub_source import StubEventSource


def make_events_file(tmp_path, events):
    path = tmp_path / "events.json"
    path.write_text(json.dumps(events))
    return path


def test_stub_event_source_matches_overlapping_window(tmp_path):
    events_file = make_events_file(
        tmp_path,
        [
            {
                "name": "Summer Picnic",
                "description": "Annual picnic",
                "location": "Park",
                "start": "2024-07-04T11:00:00",
                "end": "2024-07-04T16:00:00",
            }
        ],
    )
    source = StubEventSource(events_file)
    result = source.find_event(
        datetime(2024, 7, 4, 12, 0), datetime(2024, 7, 4, 14, 0)
    )
    assert result is not None
    assert result.name == "Summer Picnic"


def test_stub_event_source_returns_none_when_no_overlap(tmp_path):
    events_file = make_events_file(
        tmp_path,
        [
            {
                "name": "Winter Gala",
                "start": "2024-12-01T18:00:00",
                "end": "2024-12-01T22:00:00",
            }
        ],
    )
    source = StubEventSource(events_file)
    result = source.find_event(
        datetime(2024, 7, 4, 12, 0), datetime(2024, 7, 4, 14, 0)
    )
    assert result is None


def test_stub_event_source_picks_best_overlap_among_several(tmp_path):
    events_file = make_events_file(
        tmp_path,
        [
            {
                "name": "Short overlap",
                "start": "2024-07-04T13:50:00",
                "end": "2024-07-04T14:10:00",
            },
            {
                "name": "Full overlap",
                "start": "2024-07-04T11:00:00",
                "end": "2024-07-04T16:00:00",
            },
        ],
    )
    source = StubEventSource(events_file)
    result = source.find_event(
        datetime(2024, 7, 4, 12, 0), datetime(2024, 7, 4, 14, 0)
    )
    assert result.name == "Full overlap"


def test_stub_event_source_handles_missing_file(tmp_path):
    source = StubEventSource(tmp_path / "does_not_exist.json")
    result = source.find_event(datetime(2024, 1, 1), datetime(2024, 1, 2))
    assert result is None


def test_stub_event_source_includes_organizations(tmp_path):
    events_file = make_events_file(
        tmp_path,
        [
            {
                "name": "Summer Picnic",
                "location": "Park",
                "organizations": ["Rotary Club", "City Parks"],
                "start": "2024-07-04T11:00:00",
                "end": "2024-07-04T16:00:00",
            }
        ],
    )
    source = StubEventSource(events_file)
    result = source.find_event(datetime(2024, 7, 4, 12, 0), datetime(2024, 7, 4, 14, 0))
    assert result.organizations == ["Rotary Club", "City Parks"]


def test_stub_event_source_defaults_organizations_to_empty_list(tmp_path):
    events_file = make_events_file(
        tmp_path,
        [
            {
                "name": "Summer Picnic",
                "start": "2024-07-04T11:00:00",
                "end": "2024-07-04T16:00:00",
            }
        ],
    )
    source = StubEventSource(events_file)
    result = source.find_event(datetime(2024, 7, 4, 12, 0), datetime(2024, 7, 4, 14, 0))
    assert result.organizations == []
