import matplotlib
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
import os
import logging

# Use non-interactive backend to prevent memory leaks when running in background
matplotlib.use('Agg')  # Use 'Agg' backend which doesn't display figures

logger = logging.getLogger(__name__)

def plot_candles(rates: pd.DataFrame, symbol: str, timeframe: str, lookback: int = 10, save_path: str = None, ema_period: int = None):
    """
    Plot candlestick chart for given trading data with optional EMA.
    
    Args:
        rates (pd.DataFrame): Pre-fetched OHLCV data with datetime index
        symbol (str): Trading symbol (e.g. 'BTC/USD')
        timeframe (str): Chart timeframe (e.g. '1h', '4h', '1d')
        lookback (int): Number of candles to display (default: 10)
        save_path (str): Optional path to save the plot image (e.g. 'plots/btc_1h.png')
        ema_period (int, optional): Period for EMA calculation. If None, no EMA is plotted.
    """
    try:
        # Ensure we have the required columns
        required_cols = ['open', 'high', 'low', 'close']
        if not all(col in rates.columns for col in required_cols):
            raise ValueError("DataFrame must contain OHLC columns")
        
        # Slice to the most recent candles
        data = rates.iloc[-lookback:].copy()
        
        # Calculate EMA if period is specified
        if ema_period is not None and len(data) >= ema_period:
            data['ema'] = data['close'].ewm(span=ema_period, adjust=False).mean()
        
        # Rename columns to match mplfinance expectations
        data.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }, inplace=True)
        
        # Create additional plots for indicators
        apds = []
        
        # Add EMA to the plot if it exists
        if 'ema' in data.columns:
            apds.append(
                mpf.make_addplot(data['ema'], color='blue', width=1.0, panel=0, 
                               secondary_y=False, title=f'EMA{ema_period}' if ema_period else 'EMA')
            )
        
        # Plot configuration
        plot_kwargs = {
            'type': 'candle',
            'volume': 'volume' in data.columns,  # Only plot volume if data is available
            'title': f'{symbol} - {timeframe}',
            'style': 'charles',
            'figratio': (19, 10),  # 19:10 aspect ratio
            'figscale': 1.2,  # Scale up the figure
            'returnfig': True  # Return the figure and axes for further manipulation
        }
        # Only add the 'addplot' parameter if we have additional plots
        if apds:
            plot_kwargs['addplot'] = apds
        
        if save_path:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plot_kwargs['savefig'] = save_path
        
        # Create the plot
        fig, axlist = mpf.plot(data, **plot_kwargs)
        
        # Save the figure if path is provided
        if save_path:
            fig.savefig(save_path, dpi=100, bbox_inches='tight')
        
        # Close the figure to free memory
        plt.close(fig)
        
    except Exception as e:
        print(f"Error in plot_candles: {str(e)}")
        raise

def plot_rates(rates, timeframe, symbol, output_dir, position_ticket=None):
    """
    Plot rates and save the figure to the specified output directory.
    
    Args:
        rates: Either a pandas DataFrame or list of rate objects
        timeframe: Timeframe string (e.g., '1h', '4h')
        symbol: Trading symbol (e.g., 'BTC/USD')
        output_dir: Base directory to save the plots (e.g., 'backtest')
        position_ticket: Position ticket to create a subdirectory (required)
    
    Returns:
        str: Path to the saved plot
    """
    try:
        if position_ticket is None:
            raise ValueError("position_ticket is required")
            
        # Create position-specific directory under backtest
        try:
            output_dir = os.path.join(os.getcwd(), "backtest", str(position_ticket))
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Creating plots directory: {output_dir}")
            logger.info(f"Current working directory: {os.getcwd()}")
            logger.info(f"Directory exists: {os.path.exists(output_dir)}")
        except Exception as e:
            logger.error(f"Error creating directory {output_dir}: {str(e)}")
            raise
            
        if not isinstance(rates, pd.DataFrame):
            # Convert list of objects to DataFrame
            rates = pd.DataFrame([{
                'open': r.open,
                'high': r.high,
                'low': r.low,
                'close': r.close,
                'volume': getattr(r, 'volume', 0)  # Add volume if available
            } for r in rates])
        
        # Ensure we have the required columns
        required_cols = ['open', 'high', 'low', 'close']
        if not all(col in rates.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain OHLC columns. Found: {list(rates.columns)}")
            
        # Generate filename with safe characters
        safe_symbol = symbol.replace('/', '_')
        safe_timeframe = str(timeframe).replace('/', '_')
        filename = os.path.join(output_dir, f"{safe_symbol}_{safe_timeframe}.png")
        
        # Plot and save the figure with 10 lookback periods and EMA7 for 1-minute timeframe
        plot_candles(
            rates=rates,
            symbol=symbol,
            timeframe=timeframe,
            lookback=10,  # Show last 10 candles
            save_path=filename,
            ema_period=7 if str(timeframe).lower() == 'm1' else None  # Add EMA7 for 1-minute timeframe
        )
        
        return filename
        
    except Exception as e:
        print(f"Error in plot_rates: {str(e)}")
        raise
    finally:
        # Ensure all figures are closed
        plt.close('all')