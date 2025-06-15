"""Stochastic Triple Timeframe Strategy implementation."""

from mamba2.strategy.base import Strategy
from loguru import logger
from config import config
from mamba2.indicators.stochastic import get_stochastic
from mamba2.indicators.moving_average import get_moving_average


class StochasticTripleTFStrategy(Strategy):
    """
    Stochastic strategy using three timeframes:
    - Higher timeframe (M15) for market structure
    - Trading timeframe (M5) for confirmation
    - Entry timeframe (M1) for precise entry
    """

    def __init__(self, symbol="EURUSD"):
        super().__init__()
        self.symbol = symbol
        self.stochastic_timeframes = config.stochastic_timeframes
        self.k_period = config.stochastic_k_period
        self.ema_period = config.ema_period_entry
        self.doji_body_pct = config.doji_body_pct

    async def evaluate(self, market):
        """Evaluate market conditions using triple timeframe stochastic."""
        logger.info(f"StochasticTripleTFStrategy: Evaluating {self.symbol}...")

        # Get the rate_fetcher from market
        rate_fetcher = market.get('rate_fetcher')
        if not rate_fetcher:
            logger.error("No rate_fetcher in market context")
            return

        # Fetch rates for the three timeframes
        tf_higher = self.stochastic_timeframes['higher']
        tf_trading = self.stochastic_timeframes['trading']
        tf_entry = self.stochastic_timeframes['entry']

        # Get rates for each timeframe
        rates_higher = rate_fetcher.get_rates(self.symbol, tf_higher)
        rates_trading = rate_fetcher.get_rates(self.symbol, tf_trading)
        rates_entry = rate_fetcher.get_rates(self.symbol, tf_entry)

        # Check if we have enough data
        if rates_higher is None or rates_trading is None or rates_entry is None:
            logger.warning("Not enough data for stochastic triple strategy")
            return

        # Calculate stochastic for each timeframe
        stoch_higher = get_stochastic(symbol=self.symbol, timeframe=tf_higher, rate_fetcher=rate_fetcher)
        stoch_trading = get_stochastic(symbol=self.symbol, timeframe=tf_trading, rate_fetcher=rate_fetcher)
        stoch_entry = get_stochastic(symbol=self.symbol, timeframe=tf_entry, rate_fetcher=rate_fetcher)

        # Handle cases where stochastic calculation failed
        if stoch_higher is None or stoch_trading is None or stoch_entry is None:
            logger.warning(f"Could not calculate stochastic for one or more timeframes for {self.symbol}")
            return

        # Extract the last %K and %D for each
        try:
            k_higher = stoch_higher['k'].iloc[-1]
            d_higher = stoch_higher['d'].iloc[-1]
            k_trading = stoch_trading['k'].iloc[-1]
            d_trading = stoch_trading['d'].iloc[-1]
            k_entry = stoch_entry['k'].iloc[-1]
            d_entry = stoch_entry['d'].iloc[-1]
        except (IndexError, KeyError) as e:
            logger.error(f"Error extracting stochastic values: {str(e)}")
            return

        # Log the stochastic values for each timeframe
        logger.info(f"Stochastic for {tf_higher}: K={k_higher}, D={d_higher}")
        logger.info(f"Stochastic for {tf_trading}: K={k_trading}, D={d_trading}")
        logger.info(f"Stochastic for {tf_entry}: K={k_entry}, D={d_entry}")

        # Validate stochastic values
        def is_valid_stochastic(k, d):
            return k is not None and d is not None # k not in [0.0, 100.0] and d not in [0.0, 100.0]
            
        # Skip if entry timeframe (M1) has invalid stochastic
        if not is_valid_stochastic(k_entry, d_entry):
            logger.debug(f"Skipping {self.symbol} - invalid M1 stochastic values (K={k_entry}, D={d_entry})")
            return
            
        # Determine market structure using only valid timeframes
        valid_higher = is_valid_stochastic(k_higher, d_higher)
        valid_trading = is_valid_stochastic(k_trading, d_trading)
        
        if not valid_higher or not valid_trading:
            logger.debug(f"Skipping {self.symbol} - invalid higher/trading timeframe stochastic")
            return
            
        uptrend = (k_higher > d_higher) and (k_trading > d_trading)
        downtrend = (k_higher < d_higher) and (k_trading < d_trading)
        
        logger.debug(f"Uptrend: {uptrend}, Downtrend: {downtrend}")

        # Check entry conditions
        if uptrend:
            # Check for bullish entry signal on entry timeframe
            if k_entry > d_entry:
                # Get the 7-period EMA for the entry timeframe
                logger.debug(f"Fetching EMA for {self.symbol} on {tf_entry} with period {self.ema_period}")
                ema7 = get_moving_average(symbol=self.symbol, timeframe=tf_entry, ma_period=self.ema_period, ma_method='ema', rate_fetcher=rate_fetcher)
                if ema7 is None:
                    logger.error(f"Failed to calculate EMA for {self.symbol} on {tf_entry}. Aborting entry.")
                    return
                
                # Check the last candle: green and above EMA
                is_green_above_ema = self._last_green_above_ema(rates_entry, ema7)
                logger.debug(f"Uptrend Entry Check - K>D: {k_entry > d_entry}, Green Above EMA: {is_green_above_ema}")
                
                if is_green_above_ema:
                    logger.info(f"📈 BUY Signal - {self.symbol} - K={k_entry:.2f} > D={d_entry:.2f}, Price={rates_entry.iloc[-1]['close']}, EMA7={ema7}")
                    # Place buy order (let position manager handle SL/TP)
                    rates = market['rate_fetcher'].get_rates(self.symbol, 'M1')
                    if rates is None or len(rates) == 0:
                        logger.error(f"No rates available for {self.symbol}")
                        return
                    current_price = rates.iloc[-1]['close']
                    
                    order = {
                        "action": 1,  # TRADE_ACTION_DEAL for instant execution
                        "symbol": self.symbol,
                        "type": 0,  # 0 = ORDER_TYPE_BUY
                        "volume": 0.1,
                        "price": current_price,
                        "sl": 0.0,  # No stop loss
                        "tp": 0.0,   # No take profit
                        "deviation": 10,
                        "magic": 123456,
                        "comment": "Stochastic Triple Cross Strategy",
                        "type_time": 0,  # ORDER_TIME_GTC (Good till cancel)
                        "type_filling": 1  # ORDER_FILLING_FOK (Fill or Kill)
                    }
                    logger.info(f"Bullish entry signal. Placing BUY order: {order}")
                    resp = market['broker'].order_send(order)
                    if resp and resp.get('retcode') == 0 and market.get('position_manager'):
                        market['position_manager'].positions[self.symbol] = resp.get('order')
                    logger.info(f"Order response: {resp}")
        elif downtrend:
            # Check for bearish entry signal on entry timeframe
            if k_entry < d_entry:
                # Get the 7-period EMA for the entry timeframe
                logger.debug(f"Fetching EMA for {self.symbol} on {tf_entry} with period {self.ema_period}")
                ema7 = get_moving_average(symbol=self.symbol, timeframe=tf_entry, ma_period=self.ema_period, ma_method='ema', rate_fetcher=rate_fetcher)
                if ema7 is None:
                    logger.error(f"Failed to calculate EMA for {self.symbol} on {tf_entry}. Aborting entry.")
                    return
                
                # Check the last candle: red and below EMA
                is_red_below_ema = self._last_red_below_ema(rates_entry, ema7)
                logger.debug(f"Downtrend Entry Check - K<D: {k_entry < d_entry}, Red Below EMA: {is_red_below_ema}")
                
                if is_red_below_ema:
                    logger.info(f"📉 SELL Signal - {self.symbol} - K={k_entry:.2f} < D={d_entry:.2f}, Price={rates_entry.iloc[-1]['close']}, EMA7={ema7}")
                    # Place sell order
                    rates = market['rate_fetcher'].get_rates(self.symbol, 'M1')
                    if rates is None or len(rates) == 0:
                        logger.error(f"No rates available for {self.symbol}")
                        return
                    current_price = rates.iloc[-1]['close']
                    
                    order = {
                        "action": 1,  # TRADE_ACTION_DEAL for instant execution
                        "symbol": self.symbol,
                        "type": 1,  # 1 = ORDER_TYPE_SELL
                        "volume": 0.1,
                        "price": current_price,
                        "sl": 0.0,  # No stop loss
                        "tp": 0.0,   # No take profit
                        "deviation": 10,
                        "magic": 123456,
                        "comment": "Stochastic Triple TF Strategy",
                        "type_time": 0,  # ORDER_TIME_GTC (Good till cancel)
                        "type_filling": 1  # ORDER_FILLING_FOK (Fill or Kill)
                    }
                    logger.info(f"Bearish entry signal. Placing SELL order: {order}")
                    resp = market['broker'].order_send(order)
                    if resp and resp.get('retcode') == 0 and market.get('position_manager'):
                        market['position_manager'].positions[self.symbol] = resp.get('order')
                    logger.info(f"Order response: {resp}")

    def _is_doji(self, candle):
        """Check if candle is a doji (small body relative to range)."""
        body = abs(candle['close'] - candle['open'])
        total_range = candle['high'] - candle['low']
        if total_range == 0:
            return False
        body_pct = body / total_range
        return body_pct <= self.doji_body_pct

    def _registered_lower_lows(self, rates):
        """Check if last N candles show consecutive lower lows."""
        lookback = min(self.price_action_lookback, len(rates))
        if lookback < 2:
            return False

        lows = rates['low'].values[-lookback:]
        for i in range(1, lookback):
            if lows[i] >= lows[i-1]:
                return False
        return True

    def _registered_higher_highs(self, rates):
        """Check if last N candles show consecutive higher highs."""
        lookback = min(self.price_action_lookback, len(rates))
        if lookback < 2:
            return False

        highs = rates['high'].values[-lookback:]
        for i in range(1, lookback):
            if highs[i] <= highs[i-1]:
                return False
        return True

    def _last_green_above_ema(self, rates, ema_value):
        """Check if last candle is green and above EMA."""
        last_candle = rates.iloc[-1]
        is_green = last_candle['close'] > last_candle['open']
        is_above_ema = last_candle['close'] > ema_value
        logger.debug(f"Green Candle: {is_green} (Close: {last_candle['close']}, Open: {last_candle['open']})")
        logger.debug(f"Above EMA: {is_above_ema} (Close: {last_candle['close']}, EMA7: {ema_value})")
        return is_green and is_above_ema
        
    def _last_red_below_ema(self, rates, ema_value):
        """Check if last candle is red and below EMA."""
        last_candle = rates.iloc[-1]
        is_red = last_candle['close'] < last_candle['open']
        is_below_ema = last_candle['close'] < ema_value
        logger.debug(f"Red Candle: {is_red} (Close: {last_candle['close']}, Open: {last_candle['open']})")
        logger.debug(f"Below EMA: {is_below_ema} (Close: {last_candle['close']}, EMA7: {ema_value})")
        return is_red and is_below_ema