"""M023 Stage-B BUY-only session filter tests."""

from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pytest

from mamba2.backtest.m023_direction_research import (
    DirectionFilterBrokerProxy,
    P2_08_PARAMETERS,
    _require_stage_a_range,
)
from mamba2.backtest.m023_session_research import (
    STAGE_B_SESSIONS,
    SessionFilterBrokerProxy,
    stage_b_session,
)


class _Broker:
    def __init__(self):
        self.sent = []
        self.positions = [{"ticket": 1}]

    def order_send(self, request):
        self.sent.append(dict(request))
        return {"retcode": 10008, "order": len(self.sent)}

    async def positions_get(self, **kwargs):
        return list(self.positions)


def _proxy(arm_id: str, utc: str):
    broker = _Broker()
    direction = DirectionFilterBrokerProxy(
        broker,
        allowed_direction="BUY",
    )
    feed = SimpleNamespace(current_time=pd.Timestamp(utc))
    session = SessionFilterBrokerProxy(
        direction,
        feed=feed,
        session=stage_b_session(arm_id),
    )
    return broker, direction, session


def test_stage_b_matrix_is_exactly_five_frozen_arms():
    assert tuple(STAGE_B_SESSIONS) == (
        "S-R",
        "S-ACTIVE",
        "S-MORNING",
        "S-MIDDAY",
        "S-AFTERNOON",
    )
    with pytest.raises(ValueError, match="frozen M023 Stage-B matrix"):
        stage_b_session("S-EVENING")


def test_stage_b_anchor_remains_exact_p2_08_buy_only():
    p = P2_08_PARAMETERS
    assert (
        p.stochastic_k_period,
        p.stochastic_d_period,
        p.stochastic_slowing,
        p.oversold_level,
        p.overbought_level,
        p.ema_period,
        p.decision_spread_max_points,
        p.atr_sl_multiplier,
        p.atr_tp_multiplier,
        p.block_00_04_utc,
    ) == (21, 7, 7, 20.0, 80.0, 7, None, 1.5, 3.0, False)


@pytest.mark.parametrize(
    ("arm_id", "utc", "allowed"),
    [
        ("S-R", "2026-01-15T00:00:00Z", True),
        ("S-ACTIVE", "2026-01-15T05:00:00Z", True),
        ("S-ACTIVE", "2026-01-15T17:59:00Z", True),
        ("S-ACTIVE", "2026-01-15T18:00:00Z", False),
        ("S-MORNING", "2026-01-15T05:00:00Z", True),
        ("S-MORNING", "2026-01-15T08:59:00Z", True),
        ("S-MORNING", "2026-01-15T09:00:00Z", False),
        ("S-MIDDAY", "2026-01-15T09:00:00Z", True),
        ("S-MIDDAY", "2026-01-15T11:59:00Z", True),
        ("S-MIDDAY", "2026-01-15T12:00:00Z", False),
        ("S-AFTERNOON", "2026-01-15T12:00:00Z", True),
        ("S-AFTERNOON", "2026-01-15T14:59:00Z", True),
        ("S-AFTERNOON", "2026-01-15T15:00:00Z", False),
    ],
)
def test_stage_b_exact_eat_boundaries(arm_id, utc, allowed):
    broker, _direction, session = _proxy(arm_id, utc)
    result = session.order_send(
        {"symbol": "EURUSD", "type": 0, "price": 1.1}
    )
    assert (len(broker.sent) == 1) is allowed
    assert (result["retcode"] == session.RESEARCH_REJECT_CODE) is (not allowed)


def test_stage_b_zero_sell_entries_independent_of_session():
    broker, direction, session = _proxy(
        "S-ACTIVE",
        "2026-01-15T10:00:00Z",
    )
    result = session.order_send(
        {"symbol": "EURUSD", "type": 1, "price": 1.1}
    )
    assert broker.sent == []
    assert direction.rejected_by_side["SELL"] == 1
    assert result["retcode"] == direction.RESEARCH_REJECT_CODE


@pytest.mark.asyncio
async def test_outside_session_does_not_block_position_management_delegation():
    broker, _direction, session = _proxy(
        "S-MORNING",
        "2026-01-15T15:00:00Z",
    )
    positions = await session.positions_get(symbol="EURUSD")
    assert positions == [{"ticket": 1}]
    assert broker.positions == [{"ticket": 1}]


def test_session_filter_only_rejects_entry_and_never_forces_close():
    broker, _direction, session = _proxy(
        "S-MORNING",
        "2026-01-15T15:00:00Z",
    )
    result = session.order_send(
        {"symbol": "EURUSD", "type": 0, "price": 1.1}
    )
    assert result["retcode"] == session.RESEARCH_REJECT_CODE
    assert broker.positions == [{"ticket": 1}]
    assert session.rejections == 1


def test_stage_b_holdout_range_remains_refused():
    _require_stage_a_range(
        "2025-08-25T00:00:00Z",
        "2026-07-08T00:00:00Z",
    )
    with pytest.raises(ValueError, match="historical holdout is unavailable"):
        _require_stage_a_range(
            "2025-08-25T00:00:00Z",
            "2026-09-25T00:00:00Z",
        )


def test_africa_nairobi_named_zone_is_used():
    session = stage_b_session("S-MORNING")
    # 05:00 UTC == 08:00 EAT.
    assert session.allows(pd.Timestamp("2026-01-15T05:00:00Z"))
    # The same UTC clock would be outside an incorrectly interpreted 08:00 UTC.
    assert not session.allows(pd.Timestamp("2026-01-15T04:59:00Z"))
