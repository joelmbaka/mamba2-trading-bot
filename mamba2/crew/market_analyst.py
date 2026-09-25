import pandas as pd
import os
from datetime import datetime
import logging
import numpy as np
from mamba2.indicators.stochastic import get_stochastic
from mamba2.indicators.candles import is_doji, is_hammer, is_shooting_star
from mamba2.indicators import RSI

def count_candle_pattern(candles, pattern_type, lookback=None):
    """
    Count occurrences of a specific candle pattern in a list of candles.
    
    Args:
        candles: pandas DataFrame or list of dictionaries containing OHLC data
        pattern_type: Either a string ('doji', 'hammer', 'shooting_star') or a pattern function
        lookback: (Optional) Number of candles to look back. If None, checks all candles.
        
    Returns:
        int: Count of matching patterns
    """
    import pandas as pd
    
    # Convert DataFrame to list of dicts if needed
    if isinstance(candles, pd.DataFrame):
        if lookback is not None:
            candles = candles.tail(lookback)
        candles_list = candles.to_dict('records')
    else:
        if lookback is not None and len(candles) > lookback:
            candles_list = candles[-lookback:]
        else:
            candles_list = candles
    
    if callable(pattern_type):
        # If pattern_type is a function (like is_doji), use it directly
        return sum(1 for candle in candles_list if pattern_type(candle))
    else:
        # If pattern_type is a string, use the corresponding function
        count = 0
        for candle in candles_list:
            if pattern_type == 'doji' and is_doji(candle):
                count += 1
            elif pattern_type == 'hammer' and is_hammer(candle):
                count += 1
            elif pattern_type == 'shooting_star' and is_shooting_star(candle):
                count += 1
        return count


