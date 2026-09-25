"""Explicit production semantics for ATR stop/target management."""

from types import SimpleNamespace

import pytest

from mamba2.crew.position_manager import PositionManager


class FakeATR:
    def __init__(self, value):
        self.value = value

    def is_ready(self):
        return True

    def get_atr(self, symbol, timeframe):
        return self.value


class FakeBroker:
    def __init__(self, position):
        self.position = position.copy()
        self.modify_calls = []

    async def positions_get(self, symbol="", ticket=0):
        position = self.position
        if symbol and position["symbol"] != symbol:
            return []
        if ticket and position["ticket"] != ticket:
            return []
        return [position.copy()]

    def get_point_size(self, symbol):
        return 0.00001

    async def order_modify(self, ticket, sl=0.0, tp=0.0):
        self.modify_calls.append(
            {"ticket": ticket, "sl": float(sl), "tp": float(tp)}
        )
        self.position["sl"] = float(sl)
        self.position["tp"] = float(tp)
        return {"retcode": 0, "comment": "modified"}


def configure(monkeypatch):
    import mamba2.crew.position_manager as position_module

    monkeypatch.setattr(
        position_module,
        "config",
        SimpleNamespace(
            atr_timeframe="M5",
            atr_sl_multiplier=1.0,
            atr_tp_multiplier=2.0,
        ),
    )


def position(*, side, current, sl, tp, open_price=None):
    return {
        "ticket": 1,
        "symbol": "EURUSD",
        "type": side,
        "price_open": current if open_price is None else open_price,
        "price_current": current,
        "sl": sl,
        "tp": tp,
    }


async def run_once(
    monkeypatch,
    *,
    side,
    current,
    sl,
    tp,
    atr,
    open_price=None,
):
    configure(monkeypatch)
    broker = FakeBroker(
        position(
            side=side,
            current=current,
            sl=sl,
            tp=tp,
            open_price=open_price,
        )
    )
    manager = PositionManager(
        broker,
        atr_manager=FakeATR(atr),
        rates_fetcher=None,
    )
    await manager.update_once()
    return broker, manager


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("atr", "expected_sl", "expected_tp", "expected_calls"),
    [
        (0.0100, 1.1150, 1.1450, 1),
        (0.0250, 1.1000, 1.1300, 0),
        (0.0300, 1.1000, 1.1300, 0),
    ],
)
async def test_buy_near_target_never_loosens_existing_stop(
    monkeypatch,
    atr,
    expected_sl,
    expected_tp,
    expected_calls,
):
    broker, _manager = await run_once(
        monkeypatch,
        side=0,
        current=1.1250,
        sl=1.1000,
        tp=1.1300,
        atr=atr,
    )

    assert len(broker.modify_calls) == expected_calls
    assert broker.position["sl"] == pytest.approx(expected_sl)
    assert broker.position["tp"] == pytest.approx(expected_tp)


@pytest.mark.asyncio
async def test_buy_not_near_target_does_not_trail(monkeypatch):
    broker, _manager = await run_once(
        monkeypatch,
        side=0,
        current=1.1150,
        sl=1.1000,
        tp=1.1300,
        atr=0.0100,
    )

    assert broker.modify_calls == []
    assert broker.position["sl"] == pytest.approx(1.1000)
    assert broker.position["tp"] == pytest.approx(1.1300)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("atr", "expected_sl", "expected_tp", "expected_calls"),
    [
        (0.0100, 1.1150, 1.0850, 1),
        (0.0250, 1.1300, 1.1000, 0),
        (0.0300, 1.1300, 1.1000, 0),
    ],
)
async def test_sell_near_target_never_loosens_existing_stop(
    monkeypatch,
    atr,
    expected_sl,
    expected_tp,
    expected_calls,
):
    broker, _manager = await run_once(
        monkeypatch,
        side=1,
        current=1.1050,
        sl=1.1300,
        tp=1.1000,
        atr=atr,
    )

    assert len(broker.modify_calls) == expected_calls
    assert broker.position["sl"] == pytest.approx(expected_sl)
    assert broker.position["tp"] == pytest.approx(expected_tp)


