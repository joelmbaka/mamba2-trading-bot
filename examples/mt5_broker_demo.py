"""Read-only MT5 broker demo using environment-provided credentials.

Required environment variables:
- MAMBA_MT5_LOGIN
- MAMBA_MT5_PASSWORD
- MAMBA_MT5_SERVER

The demo only reads account/market information and does not submit orders.
"""

from config import mt5 as mt5_config
from mamba2.broker import MT5Broker


def main():
    required = {
        "MAMBA_MT5_LOGIN": mt5_config.login,
        "MAMBA_MT5_PASSWORD": mt5_config.password,
        "MAMBA_MT5_SERVER": mt5_config.server,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise SystemExit(
            "Missing MT5 environment variables: " + ", ".join(missing)
        )

    print("Initializing MT5 broker...")
    broker = MT5Broker(
        path=mt5_config.path,
        login=mt5_config.login,
        password=mt5_config.password,
        server=mt5_config.server,
        timeout=mt5_config.timeout,
        portable=mt5_config.portable,
    )

    try:
        if not broker.initialize():
            print("Failed to initialize MT5 connection")
            return

        print("\n=== Account Information ===")
        account = broker.account_info()
        print(f"Account: {account.get('login')}")
        print(f"Balance: {account.get('balance')} {account.get('currency')}")
        print(f"Equity: {account.get('equity')} {account.get('currency')}")
        print(f"Server: {account.get('server')}")

        symbol = "EURUSD"
        print(f"\n=== Market Data for {symbol} ===")
        if not broker.symbol_select(symbol):
            print(f"Failed to select {symbol}")
            return

        print("\nFetching historical data...")
        bars = broker.copy_rates_from_pos(symbol, 1, 0, 5)

        print("\nLast 5 M1 bars:")
        for index, bar in enumerate(bars, start=1):
            print(
                f"Bar {index}: Time={bar['time']}, O={bar['open']}, "
                f"H={bar['high']}, L={bar['low']}, C={bar['close']}"
            )

        print("\n=== Open Positions ===")
        print(f"Open positions: {broker.positions_total()}")

    finally:
        print("\nShutting down MT5 connection...")
        broker.shutdown()


if __name__ == "__main__":
    main()