def get_metrics(position_ticket: str, symbol: str, rate_fetcher, 
                tf_higher: str, tf_trading: str, tf_entry: str, 
                lookback_period_higher: int, lookback_period_trading: int, lookback_period_entry: int, 
                order_type: str = "", trend: str = None,
                include_higher_tf: bool = True) -> str:
    """
    Calculate and save market metrics across multiple timeframes to a centralized CSV
    
    Args:
        position_ticket: Order ID or timestamp used as position identifier
        symbol: Trading symbol
        rate_fetcher: RateFetcher instance for cached rates
        tf_higher: Higher timeframe string
        tf_trading: Trading timeframe string
        tf_entry: Entry timeframe string
        lookback_period_higher: Lookback period for higher timeframe
        lookback_period_trading: Lookback period for trading timeframe
        lookback_period_entry: Lookback period for entry timeframe
        order_type: Type of order ("buy" or "sell")
        trend: Detected trend ("uptrend" or "downtrend")
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Create backtest directory if it doesn't exist
        output_dir = os.path.join(os.getcwd(), "backtest")
        logger.info(f"Ensuring backtest directory exists: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)
        
        # Centralized CSV file path
        csv_path = os.path.join(output_dir, "market_metrics.csv")
        logger.info(f"Using centralized CSV file: {csv_path}")
        
        # Get stochastics for each timeframe (use same parameters as in strategy)
        logger.info(f"Getting stochastics for {symbol} - Higher TF: {tf_higher}, Trading TF: {tf_trading}, Entry TF: {tf_entry}")
        
        stoch_higher = (
            get_stochastic(
                symbol,
                tf_higher,
                lookback_period=lookback_period_higher,
                rate_fetcher=rate_fetcher,
            )
            if include_higher_tf
            else None
        )
        stoch_trading = get_stochastic(symbol, tf_trading, lookback_period=lookback_period_trading, rate_fetcher=rate_fetcher)
        stoch_entry = get_stochastic(symbol, tf_entry, lookback_period=lookback_period_entry, rate_fetcher=rate_fetcher)
        
        # Get RSI for 5-minute timeframe
        rsi_5m = RSI.get_rsi(symbol, 'M5', rate_fetcher=rate_fetcher)

        # Helper function to safely convert series to list
        def safe_tolist(series):
            """Safely convert a pandas Series to list, handling empty series."""
            return series.tolist() if not series.empty else []
            
        # Helper function to count consecutive consistent periods
        def count_consecutive_consistency(k_list, d_list):
            """Count consecutive periods where K > D or D > K."""
            if not k_list or not d_list:
                return 0
                
            # Determine trend direction (most recent period)
            current_trend = "up" if k_list[-1] > d_list[-1] else "down"
            count = 0
            
            # Count backwards from current period
            for i in range(len(k_list)-1, -1, -1):
                if current_trend == "up" and k_list[i] > d_list[i]:
                    count += 1
                elif current_trend == "down" and d_list[i] > k_list[i]:
                    count += 1
                else:
                    break
            return count
            
        # Helper function to get the latest %K value
        def get_latest_k(stoch_data):
            """Safely get the latest %K value, rounded to 2 decimal places"""
            if stoch_data and not stoch_data['k'].empty:
                return round(stoch_data['k'].iloc[-1], 2)
            return None
            
        # Prepare DataFrame row
        
        data = {
            'ticket': position_ticket,
            'entry_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': symbol,
            'order_type': order_type,  
            '15min_trendline': trend,  
          #  'higher_tf_k': get_latest_k(stoch_higher),
            'trading_tf_k': get_latest_k(stoch_trading),
            'entry_tf_k': get_latest_k(stoch_entry),
            'rsi_5m': round(rsi_5m, 2) if rsi_5m is not None else None,
           # 'higher_tf_consistency': count_consecutive_consistency(
           #     safe_tolist(stoch_higher['k']) if stoch_higher else [],
           #     safe_tolist(stoch_higher['d']) if stoch_higher else []
           # ),
            'trading_tf_consistency': count_consecutive_consistency(
                safe_tolist(stoch_trading['k']) if stoch_trading else [],
                safe_tolist(stoch_trading['d']) if stoch_trading else []
            ),
            'entry_tf_consistency': count_consecutive_consistency(
                safe_tolist(stoch_entry['k']) if stoch_entry else [],
                safe_tolist(stoch_entry['d']) if stoch_entry else []
            ),
            'pl': None,  
            'close_time': None,  
            'unfilled': True,  
            # Candle pattern counting for entry timeframe
            'doji_count': count_candle_pattern(rate_fetcher.get_rates(symbol, tf_entry), 'doji', lookback=10) \
                if rate_fetcher and hasattr(rate_fetcher, 'get_rates') and isinstance(rate_fetcher.get_rates(symbol, tf_entry), pd.DataFrame) \
                else 0,
            'hammer_count': count_candle_pattern(rate_fetcher.get_rates(symbol, tf_entry), 'hammer', lookback=10) \
                if rate_fetcher and hasattr(rate_fetcher, 'get_rates') and isinstance(rate_fetcher.get_rates(symbol, tf_entry), pd.DataFrame) \
                else 0,
            'shooting_star_count': count_candle_pattern(rate_fetcher.get_rates(symbol, tf_entry), 'shooting_star', lookback=10) \
                if rate_fetcher and hasattr(rate_fetcher, 'get_rates') and isinstance(rate_fetcher.get_rates(symbol, tf_entry), pd.DataFrame) \
                else 0,

        }
        
        # Create DataFrame from single row
        new_row = pd.DataFrame([data])
        
        # Append to centralized CSV
        if os.path.exists(csv_path):
            # Read existing CSV and append new row
            existing_df = pd.read_csv(csv_path)
            updated_df = pd.concat([existing_df, new_row], ignore_index=True)
            updated_df.to_csv(csv_path, index=False)
            logger.info(f"Appended market data to {csv_path}")
        else:
            # Create new file with header
            new_row.to_csv(csv_path, index=False)
            logger.info(f"Created new market file at {csv_path}")
        
        logger.info(f"Successfully saved market data to {csv_path}")
        return csv_path
        
    except Exception as e:
        logger.error(f"Error in get_metrics: {str(e)}", exc_info=True)
        # Try to save error information
        try:
            error_path = os.path.join(output_dir, f"error_{position_ticket}.txt")
            with open(error_path, 'w') as f:
                f.write(f"Error processing market data for {symbol} at {datetime.now()}\n")
                f.write(f"Error: {str(e)}\n")
            logger.info(f"Saved error details to {error_path}")
        except Exception as save_error:
            logger.error(f"Failed to save error details: {str(save_error)}")
        raise