@pytest.mark.asyncio
async def test_sell_not_near_target_does_not_trail(monkeypatch):
    broker, _manager = await run_once(
        monkeypatch,
        side=1,
        current=1.1150,
        sl=1.1300,
        tp=1.1000,
        atr=0.0100,
    )

    assert broker.modify_calls == []
    assert broker.position["sl"] == pytest.approx(1.1300)
    assert broker.position["tp"] == pytest.approx(1.1000)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("side", "expected_sl", "expected_tp"),
    [
        (0, 1.1100, 1.1400),
        (1, 1.1300, 1.1000),
    ],
)
async def test_initial_atr_protection_is_installed(
    monkeypatch,
    side,
    expected_sl,
    expected_tp,
):
    broker, _manager = await run_once(
        monkeypatch,
        side=side,
        current=1.1200,
        sl=0.0,
        tp=0.0,
        atr=0.0100,
    )

    assert len(broker.modify_calls) == 1
    assert broker.position["sl"] == pytest.approx(expected_sl)
    assert broker.position["tp"] == pytest.approx(expected_tp)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "side",
        "open_price",
        "current",
        "expected_sl",
        "expected_tp",
    ),
    [
        # BUY fills at Ask while its immediately executable closing side is
        # Bid.  A spread wider than the target ATR distance must not put TP
        # below the entry fill.
        (0, 1.1200, 1.1000, 1.0950, 1.1300),
        # SELL fills at Bid while its immediately executable closing side is
        # Ask.  A wide spread must not put TP above the entry fill.
        (1, 1.1000, 1.1200, 1.1250, 1.0900),
    ],
)
async def test_initial_atr_target_never_crosses_entry_fill_under_wide_spread(
    monkeypatch,
    side,
    open_price,
    current,
    expected_sl,
    expected_tp,
):
    broker, _manager = await run_once(
        monkeypatch,
        side=side,
        open_price=open_price,
        current=current,
        sl=0.0,
        tp=0.0,
        atr=0.0050,
    )

    assert len(broker.modify_calls) == 1
    assert broker.position["sl"] == pytest.approx(expected_sl)
    assert broker.position["tp"] == pytest.approx(expected_tp)

    if side == 0:
        assert broker.position["tp"] > open_price
    else:
        assert broker.position["tp"] < open_price


@pytest.mark.asyncio
@pytest.mark.parametrize("atr", [None, 0.0, -0.001])
@pytest.mark.parametrize("side", [0, 1])
async def test_unavailable_atr_never_modifies_protected_position(
    monkeypatch,
    side,
    atr,
):
    sl, tp, current = (
        (1.1000, 1.1300, 1.1250)
        if side == 0
        else (1.1300, 1.1000, 1.1050)
    )
    broker, _manager = await run_once(
        monkeypatch,
        side=side,
        current=current,
        sl=sl,
        tp=tp,
        atr=atr,
    )

    assert broker.modify_calls == []
    assert broker.position["sl"] == pytest.approx(sl)
    assert broker.position["tp"] == pytest.approx(tp)


@pytest.mark.asyncio
@pytest.mark.parametrize("side", [0, 1])
async def test_rejected_trailing_stop_does_not_move_take_profit(
    monkeypatch,
    side,
):
    if side == 0:
        current, sl, tp, atr = 1.1250, 1.1000, 1.1300, 0.0300
    else:
        current, sl, tp, atr = 1.1050, 1.1300, 1.1000, 0.0300

    broker, _manager = await run_once(
        monkeypatch,
        side=side,
        current=current,
        sl=sl,
        tp=tp,
        atr=atr,
    )

    assert broker.modify_calls == []
    assert broker.position["sl"] == pytest.approx(sl)
    assert broker.position["tp"] == pytest.approx(tp)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("side", "current", "sl", "tp", "expected_sl", "expected_tp"),
    [
        (0, 1.1250, 1.1000, 1.1300, 1.1150, 1.1450),
        (1, 1.1050, 1.1300, 1.1000, 1.1150, 1.0850),
    ],
)
async def test_successful_trailing_update_moves_stop_and_target_together(
    monkeypatch,
    side,
    current,
    sl,
    tp,
    expected_sl,
    expected_tp,
):
    broker, _manager = await run_once(
        monkeypatch,
        side=side,
        current=current,
        sl=sl,
        tp=tp,
        atr=0.0100,
    )

    assert len(broker.modify_calls) == 1
    call = broker.modify_calls[0]
    assert call["sl"] == pytest.approx(expected_sl)
    assert call["tp"] == pytest.approx(expected_tp)
    assert broker.position["sl"] == pytest.approx(expected_sl)
    assert broker.position["tp"] == pytest.approx(expected_tp)


@pytest.mark.asyncio
async def test_live_wrapper_and_replay_entry_point_share_same_semantics(
    monkeypatch,
):
    configure(monkeypatch)
    initial = position(
        side=0,
        current=1.1250,
        sl=1.1000,
        tp=1.1300,
    )

    replay_broker = FakeBroker(initial)
    replay = PositionManager(
        replay_broker,
        atr_manager=FakeATR(0.0100),
    )
    await replay.update_once()

    live_broker = FakeBroker(initial)
    live = PositionManager(
        live_broker,
        atr_manager=FakeATR(0.0100),
    )
    live.running = True
    await live.update_trailing_stops()

    assert replay_broker.modify_calls == live_broker.modify_calls
    assert replay_broker.position == live_broker.position
