import numpy as np
import pytest


def _sma(data: np.ndarray, period: int) -> np.ndarray:
    if len(data) < period:
        return np.array([])
    return np.convolve(data, np.ones(period) / period, mode="valid")


class TestMASignal:
    def test_ma_crosses_above(self):
        closes = np.concatenate([
            np.linspace(100, 100, 150),
            np.linspace(100, 130, 100),
        ])
        assert len(closes) >= 200
        ma50 = _sma(closes, 50)
        ma200 = _sma(closes, 200)
        min_len = min(len(ma50), len(ma200))
        assert ma50[-1] > ma200[-1]

    def test_ma_crosses_below(self):
        closes = np.concatenate([
            np.linspace(130, 130, 150),
            np.linspace(130, 100, 100),
        ])
        assert len(closes) >= 200
        ma50 = _sma(closes, 50)
        ma200 = _sma(closes, 200)
        min_len = min(len(ma50), len(ma200))
        assert ma50[-1] < ma200[-1]

    def test_ma_not_crossed(self):
        closes = np.linspace(100, 130, 250)
        ma50 = _sma(closes, 50)
        ma200 = _sma(closes, 200)
        min_len = min(len(ma50), len(ma200))
        with_50 = ma50[-min_len:]
        with_200 = ma200[-min_len:]
        assert np.all(with_50 > with_200)

    def test_sma_basic(self):
        data = np.array([1, 2, 3, 4, 5], dtype=float)
        result = _sma(data, 3)
        assert result[0] == pytest.approx(2.0)
        assert result[-1] == pytest.approx(4.0)
        assert len(result) == 3

    def test_sma_insufficient_data(self):
        data = np.array([1, 2], dtype=float)
        result = _sma(data, 3)
        assert len(result) == 0
