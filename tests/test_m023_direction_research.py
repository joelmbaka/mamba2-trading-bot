"""M023 Stage-A causal direction machinery tests."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from mamba2.backtest.m023_direction_research import (
    M023_STAGE_A_DATE_LIST_SHA256,
    M023_STAGE_A_END_EXCLUSIVE_UTC,
    M023_STAGE_A_FOLDS,
    M023_STAGE_A_START_UTC,
    P2_08_PARAMETERS,
    STAGE_A_DIRECTIONS,
    DirectionFilterBrokerProxy,
    DirectionStrategyWrapper,
    _require_stage_a_range,
    stage_a_arm,
)


def test_stage_a_matrix_is_exactly_three_frozen_arms():
    assert STAGE_A_DIRECTIONS == {
        "D-R": "BOTH",
        "D-S": "SELL",
        "D-B": "BUY",
    }
    assert stage_a_arm("D-R").direction == "BOTH"
    assert stage_a_arm("D-S").direction == "SELL"
    assert stage_a_arm("D-B").direction == "BUY"

    with pytest.raises(ValueError, match="frozen M023 Stage-A matrix"):
        stage_a_arm("D-X")


def test_stage_a_anchor_is_exact_p2_08():
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


def test_stage_a_partition_and_folds_are_exactly_frozen():
    assert M023_STAGE_A_START_UTC == "2025-08-25T00:00:00Z"
    assert M023_STAGE_A_END_EXCLUSIVE_UTC == "2026-07-08T00:00:00Z"
    assert (
        M023_STAGE_A_DATE_LIST_SHA256
        == "50b56aabc47dd0f485d07ee531b9967922a7b81780b02aacf8affc80f744dfb0"
    )
    assert [row[0] for row in M023_STAGE_A_FOLDS] == [
        "F1",
        "F2",
        "F3",
        "F4",
        "F5",
    ]


def test_holdout_range_is_refused_before_manifest_access():
    _require_stage_a_range(
        "2025-08-25T00:00:00Z",
        "2026-07-08T00:00:00Z",
    )
    with pytest.raises(ValueError, match="historical holdout is unavailable"):
        _require_stage_a_range(
            "2025-08-25T00:00:00Z",
            "2026-09-25T00:00:00Z",
        )


class _Broker:
    def __init__(self):
        self.sent = []

    def order_send(self, request):
        self.sent.append(dict(request))
        return {"retcode": 10008, "order": len(self.sent)}


@pytest.mark.parametrize(
    ("allowed", "side_type", "rejected"),
    [
        ("BOTH", 0, False),
        ("BOTH", 1, False),
        ("SELL", 0, True),
        ("SELL", 1, False),
        ("BUY", 0, False),
        ("BUY", 1, True),
    ],
)
def test_direction_proxy_changes_new_entry_eligibility_only(
    allowed,
    side_type,
    rejected,
):
    broker = _Broker()
    proxy = DirectionFilterBrokerProxy(
        broker,
        allowed_direction=allowed,
    )
    result = proxy.order_send(
        {
            "symbol": "EURUSD",
            "type": side_type,
            "price": 1.1,
        }
    )

    if rejected:
        assert result["retcode"] == proxy.RESEARCH_REJECT_CODE
        assert broker.sent == []
        assert proxy.rejections == 1
    else:
        assert result["retcode"] == 10008
        assert len(broker.sent) == 1
        assert proxy.rejections == 0


def test_direction_proxy_refuses_unknown_order_type():
    proxy = DirectionFilterBrokerProxy(_Broker(), allowed_direction="BOTH")
    with pytest.raises(ValueError, match="unsupported entry order type"):
        proxy.order_send(
            {"symbol": "EURUSD", "type": 2, "price": 1.1}
        )


@pytest.mark.asyncio
async def test_strategy_wrapper_replaces_only_broker():
    seen = {}

    class Strategy:
        symbol = "EURUSD"

        async def evaluate(self, market):
            seen.update(market)

    broker = _Broker()
    proxy = DirectionFilterBrokerProxy(
        broker,
        allowed_direction="SELL",
    )
    wrapper = DirectionStrategyWrapper(Strategy(), proxy)
    marker = object()

    await wrapper.evaluate(
        {
            "broker": marker,
            "position_manager": "pm",
            "rate_fetcher": "rf",
        }
    )

    assert seen["broker"] is proxy
    assert seen["position_manager"] == "pm"
    assert seen["rate_fetcher"] == "rf"


def test_direction_proxy_tracks_passed_and_rejected_sides():
    broker = _Broker()
    proxy = DirectionFilterBrokerProxy(
        broker,
        allowed_direction="SELL",
    )
    proxy.order_send({"symbol": "EURUSD", "type": 0, "price": 1.1})
    proxy.order_send({"symbol": "EURUSD", "type": 1, "price": 1.1})

    assert proxy.rejected_by_side == {"BUY": 1, "SELL": 0}
    assert proxy.passed_by_side == {"BUY": 0, "SELL": 1}
    assert len(broker.sent) == 1


def test_stage_a_arm_parameters_are_immutable_reference():
    arm = stage_a_arm("D-S")
    assert arm.parameters is P2_08_PARAMETERS
    assert arm.direction == "SELL"
