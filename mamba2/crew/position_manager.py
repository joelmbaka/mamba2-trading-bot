"""Position manager for handling open positions and trailing stops."""
import os
import asyncio
import time  # Added for timestamp functionality
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from mamba2.crew.logger import logger
from mamba2.crew.atr_manager import ATRManager

# Import configuration
from config import config

# Trade action constants
TRADE_ACTION_SLTP = 2
TRADE_RETCODE_DONE = 10009  # MT5 success code


class PositionManager:
    """Manages open positions and implements trailing stop functionality."""
    
    def __init__(self, broker, atr_manager: ATRManager = None, rates_fetcher=None):
        """Initialize with broker and optional ATR manager."""
        self.broker = broker
        self.atr_manager = atr_manager  # Store instance
        self.rates_fetcher = rates_fetcher  # Store rates fetcher
        self.running = False
        self.positions = {}  # Initialize positions dictionary
    
    async def update_trailing_stops(self):
        """Update trailing stops during the live wall-clock loop."""
        if not self.running:
            return

        if self.atr_manager:
            timeout = 30
            start_time = time.time()
            while not self.atr_manager.is_ready() and self.running:
                if time.time() - start_time > timeout:
                    logger.error("ATR manager not ready after 30 seconds")
                    break
                logger.debug("Waiting for ATR manager to initialize...")
                await asyncio.sleep(1)

        await self.update_once()

    async def update_once(self):
        """Run one production position-management cycle without sleeping.

        This is the deterministic entry point used by historical replay. Any
        stop/target change calculated from a just-completed candle therefore
        applies from the following candle onward.
        """

        try:
            positions = await self.broker.positions_get()
            if not positions:
                logger.trace("No open positions to update")
                return
                
