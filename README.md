# Mamba2 - Algorithmic Trading Framework

Mamba2 is a Python-based algorithmic trading framework designed for backtesting and live trading with MetaTrader 5. The framework provides a clean, type-hinted API for developing, testing, and deploying trading strategies.

## Features

- **Unified Broker Interface**: Common interface for both live and mock trading
- **MT5 Integration**: Seamless integration with MetaTrader 5
- **Mock Trading**: Full-featured mock implementation for testing strategies without a live account
- **Type Hints**: Full Python type hint support for better IDE assistance and code quality
- **Testing**: Comprehensive test suite with unit and integration tests

## Installation

1. Install Python 3.8+
2. Install the package in development mode:
   ```bash
   git clone <repository-url>
   cd mamba2
   uv pip install -e .
   ```
3. For MT5 support, install the MetaTrader5 package:
   ```bash
   uv pip install MetaTrader5
   ```

## Quick Start

```python
from mamba2.broker import MT5Broker, MT5Mock

# For live trading
broker = MT5Broker(login=YOUR_LOGIN, password="YOUR_PASSWORD", server="YOUR_SERVER")

# For testing/development
mock_broker = MT5Mock()

# Initialize connection
if broker.initialize():
    try:
        # Get account info
        account = broker.account_info()
        print(f"Account: {account['login']} Balance: {account['balance']}")
        
        # Example: Get market data
        if broker.symbol_select("EURUSD"):
            bars = broker.copy_rates_from_pos("EURUSD", 1, 0, 10)  # Last 10 M1 bars
            print(f"Got {len(bars)} bars of EURUSD data")
            
    finally:
        broker.shutdown()
```

## Project Structure

- `mamba2/` - Core package
  - `broker/` - Broker interface and implementations
    - `base.py` - Abstract base class for all brokers
    - `mt5_broker.py` - MT5 live trading implementation
    - `mt5_mock.py` - Mock implementation for testing
  - `strategy/` - Strategy interfaces and base classes
  - `trader/` - Trading client and execution logic
- `tests/` - Test suite
  - `unit/` - Unit tests
  - `integration/` - Integration tests
- `examples/` - Example scripts and strategies

## Project Status

### ✅ Completed

- **Core Infrastructure**
  - [x] Package structure and module organization
  - [x] Test infrastructure with pytest
  - [x] CI/CD pipeline

- **Broker Implementation**
  - [x] `Broker` abstract base class
  - [x] `MT5Broker` - Live trading with MetaTrader 5
  - [x] `MT5Mock` - Mock implementation for testing
  - [x] Comprehensive test coverage
  - [x] Example usage scripts

- **Documentation**
  - [x] API documentation
  - [x] Usage examples
  - [x] Developer guide

### 🚧 In Progress

- **Backtesting Engine**
  - [ ] Historical data processing
  - [ ] Strategy performance metrics
  - [ ] Optimization framework

- **Strategy Development**
  - [ ] Built-in technical indicators
  - [ ] Risk management tools
  - [ ] Performance analytics

### 📅 Planned

- **Live Trading**
  - [ ] Paper trading mode
  - [ ] Risk management system
  - [ ] Performance monitoring

- **Advanced Features**
  - [ ] Machine learning integration
  - [ ] Multi-timeframe analysis
  - [ ] Web dashboard

## Getting Involved

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on how to get started.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.