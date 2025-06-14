"""Position manager for handling open positions and trailing stops."""
import asyncio
from typing import Dict, Any, Optional

from mamba2.crew.logger import logger
from mamba2.crew.atr_manager import ATRManager

# Import configuration
from config import config

# Trade action constants
TRADE_ACTION_SLTP = 2
TRADE_RETCODE_DONE = 10009  # MT5 success code

class PositionManager:
    """Manages open positions and implements trailing stop functionality."""
    
    def __init__(self, broker, atr_manager: ATRManager = None):
        """Initialize with broker and optional ATR manager."""
        self.broker = broker
        self.atr_manager = atr_manager  # Store instance
        self.running = False
        self.positions = {}  # Initialize positions dictionary
    
    async def update_trailing_stops(self):
        """Update trailing stop losses for all open positions."""
        try:
            positions = self.broker.positions_get()
            if not positions:
                logger.trace("No open positions to update")
                return
                
            logger.debug(f"Updating trailing stops for {len(positions)} positions")
            for position in positions:
                # Extract position details
                ticket = position['ticket']
                symbol = position['symbol']
                position_type = position['type']  # 0 for buy, 1 for sell
                current_price = position['price_current']
                stop_loss = position['sl']
                take_profit = position['tp']
                
                # If no stop loss is set, calculate SL/TP based on ATR
                if stop_loss == 0 and self.atr_manager:
                    logger.trace(f"No SL set for position {ticket}, getting ATR-based SL/TP")
                    
                    # Get ATR value using the configured timeframe (default 'M5')
                    timeframe = getattr(config, 'atr_timeframe', 'M5')
                    atr = self.atr_manager.get_atr(symbol, timeframe)
                    
                    if atr is not None and atr > 0:
                        current_price = position['price_open']  # Use entry price for new positions
                        if position_type == 0:  # Buy position
                            stop_loss = current_price - (atr * config.atr_sl_multiplier)
                            take_profit = current_price + (atr * config.atr_tp_multiplier)
                        else:  # Sell position
                            stop_loss = current_price + (atr * config.atr_sl_multiplier)
                            take_profit = current_price - (atr * config.atr_tp_multiplier)
                        
                        # Update the position with new SL/TP
                        logger.info(f"Setting ATR-based SL/TP for {symbol} position {ticket}: SL={stop_loss:.5f}, TP={take_profit:.5f}")
                        success = await self._update_position_sl(ticket, symbol, stop_loss, take_profit)
                        if success:
                            logger.trace(f"Successfully set ATR-based SL/TP for position {ticket}")
                        continue  # Skip trailing for this position as we just set initial SL/TP
                
                # Calculate pip value (approximate for non-forex pairs)
                pip_value = 0.0001 if '.' in str(current_price)[:2] else 0.01
                
                # Calculate new stop loss based on price movement
                if position_type == 0:  # Buy position
                    # For buy positions, trail stop loss below the price
                    new_sl = current_price - (config.trailing_stop_pips * pip_value)
                    min_sl = stop_loss + (config.trailing_step_pips * pip_value)
                    if new_sl > min_sl:  # Only move stop up
                        logger.trace(f"Updating BUY position {ticket} SL from {stop_loss:.5f} to {new_sl:.5f}")
                        success = await self._update_position_sl(ticket, symbol, new_sl, take_profit)
                        if not success:
                            logger.warning(f"Failed to update BUY position {ticket}")
                    else:
                        logger.trace(f"No SL update needed for BUY position {ticket} (current SL: {stop_loss:.5f}, new SL would be: {new_sl:.5f})")
                
                elif position_type == 1:  # Sell position
                    # For sell positions, trail stop loss above the price
                    new_sl = current_price + (config.trailing_stop_pips * pip_value)
                    max_sl = stop_loss - (config.trailing_step_pips * pip_value)
                    if new_sl < max_sl:  # Only move stop down
                        logger.trace(f"Updating SELL position {ticket} SL from {stop_loss:.5f} to {new_sl:.5f}")
                        success = await self._update_position_sl(ticket, symbol, new_sl, take_profit)
                        if not success:
                            logger.warning(f"Failed to update SELL position {ticket}")
                    else:
                        logger.trace(f"No SL update needed for SELL position {ticket} (current SL: {stop_loss:.5f}, new SL would be: {new_sl:.5f})")
                
                # Store the position in the dictionary
                self.positions[symbol] = position
        
        except Exception as e:
            logger.error(f"Error in update_trailing_stops: {str(e)}")
            logger.opt(exception=e).error("Exception details:")
    
    async def _update_position_sl(self, ticket: int, symbol: str, new_sl: float, take_profit: float):
        """Update the stop loss for a position."""
        try:
            logger.info(f"Updating position {ticket} ({symbol}): SL={new_sl:.5f}, TP={take_profit:.5f}")
            result = self.broker.order_modify(ticket, sl=new_sl, tp=take_profit)
            if result.retcode != TRADE_RETCODE_DONE:
                logger.error(f"Failed to update SL/TP for position {ticket}: {result.comment}")
                return False
            logger.success(f"Successfully updated position {ticket} (SL={new_sl:.5f}, TP={take_profit:.5f})")
            return True
        except Exception as e:
            logger.error(f"Error updating stop loss for position {ticket}")
            logger.opt(exception=e).error("Exception details:")
            return False
    
    def get_position(self, symbol: str):
        """Get the current position for a specific symbol.
        
        Args:
            symbol: The trading symbol (e.g. 'EURUSD')
            
        Returns:
            The position object if exists, None otherwise
        """
        return self.positions.get(symbol)
    
    async def run(self):
        """Run the position manager to update trailing stops."""
        self.running = True
        logger.info("🚀 Position manager started")
        
        while self.running:
            try:
                logger.trace("Starting position update cycle")
                await self.update_trailing_stops()
                logger.trace("Completed position update cycle")
                
                # Wait for 5 seconds before next update
                for i in range(5):
                    if not self.running:
                        logger.info("🛑 Position manager stopping...")
                        break
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                logger.warning("Position manager task cancelled")
                self.running = False
                break
            except Exception as e:
                logger.error("Unexpected error in position manager")
                logger.opt(exception=e).error("Error details:")
                await asyncio.sleep(5)  # Wait before retrying
        
        logger.info("🛑 Position manager stopped")
    
    def stop(self):
        """Stop the position manager."""
        if self.running:
            logger.info("🛑 Stopping position manager...")
            self.running = False