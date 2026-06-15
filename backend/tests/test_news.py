from datetime import datetime, timezone, timedelta
import pytest

from app.services.scoring import NewsScoringEngine, ScoreLabel


class TestNewsScoring:
    @pytest.fixture
    def engine(self):
        return NewsScoringEngine()

    def test_positive_sentiment(self, engine):
        score = engine._compute_sentiment("MU beats earnings estimates, profit surges 20%")
        assert score > 0

    def test_negative_sentiment(self, engine):
        score = engine._compute_sentiment("VOO drops on recession fears, loss widens")
        assert score < 0

    def test_neutral(self, engine):
        score = engine._compute_sentiment("Market opens mixed today")
        assert score == 0.0

    def test_event_earnings_beat(self, engine):
        score = engine._compute_event_score("earnings_beat")
        assert score == 90.0

    def test_event_earnings_miss(self, engine):
        score = engine._compute_event_score("earnings_miss")
        assert score == -90.0

    def test_event_none(self, engine):
        score = engine._compute_event_score(None)
        assert score == 0.0

    def test_event_unknown(self, engine):
        score = engine._compute_event_score("unknown_type")
        assert score == 0.0

    def test_event_human_readable_key(self, engine):
        score = engine._compute_event_score("earnings beat")
        assert score == 90.0

    def test_event_human_readable_miss(self, engine):
        score = engine._compute_event_score("earnings miss")
        assert score == -90.0

    def test_source_reuters(self, engine):
        score = engine._compute_source_score("Reuters")
        assert score == 90.0

    def test_source_unknown(self, engine):
        score = engine._compute_source_score("unknown_blog")
        assert score == 30.0

    def test_recency_recent(self, engine):
        score = engine._compute_recency(datetime.now(timezone.utc) - timedelta(hours=1))
        assert score > 80

    def test_recency_old(self, engine):
        score = engine._compute_recency(datetime.now(timezone.utc) - timedelta(days=30))
        assert score < 20

    def test_label_strong_bullish(self, engine):
        assert engine._compute_label(85) == ScoreLabel.STRONG_BULLISH

    def test_label_bullish(self, engine):
        assert engine._compute_label(50) == ScoreLabel.BULLISH

    def test_label_neutral(self, engine):
        assert engine._compute_label(0) == ScoreLabel.NEUTRAL

    def test_label_bearish(self, engine):
        assert engine._compute_label(-50) == ScoreLabel.BEARISH

    def test_label_strong_bearish(self, engine):
        assert engine._compute_label(-85) == ScoreLabel.STRONG_BEARISH

    def test_final_score_positive(self, engine):
        sent = engine._compute_sentiment("Strong beat earnings, raised guidance, profit surges")
        ev = engine._compute_event_score("earnings_beat")
        src = engine._compute_source_score("reuters")
        rec = engine._compute_recency(datetime.now(timezone.utc))
        final = engine.sentiment_weight * sent + engine.event_weight * ev + engine.source_weight * src + engine.recency_weight * rec
        assert final > 50

    def test_final_score_negative(self, engine):
        sent = engine._compute_sentiment("Bankruptcy fears, massive losses, fraud investigation, delist warning, default risk, crash")
        ev = engine._compute_event_score("earnings_miss")
        src = engine._compute_source_score("unknown_blog")
        rec = engine._compute_recency(datetime.now(timezone.utc) - timedelta(days=30))
        final = engine.sentiment_weight * sent + engine.event_weight * ev + engine.source_weight * src + engine.recency_weight * rec
        assert final < -30
