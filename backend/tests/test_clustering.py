from datetime import date, datetime

from app.ingest.clustering import (
    TimestampedPhoto,
    choose_primary_burst,
    find_event_day,
    group_by_date,
    split_into_bursts,
)


def tp(path: str, iso: str) -> TimestampedPhoto:
    return TimestampedPhoto(path=path, captured_at=datetime.fromisoformat(iso))


def test_group_by_date_buckets_by_calendar_day():
    photos = [
        tp("a.jpg", "2024-07-04T10:00:00"),
        tp("b.jpg", "2024-07-04T11:00:00"),
        tp("c.jpg", "2024-07-05T09:00:00"),
    ]
    groups = group_by_date(photos)
    assert set(groups.keys()) == {date(2024, 7, 4), date(2024, 7, 5)}
    assert len(groups[date(2024, 7, 4)]) == 2


def test_find_event_day_walks_backward_when_today_is_empty():
    photos = [tp("a.jpg", "2024-07-01T10:00:00")]
    result = find_event_day(photos, start_date=date(2024, 7, 5), max_lookback_days=10)
    assert result is not None
    day, day_photos = result
    assert day == date(2024, 7, 1)
    assert len(day_photos) == 1


def test_find_event_day_respects_min_photos_threshold():
    photos = [
        tp("a.jpg", "2024-07-04T10:00:00"),  # only 1 photo this day
        tp("b.jpg", "2024-07-01T10:00:00"),
        tp("c.jpg", "2024-07-01T10:05:00"),
        tp("d.jpg", "2024-07-01T10:10:00"),
    ]
    result = find_event_day(
        photos, start_date=date(2024, 7, 4), min_photos=3, max_lookback_days=10
    )
    assert result is not None
    day, day_photos = result
    assert day == date(2024, 7, 1)
    assert len(day_photos) == 3


def test_find_event_day_returns_none_when_nothing_found():
    assert find_event_day([], max_lookback_days=5) is None


def test_split_into_bursts_separates_by_time_gap():
    photos = [
        tp("a.jpg", "2024-07-04T09:00:00"),
        tp("b.jpg", "2024-07-04T09:05:00"),
        tp("c.jpg", "2024-07-04T15:00:00"),  # big gap -> new burst
        tp("d.jpg", "2024-07-04T15:02:00"),
    ]
    bursts = split_into_bursts(photos, gap_minutes=30)
    assert len(bursts) == 2
    assert len(bursts[0]) == 2
    assert len(bursts[1]) == 2


def test_choose_primary_burst_picks_the_largest():
    bursts = [[tp("a.jpg", "2024-07-04T09:00:00")], [
        tp("b.jpg", "2024-07-04T15:00:00"),
        tp("c.jpg", "2024-07-04T15:02:00"),
    ]]
    primary = choose_primary_burst(bursts)
    assert len(primary) == 2


def test_choose_primary_burst_handles_empty_input():
    assert choose_primary_burst([]) == []
