"""A minimal example strategy for demonstration."""

from mamba2.strategy.base import Strategy
from loguru import logger

class StrategyImpl(Strategy):
    def evaluate(self, market):
        logger.info("Evaluating market via mock MT5...")
        rates = market.copy_rates_from_pos("EURUSD", timeframe=1, start_pos=0, count=5)
        logger.info(f"Received rates: {rates}")

        # Dummy logic: place order if close > open
        if rates[0]["close"] > rates[0]["open"]:
            resp = market.order_send({"symbol": "EURUSD", "type": "BUY"})
            logger.info(f"Order response: {resp}")
