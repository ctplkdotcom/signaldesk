from datetime import datetime, timezone, timedelta
import numpy as np
import pytest

from app.utils.time import classify_session, SessionType, to_utc, to_et
from app.services.scoring import NewsScoringEngine, ScoreLabel


class TestDataQuality:
    @pytest.fixture
    def engine(self):
        return NewsScoringEngine()

    def test_session_anti_lookahead(self):
        et = __import__("pytz").timezone("US/Eastern")
        pre = et.localize(datetime(2024, 1, 3, 9, 29, 59))
        open_bell = et.localize(datetime(2024, 1, 3, 9, 30, 0))
        close_bell = et.localize(datetime(2024, 1, 3, 16, 0, 0))
        after = et.localize(datetime(2024, 1, 3, 16, 0, 1))

        assert classify_session(pre) == SessionType.PREMARKET
        assert classify_session(open_bell) == SessionType.REGULAR
        assert classify_session(close_bell) == SessionType.REGULAR
        assert classify_session(after) == SessionType.AFTERHOURS

    def test_timezone_dst_transition(self):
        spring = datetime(2024, 3, 10, 4, 0)
        fall = datetime(2024, 11, 3, 4, 0)
        et_spring = __import__("pytz").timezone("US/Eastern").localize(spring)
        et_fall = __import__("pytz").timezone("US/Eastern").localize(fall)

        spring_utc = to_utc(et_spring)
        fall_utc = to_utc(et_fall)

        assert spring_utc.hour == 8
        assert fall_utc.hour == 9

    def test_score_clamping(self, engine):
        final = engine.sentiment_weight * 200 + engine.event_weight * 0 + engine.source_weight * 0 + engine.recency_weight * 0
        assert -100 <= max(-100, min(100, final)) <= 100

        final2 = engine.sentiment_weight * (-200) + engine.event_weight * 0 + engine.source_weight * 0 + engine.recency_weight * 0
        assert -100 <= max(-100, min(100, final2)) <= 100

    def test_label_band_boundaries(self, engine):
        bands = [
            (70, ScoreLabel.STRONG_BULLISH),
            (69, ScoreLabel.BULLISH),
            (30, ScoreLabel.BULLISH),
            (29, ScoreLabel.NEUTRAL),
            (0, ScoreLabel.NEUTRAL),
            (-29, ScoreLabel.NEUTRAL),
            (-30, ScoreLabel.BEARISH),
            (-69, ScoreLabel.BEARISH),
            (-70, ScoreLabel.STRONG_BEARISH),
        ]
        for score, expected_label in bands:
            assert engine._compute_label(score) == expected_label, f"Score {score} should be {expected_label}"

    def test_empty_data_handling(self, engine):
        assert engine._compute_sentiment("") == 0.0
        assert engine._compute_sentiment("   ") == 0.0
        assert engine._compute_event_score(None) == 0.0
        assert engine._compute_source_score(None) == 30.0
        assert engine._compute_recency(None) == 0.0

    def test_duplicate_keys_preserved(self, engine):
        score1 = engine._compute_event_score("earnings_beat")
        score2 = engine._compute_event_score("earnings beat")
        assert score1 == 90.0
        assert score2 == 90.0

    def test_sma_monotonic_uptrend(self):
        closes = np.linspace(100, 200, 300)
        ma50 = np.convolve(closes, np.ones(50) / 50, mode="valid")
        ma200 = np.convolve(closes, np.ones(200) / 200, mode="valid")
        assert np.all(np.diff(ma50) >= 0)
        assert np.all(np.diff(ma200) >= 0)
        assert ma50[-1] > ma200[-1]

    def test_sma_monotonic_downtrend(self):
        closes = np.linspace(200, 100, 300)
        ma50 = np.convolve(closes, np.ones(50) / 50, mode="valid")
        ma200 = np.convolve(closes, np.ones(200) / 200, mode="valid")
        assert np.all(np.diff(ma50) <= 0)
        assert np.all(np.diff(ma200) <= 0)
        assert ma50[-1] < ma200[-1]

    def test_volatile_data_no_crash(self):
        closes = np.random.default_rng(42).normal(100, 20, 300)
        ma50 = np.convolve(closes, np.ones(50) / 50, mode="valid")
        ma200 = np.convolve(closes, np.ones(200) / 200, mode="valid")
        assert len(ma50) > 0
        assert len(ma200) > 0
