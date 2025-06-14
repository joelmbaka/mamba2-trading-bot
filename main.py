import asyncio
import json
import os
from pathlib import Path
import MetaTrader5 as mt5
from mamba2.broker import MT5Broker

class Bot:
    def __init__(self):
        self.broker = None
        self.cache_file = Path("bot_cache.json")
        self.cache = self._load_cache()
        self.running = False

    def _load_cache(self):
        """Load cached data from JSON file."""
        if not self.cache_file.exists():
            return {}
        
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load cache - {e}")
            return {}

    def _save_cache(self):
        """Save current cache to JSON file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except IOError as e:
            print(f"Warning: Failed to save cache - {e}")

    async def initialize(self):
        """Initialize the bot and MT5 connection."""
        self.broker = MT5Broker(
            login=93117167,
            password="B*8hZaYl",
            server="MetaQuotes-Demo"
        )
        
        if not self.broker.initialize():
            raise RuntimeError("Failed to initialize MT5 connection")
        
        # Log account info on startup
        account_info = self.broker.account_info()
        print(f"Bot started with account info: {account_info}")
        
        # Store account info in cache
        self.cache["last_account_info"] = account_info
        self._save_cache()
        
        self.running = True

    async def run(self):
        """Main bot event loop."""
        while self.running:
            # Main bot logic would go here
            await asyncio.sleep(1)

    async def shutdown(self):
        """Cleanup resources."""
        if self.broker:
            self.broker.shutdown()
        self._save_cache()
        self.running = False

async def main():
    bot = Bot()
    
    # Setup signal handler for Ctrl+C (Windows compatible)
    if os.name == 'nt':  # Windows
        try:
            import win32api
            def handle_signal(sig):
                asyncio.create_task(bot.shutdown())
            win32api.SetConsoleCtrlHandler(handle_signal, True)
        except ImportError:
            print("Warning: pywin32 not installed, using basic keyboard interrupt handling")
    else:  # Unix
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig,
                lambda: asyncio.create_task(bot.shutdown())
            )
    
    try:
        await bot.initialize()
        await bot.run()
    except asyncio.CancelledError:
        pass  # Expected during shutdown
    except Exception as e:
        print(f"Bot error: {e}")
    finally:
        await bot.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
