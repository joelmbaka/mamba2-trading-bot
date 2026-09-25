"""Stochastic Triple Timeframe Strategy implementation."""

import time
import os
from mamba2.strategy.base import Strategy
from loguru import logger
from config import config
from mamba2.indicators.stochastic import get_stochastic
from mamba2.crew.market_analyst import count_candle_pattern
from mamba2.indicators.candles import is_doji, is_hammer, is_shooting_star
from mamba2.indicators.detect_trend import calculate_5min_trendline
from mamba2.indicators.RSI import get_rsi

# Constants for order types (should match MT5 constants but we don't import MT5 directly)
TRADE_ACTION_DEAL = 1
ORDER_TYPE_BUY = 0
ORDER_TYPE_SELL = 1
ORDER_TIME_GTC = 0
ORDER_FILLING_FOK = 1


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
        self.use_higher_tf = config.use_higher_tf  # New configuration option
        
    async def evaluate(self, market):
        """Evaluate market conditions using triple timeframe stochastic."""
 #       logger.info(f"StochasticTripleTFStrategy: Evaluating {self.symbol}...")

        # Get the rate_fetcher from market
        rate_fetcher = market.get('rate_fetcher')
        if not rate_fetcher:
            logger.error("No rate_fetcher in market context")
            return

        # Fetch rates for the three timeframes
        tf_higher = self.stochastic_timeframes['higher']
        tf_trading = self.stochastic_timeframes['trading']
        tf_entry = self.stochastic_timeframes['entry']

        # Get only the timeframes required by the active signal filters.
        # A disabled higher-TF filter must not make M15 data a hidden
        # prerequisite for M5/M1 signal evaluation.
        rates_higher = (
            rate_fetcher.get_rates(self.symbol, tf_higher)
            if self.use_higher_tf
            else None
        )
        rates_trading = rate_fetcher.get_rates(self.symbol, tf_trading)
        rates_entry = rate_fetcher.get_rates(self.symbol, tf_entry)

        required_rates = [rates_trading, rates_entry]
        if self.use_higher_tf:
            required_rates.append(rates_higher)
        if any(rates is None for rates in required_rates):
            logger.warning("Not enough data for stochastic triple strategy")
            return

        # Calculate stochastic only for active signal timeframes.
        stoch_higher = (
            get_stochastic(
                symbol=self.symbol,
                timeframe=tf_higher,
                rate_fetcher=rate_fetcher,
            )
            if self.use_higher_tf
            else None
        )
        stoch_trading = get_stochastic(
            symbol=self.symbol,
            timeframe=tf_trading,
            rate_fetcher=rate_fetcher,
        )
        stoch_entry = get_stochastic(
            symbol=self.symbol,
            timeframe=tf_entry,
            rate_fetcher=rate_fetcher,
            lookback_period=10,
        )

        if (
            stoch_trading is None
            or stoch_entry is None
            or (self.use_higher_tf and stoch_higher is None)
        ):
            logger.warning(
                f"Could not calculate stochastic for one or more active "
                f"timeframes for {self.symbol}"
            )
            return

        # Extract the last %K and %D for each active timeframe.
        try:
            k_higher = (
                stoch_higher['k'].iloc[-1]
                if self.use_higher_tf
                else None
            )
            d_higher = (
                stoch_higher['d'].iloc[-1]
                if self.use_higher_tf
                else None
            )
            k_trading = stoch_trading['k'].iloc[-1]
            d_trading = stoch_trading['d'].iloc[-1]
            # Add debug logging for stochastic values
            """
            logger.debug(f"Stochastic values - Entry TF ({tf_entry}): K={k_entry:.2f}, D={d_entry:.2f}")
            logger.debug(f"Stochastic values - Trading TF ({tf_trading}): K={k_trading:.2f}, D={d_trading:.2f}")
            logger.debug(f"Stochastic values - Higher TF ({tf_higher}): K={k_higher:.2f}, D={d_higher:.2f}")
            """
        except (IndexError, KeyError) as e:
            logger.error(f"Error extracting stochastic values: {str(e)}")
            return

        # Validate stochastic values and check conditions
        def is_valid_stochastic(k, d):
            return k is not None and d is not None
            
        # Check all timeframes together
        conditions = [
            is_valid_stochastic(k_trading, d_trading),
            is_valid_stochastic(stoch_entry['k'].iloc[-1], stoch_entry['d'].iloc[-1])
        ]
        
        # Conditionally include higher timeframe check based on configuration
        if self.use_higher_tf:
            conditions.append(is_valid_stochastic(k_higher, d_higher))
        
        if all(conditions):
            
            # Trend is an optional filter, not a master trading switch.
            # When disabled, signal evaluation must not depend on trend data.
            trend = "disabled"
            if config.ENABLE_TREND_CONDITION:
                rates_5min = rate_fetcher.get_rates(self.symbol, 'M5')
                trend = calculate_5min_trendline(rates_5min)
                if trend not in ['uptrend', 'downtrend']:
                    logger.debug(f"Skipping {self.symbol} because trend is {trend}")
                    logger.info(f"{self.symbol} - Trend is {trend}")
                    return

            buy_trend_allowed = (
                not config.ENABLE_TREND_CONDITION or trend == 'uptrend'
            )
            sell_trend_allowed = (
                not config.ENABLE_TREND_CONDITION or trend == 'downtrend'
            )

            if buy_trend_allowed:
                # Only look for buy signals
                oversold_level = 20
                buy_conditions = [
                    k_trading > d_trading,
                    (stoch_entry['k'] < oversold_level).any(),
                    stoch_entry['k'].iloc[-1] > stoch_entry['d'].iloc[-1]
                ]
                
                # Conditionally include higher timeframe check
                if self.use_higher_tf:
                    buy_conditions.append(k_higher > d_higher)
                
                if all(buy_conditions):
                    # Check RSI condition if enabled in config
                    if config.ENABLE_RSI_CONDITION:
                        # Calculate RSI for the entry timeframe
                        rsi = get_rsi(symbol=self.symbol, timeframe=tf_trading, rate_fetcher=rate_fetcher)
                        if rsi is None:
                            logger.warning(f"Could not calculate RSI for {self.symbol} on {tf_trading}")
                            return
                        try:
                            # If it's a pandas Series, get the last value by index
                            current_rsi = rsi.iloc[-1]
                        except AttributeError:
                            # If it doesn't have iloc, assume it's a scalar
                            current_rsi = rsi

                        if current_rsi <= 50:
                            logger.debug(f"{self.symbol} - Buy signal skipped because RSI ({current_rsi:.2f}) is not above 50")
                            return

                    # Wait for a green candle to close above 7-period EMA
                    rates = market['rate_fetcher'].get_rates(self.symbol, 'M1')
                    if len(rates) < 2:  # Need at least 2 candles to check current and previous
                        return
                    
                    # Get 7-period EMA
                    from mamba2.indicators.moving_average import get_moving_average
                    ema7 = get_moving_average(self.symbol, 'M1', 7, 'ema', market['rate_fetcher'])
                    
                    if ema7 is None:
                        logger.warning(f"Could not calculate 7-period EMA for {self.symbol}")
                        return
                    
                    # Check if current candle is green and closed above EMA7
                    current_candle = rates.iloc[-1]
                    if current_candle['close'] <= ema7 or current_candle['close'] <= current_candle['open']:
                        logger.debug(f"{self.symbol} - Buy signal skipped - waiting for green candle above EMA7. Current close: {current_candle['close']}, EMA7: {ema7:.5f}")
                        return
                    
                    # Log the buy signal with conditional higher TF info
                    higher_tf_log = f"Higher K={k_higher:.2f} > D={d_higher:.2f}, " if self.use_higher_tf else ""
                    logger.info(f"📈 BUY Signal - {self.symbol}: Trend is {trend} - {higher_tf_log}Trading K={k_trading:.2f} > D={d_trading:.2f}, Entry K={stoch_entry['k'].iloc[-1]:.2f} > D={stoch_entry['d'].iloc[-1]:.2f}")
                    
                    # Place buy order (let position manager handle SL/TP)
                    rates = market['rate_fetcher'].get_rates(self.symbol, 'M1')
                    # Get current market data from the broker
                    try:
                        # The broker should provide the current price
                        symbol_info = market['broker'].symbol_info_tick(self.symbol)
                        if not symbol_info:
                            logger.error(f"Failed to get current price for {self.symbol}")
                            return
                            
                        order = {
                            "action": TRADE_ACTION_DEAL,
                            "symbol": self.symbol,
                            "type": ORDER_TYPE_BUY,
                            "volume": config.position_size,
                            "price": symbol_info['ask'] if 'ask' in symbol_info else symbol_info['bid'],
                            "sl": 0.0,  # No stop loss
                            "tp": 0.0,   # No take profit
                            "deviation": 10,
                            "magic": 123456,
                            "comment": "Stochastic Triple Cross",
                            "type_time": ORDER_TIME_GTC,
                            "type_filling": ORDER_FILLING_FOK
                        }
                    except Exception as e:
                        logger.error(f"Error getting market data for {self.symbol}: {str(e)}")
                        return
                    logger.info(f"Bullish entry signal. Placing BUY order: {order}")
                    
                    # NEW: Requote handling with retries
                    MAX_RETRIES = 3
                    for attempt in range(MAX_RETRIES):
                        resp = market['broker'].order_send(order)
                        
                        # Handle successful order or execution notification
                        if resp and (resp.get('retcode') == 0 or resp.get('retcode') == 10009):
                            if resp.get('retcode') == 10009:  # Order executed notification
                                logger.debug(f"Order executed: {resp}")
                            else:
                                logger.info(f"Order response: {resp}")
                            if market.get('position_manager'):
                                market['position_manager'].positions[self.symbol] = resp.get('order')
                            break
                            
                        # Handle requote (10004)
                        if resp and resp.get('retcode') == 10004:
                            # Calculate price difference
                            price_diff = abs(resp['price'] - order['price'])
                            
                            # Accept price within tolerance (0.1%)
                            if price_diff / order['price'] < 0.001:
                                order['price'] = resp['price']
                                logger.warning(f"Requote accepted (attempt {attempt+1}/{MAX_RETRIES})")
                                continue
                            
                            logger.warning(f"Requote rejected (price diff: {price_diff:.4f})")
                            
                        # Log other errors and break
                        if resp and resp.get('retcode') not in [0, 10004, 10009]:  # Skip already handled codes
                            logger.error(f"Order failed with code {resp.get('retcode')}: {resp}")
                        break
                    
                    if market.get("reporting_enabled", True):
                        self._record_entry_artifacts(
                            response=resp,
                            order_type="buy",
                            trend=trend,
                            rates_higher=rates_higher,
                            rates_trading=rates_trading,
                            rates_entry=rates_entry,
                            tf_higher=tf_higher,
                            tf_trading=tf_trading,
                            tf_entry=tf_entry,
                            rate_fetcher=market['rate_fetcher'],
                        )
            if sell_trend_allowed:
                # Only look for sell signals
                overbought_level = 80
                sell_conditions = [
                    k_trading < d_trading,
                    (stoch_entry['k'] > overbought_level).any(),
                    stoch_entry['k'].iloc[-1] < stoch_entry['d'].iloc[-1]
                ]
                
                # Conditionally include higher timeframe check
                if self.use_higher_tf:
                    sell_conditions.append(k_higher < d_higher)
                
                if all(sell_conditions):
                    # Apply the RSI filter only when explicitly enabled.
                    if config.ENABLE_RSI_CONDITION:
                        rsi = get_rsi(
                            symbol=self.symbol,
                            timeframe=tf_trading,
                            rate_fetcher=rate_fetcher,
                        )
                        if rsi is None:
                            logger.warning(
                                f"Could not calculate RSI for {self.symbol} "
                                f"on {tf_trading}"
                            )
                            return
                        try:
                            current_rsi = rsi.iloc[-1]
                        except AttributeError:
                            current_rsi = rsi

                        if current_rsi >= 50:
                            logger.debug(
                                f"{self.symbol} - Sell signal skipped because "
                                f"RSI ({current_rsi:.2f}) is not below 50"
                            )
                            return

                    # Wait for a red candle to close below 7-period EMA
                    rates = market['rate_fetcher'].get_rates(self.symbol, 'M1')
                    if len(rates) < 2:  # Need at least 2 candles to check current and previous
                        return
                    
                    # Get 7-period EMA
                    from mamba2.indicators.moving_average import get_moving_average
                    ema7 = get_moving_average(self.symbol, 'M1', 7, 'ema', market['rate_fetcher'])
                    
                    if ema7 is None:
                        logger.warning(f"Could not calculate 7-period EMA for {self.symbol}")
                        return
                    
                    # Check if current candle is red and closed below EMA7
                    current_candle = rates.iloc[-1]
                    if current_candle['close'] >= ema7 or current_candle['close'] >= current_candle['open']:
                        logger.debug(f"{self.symbol} - Sell signal skipped - waiting for red candle below EMA7. Current close: {current_candle['close']}, EMA7: {ema7:.5f}")
                        return
                    higher_tf_log = (
                        f"Higher K={k_higher:.2f} < D={d_higher:.2f}, "
                        if self.use_higher_tf
                        else ""
                    )
                    logger.info(
                        f"📉 SELL Signal - {self.symbol}: Trend is {trend} - "
                        f"{higher_tf_log}Trading K={k_trading:.2f} < "
                        f"D={d_trading:.2f}, Entry K="
                        f"{stoch_entry['k'].iloc[-1]:.2f} < "
                        f"D={stoch_entry['d'].iloc[-1]:.2f}"
                    )
                    # Place sell order
                    rates = market['rate_fetcher'].get_rates(self.symbol, 'M1')
                    # Get current market data from the broker
                    try:
                        # The broker should provide the current price
                        symbol_info = market['broker'].symbol_info_tick(self.symbol)
                        if not symbol_info:
                            logger.error(f"Failed to get current price for {self.symbol}")
                            return
                            
                        order = {
                            "action": TRADE_ACTION_DEAL,
                            "symbol": self.symbol,
                            "type": ORDER_TYPE_SELL,
                            "volume": config.position_size,
                            "price": symbol_info['bid'] if 'bid' in symbol_info else symbol_info['ask'],
                            "sl": 0.0,  # No stop loss
                            "tp": 0.0,   # No take profit
                            "deviation": 10,
                            "magic": 123456,
                            "comment": "Stochastic Triple Cross",
                            "type_time": ORDER_TIME_GTC,
                            "type_filling": ORDER_FILLING_FOK
                        }
                    except Exception as e:
                        logger.error(f"Error getting market data for {self.symbol}: {str(e)}")
                        return
                    logger.info(f"Bearish entry signal. Placing SELL order: {order}")
                    
                    # NEW: Requote handling with retries
                    MAX_RETRIES = 3
                    for attempt in range(MAX_RETRIES):
                        resp = market['broker'].order_send(order)
                        
                        # Handle successful order or execution notification
                        if resp and (resp.get('retcode') == 0 or resp.get('retcode') == 10009):
                            if resp.get('retcode') == 10009:  # Order executed notification
                                logger.debug(f"Order executed: {resp}")
                            else:
                                logger.info(f"Order response: {resp}")
                            if market.get('position_manager'):
                                market['position_manager'].positions[self.symbol] = resp.get('order')
                            break
                            
                        # Handle requote (10004)
                        if resp and resp.get('retcode') == 10004:
                            # Calculate price difference
                            price_diff = abs(resp['price'] - order['price'])
                            
                            # Accept price within tolerance (0.1%)
                            if price_diff / order['price'] < 0.001:
                                order['price'] = resp['price']
                                logger.warning(f"Requote accepted (attempt {attempt+1}/{MAX_RETRIES})")
                                continue
                            
                            logger.warning(f"Requote rejected (price diff: {price_diff:.4f})")
                            
                        # Log other errors and break
                        if resp and resp.get('retcode') not in [0, 10004, 10009]:  # Skip already handled codes
                            logger.error(f"Order failed with code {resp.get('retcode')}: {resp}")
                        break
                    
                    if market.get("reporting_enabled", True):
                        self._record_entry_artifacts(
                            response=resp,
                            order_type="sell",
                            trend=trend,
                            rates_higher=rates_higher,
                            rates_trading=rates_trading,
                            rates_entry=rates_entry,
                            tf_higher=tf_higher,
                            tf_trading=tf_trading,
                            tf_entry=tf_entry,
                            rate_fetcher=market['rate_fetcher'],
                        )
        else:
            logger.debug(f"Skipping {self.symbol} - invalid stochastic values on one or more timeframes")


    def _record_entry_artifacts(
        self,
        *,
        response,
        order_type,
        trend,
        rates_higher,
        rates_trading,
        rates_entry,
        tf_higher,
        tf_trading,
        tf_entry,
        rate_fetcher,
    ):
        """Persist live analytics after a signal without affecting execution."""

        lookback = 10
        count_candle_pattern(rates_entry, is_doji, lookback)
        count_candle_pattern(rates_entry, is_hammer, lookback)
        count_candle_pattern(rates_entry, is_shooting_star, lookback)

        from mamba2.crew.plotter import plot_rates

        output_dir = os.path.join(os.getcwd(), "backtest")
        position_ticket = response.get('order') or int(time.time())

        if self.use_higher_tf:
            plot_rates(
                rates_higher,
                tf_higher,
                self.symbol,
                output_dir,
                position_ticket,
            )
        plot_rates(
            rates_trading,
            tf_trading,
            self.symbol,
            output_dir,
            position_ticket,
        )
        plot_rates(
            rates_entry,
            tf_entry,
            self.symbol,
            output_dir,
            position_ticket,
        )

        from mamba2.crew.market_analyst import get_metrics

        get_metrics(
            position_ticket,
            self.symbol,
            rate_fetcher,
            tf_higher,
            tf_trading,
            tf_entry,
            10,
            10,
            10,
            order_type=order_type,
            trend=trend,
            include_higher_tf=self.use_higher_tf,
        )

    def _registered_lower_lows(self, rates):
        """Check if last 2 candles registered lower lows."""
        if len(rates) < 2:
            return False
        return (rates.iloc[-1]['low'] < rates.iloc[-2]['low'])