#            logger.debug(f"Updating trailing stops for {len(positions)} positions")
            for position in positions:
                # Extract position details
                ticket = position['ticket']
                symbol = position['symbol']
                position_type = position['type']  # 0 for buy, 1 for sell
                current_price = position['price_current']
                stop_loss = position['sl']
                take_profit = position['tp']
                
                # If no stop loss or take profit is set, calculate SL/TP based on ATR.
                if stop_loss == 0 or take_profit == 0:
                    if not self.atr_manager:
                        self.positions[symbol] = position
                        continue

                    logger.trace(
                        f"No SL/TP set for position {ticket}, getting ATR-based levels"
                    )
                    timeframe = getattr(config, 'atr_timeframe', 'M5')
                    atr = self.atr_manager.get_atr(symbol, timeframe)

                    # A replay boundary can legitimately arrive before enough
                    # completed M5 history exists for ATR. Keep the position
                    # untouched until a positive ATR becomes available.
                    if atr is None or atr <= 0:
                        self.positions[symbol] = position
                        continue

                    # Initial stop protection remains anchored to
                    # the current closing-side price, preserving the accepted
                    # live/replay behavior and broker-valid stop direction.
                    #
                    # The existing target calculation is also preserved unless
                    # a wide spread would put TP at or beyond the wrong side of
                    # the actual entry fill. In that defect case only, anchor
                    # TP to the fill so a take-profit cannot realize a loss
                    # solely because Bid/Ask spread exceeded the ATR target
                    # distance.
                    open_price = float(position["price_open"])
                    if position_type == 0:  # Buy position
                        stop_loss = current_price - (
                            atr * config.atr_sl_multiplier
                        )
                        take_profit = current_price + (
                            atr * config.atr_tp_multiplier
                        )
                        if take_profit <= open_price:
                            take_profit = open_price + (
                                atr * config.atr_tp_multiplier
                            )
                    else:  # Sell position
                        stop_loss = current_price + (
                            atr * config.atr_sl_multiplier
                        )
                        take_profit = current_price - (
                            atr * config.atr_tp_multiplier
                        )
                        if take_profit >= open_price:
                            take_profit = open_price - (
                                atr * config.atr_tp_multiplier
                            )

                    logger.debug(
                        f"Calculated initial SL/TP for {symbol}: "
                        f"Open={open_price:.5f}, Current={current_price:.5f}, "
                        f"ATR={atr:.5f}, SL={stop_loss:.5f}, "
                        f"TP={take_profit:.5f}"
                    )
                    success = await self._update_position_sl(
                        position,
                        stop_loss,
                        take_profit,
                    )
                    if success:
                        logger.trace(
                            f"Successfully set ATR-based SL/TP for position {ticket}"
                        )
                    self.positions[symbol] = position
                    continue

                # Existing protected positions may be trailed only when a
                # positive ATR is currently available.
                if self.atr_manager:
                    atr = self.atr_manager.get_atr(
                        symbol,
                        getattr(config, 'atr_timeframe', 'M5'),
                    )
                    if atr is not None and atr > 0:
                        if position_type == 0:
                            near_target = (
                                take_profit - current_price
                            ) < (1 / 3) * (take_profit - stop_loss)
                            if near_target:
                                new_sl = current_price - (
                                    atr * config.atr_sl_multiplier
                                )
                                new_tp = current_price + (
                                    atr * config.atr_tp_multiplier
                                )
                                if self._is_more_protective_stop(
                                    position_type,
                                    current_sl=stop_loss,
                                    candidate_sl=new_sl,
                                ):
                                    await self._update_position_sl(
                                        position,
                                        new_sl,
                                        new_tp,
                                    )
                        else:
                            near_target = (
                                current_price - take_profit
                            ) < (1 / 3) * (stop_loss - take_profit)
                            if near_target:
                                new_sl = current_price + (
                                    atr * config.atr_sl_multiplier
                                )
                                new_tp = current_price - (
                                    atr * config.atr_tp_multiplier
                                )
                                if self._is_more_protective_stop(
                                    position_type,
                                    current_sl=stop_loss,
                                    candidate_sl=new_sl,
                                ):
                                    await self._update_position_sl(
                                        position,
                                        new_sl,
                                        new_tp,
                                    )

                self.positions[symbol] = position
        
        except Exception as e:
            logger.error(f"Error in update_trailing_stops: {str(e)}")
            logger.opt(exception=e).error("Exception details:")
    
   
    @staticmethod
    def _is_more_protective_stop(
        position_type: int,
        *,
        current_sl: float,
        candidate_sl: float,
    ) -> bool:
        """Return whether a trailing stop moves strictly toward protection.

        BUY stops may only move upward. SELL stops may only move downward.
        Equality is intentionally rejected so an existing stop is never
        rewritten without improving protection.
        """
        if position_type == 0:
            return candidate_sl > current_sl
        return candidate_sl < current_sl

    async def _update_position_sl(self, position: dict, new_sl: float, new_tp: float) -> Optional[bool]:
        """Update the stop loss and take profit of a position."""
        try:
            # Get the current stop loss and take profit
            current_sl = position['sl']
            current_tp = position['tp']
            
            # Calculate the minimum change (in price) for 1 pip
            point = self.broker.get_point_size(position['symbol'])
            min_change = 1.5 * point  # 1 pip
            
            # Check if the changes are too small
            if abs(new_sl - current_sl) < min_change and abs(new_tp - current_tp) < min_change:
                logger.debug(f"Skipping update for position {position['ticket']} because changes are too small")
                return None
            
            # Call order_modify with the position ticket and new SL/TP values
            result = await self.broker.order_modify(
                ticket=position['ticket'],
                sl=new_sl,
                tp=new_tp
            )
            
            if not result or 'retcode' not in result:
                logger.error(f"Invalid response from broker when updating position {position['ticket']}")
                return False
                
            # MT5 returns 10009 (TRADE_RETCODE_DONE) on success
            if result['retcode'] not in [0, 10009]:
                error_msg = result.get('comment', 'Unknown error')
                logger.error(f"Failed to update SL/TP for position {position['ticket']}: {error_msg}")
                logger.debug(f"Broker response: {result}")
                return False
                
            logger.success(f"Successfully updated position {position['ticket']} (SL={new_sl:.5f}, TP={new_tp:.5f})")
            return True
            
        except Exception as e:
            logger.error(f"Exception when updating position {position['ticket']}: {str(e)}")
            logger.opt(exception=e).debug("Exception details:")
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
        """Run the position manager's main loop."""
        self.running = True
        logger.info("🚀 Position manager started")
        
       
        try:
            while self.running:
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
            raise
        except Exception as e:
            logger.error("Unexpected error in position manager")
            logger.opt(exception=e).error("Error details:")
            await asyncio.sleep(5)  # Wait before retrying
        
        logger.info("🛑 Position manager stopped")
    
    async def stop(self):
        """Stop the position manager."""
        logger.info("🛑 Stopping position manager...")
        self.running = False
        
        # Clear positions cache
        self.positions.clear()
        logger.debug("Cleared positions cache")
        
        logger.info("Position manager stopped")