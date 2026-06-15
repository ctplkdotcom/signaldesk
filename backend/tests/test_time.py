from datetime import datetime
import pytz

from app.utils.time import classify_session, SessionType, to_utc, to_et, is_market_open, get_market_hours_description

ET = pytz.timezone("US/Eastern")


def test_premarket():
    dt = ET.localize(datetime(2024, 1, 3, 6, 0))
    assert classify_session(dt) == SessionType.PREMARKET


def test_regular():
    dt = ET.localize(datetime(2024, 1, 3, 10, 0))
    assert classify_session(dt) == SessionType.REGULAR


def test_afterhours():
    dt = ET.localize(datetime(2024, 1, 3, 17, 0))
    assert classify_session(dt) == SessionType.AFTERHOURS


def test_closed():
    dt = ET.localize(datetime(2024, 1, 3, 3, 0))
    assert classify_session(dt) == SessionType.CLOSED


def test_premarket_boundary():
    dt = ET.localize(datetime(2024, 1, 3, 4, 0))
    assert classify_session(dt) == SessionType.PREMARKET


def test_regular_start_boundary():
    dt = ET.localize(datetime(2024, 1, 3, 9, 30))
    assert classify_session(dt) == SessionType.REGULAR


def test_regular_end_boundary():
    dt = ET.localize(datetime(2024, 1, 3, 16, 0))
    assert classify_session(dt) == SessionType.REGULAR


def test_weekend():
    dt = ET.localize(datetime(2024, 1, 6, 12, 0))
    assert classify_session(dt) == SessionType.CLOSED


def test_to_utc():
    dt = ET.localize(datetime(2024, 1, 3, 9, 30))
    utc = to_utc(dt)
    assert utc.hour == 14 or utc.hour == 15  # EST or EDT


def test_to_et():
    from datetime import timezone
    utc = datetime(2024, 1, 3, 14, 30, tzinfo=timezone.utc)
    et = to_et(utc)
    assert et.hour == 9


def test_is_market_open():
    dt = ET.localize(datetime(2024, 1, 3, 11, 0))
    assert is_market_open(dt) is True


def test_market_hours_description():
    dt = ET.localize(datetime(2024, 1, 3, 11, 0))
    desc = get_market_hours_description(dt)
    assert "Regular" in desc


def test_afterhours_boundary():
    dt = ET.localize(datetime(2024, 1, 3, 20, 0))
    assert classify_session(dt) == SessionType.CLOSED


def test_premarket_just_after_start():
    dt = ET.localize(datetime(2024, 1, 3, 4, 0, 1))
    assert classify_session(dt) == SessionType.PREMARKET


def test_closed_before_premarket():
    dt = ET.localize(datetime(2024, 1, 3, 3, 59, 59))
    assert classify_session(dt) == SessionType.CLOSED


def test_closed_after_hours():
    dt = ET.localize(datetime(2024, 1, 3, 20, 0, 1))
    assert classify_session(dt) == SessionType.CLOSED


def test_sunday_classified_closed():
    dt = ET.localize(datetime(2024, 1, 7, 12, 0))
    assert classify_session(dt) == SessionType.CLOSED
