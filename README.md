My name is Joel, and i am a software engineer
this is a new project i have just started called Mamba2
it is an algorithmic trading project
i am using uv package manager to manage python packages, metatrader 5 and pytest 
i am still in development stage
i already have established a reliable trading strategy that i want to backtest and implement in this project
this is how i want it to work:
1. use pytest to create a mock mt5 server which will give us access to the mt5 functions like symbol selection, tick data, candles, order sending, position management etc.
2. implement a client who is a trader and who can import functions from any modules they want and take action i.e execute orders, manage positions etc. when certain conditions are met. this will e like the real application that we are building
3. scaffold initial package and tests

## Project TODO Checklist

- [x] Scaffold core package (`mamba2`) and submodules
  - [x] `broker.mt5_mock` – mock MetaTrader5 API
  - [x] `strategy.base` – strategy interface
  - [x] `trader.client` – trading client
- [x] Test infrastructure
  - [x] `tests/conftest.py` & unit tests
- [x] Example user strategy
- [ ] Broker abstraction
  - [ ] Define `Broker` ABC in `broker/base.py`
  - [ ] Implement real MT5 broker adapter
  - [ ] Make `MT5Mock` implement the `Broker` interface
- [ ] Back-testing engine
  - [ ] Event loop for historical data
  - [ ] Virtual order execution
  - [ ] PnL and metrics tracking
- [ ] Configuration & CLI
  - [ ] Pydantic settings for config
  - [ ] CLI for running strategies
  - [ ] Support for different modes (backtest, paper, live)
- [ ] Extended test suite
  - [ ] Unit tests for broker implementations
  - [ ] Property-based tests
  - [ ] Integration tests with small datasets
- [ ] Tooling & CI
  - [ ] Linting (ruff, black) config
  - [ ] Pre-commit hooks
  - [ ] GitHub Actions workflow
- [ ] Documentation
  - [ ] Comprehensive README
  - [ ] Usage examples
  - [ ] API documentation