# Next Authorized Task

## M029 — Stage 3B preflight attempted; import-only smoke blocked by missing isolated runtime

Branch: `prospective-paper-recovery`. Do not merge or promote to `main`.

The frozen M029 operational contract remains:
`docs/milestones/029-stage3-operational-protocol.md`;
freeze SHA `c74ca08fe32bf9ac9954cee5b033f808f3932ddd`.

### Stage 3A accepted evidence (2026-11-12)

- Tested implementation HEAD:
  `50cc8dded6003fc6f7558263c8f5186cda796989`.
- Full native regression result:
  `bb68fab6c7e55543717a33b9a27fb788093d359f`
  on `local-control-results`.
- **382 passed, 2 skipped, 13 pre-existing warnings; zero failures.**
- Pure/mock adapter: `mamba2/backtest/m029_stage3a.py`.
- Tested direct UTC acquisition start/finish, immutable record final-clock
  refusal, window close during source/broker calls, quote tick in active
  window and <=300 seconds old, raw/normalized hashes, eight fixed symbols,
  projected buy/sell margins, symlink and corrupt journal refusal.
- No real publisher data, broker session, quote, signal, trade or live P/L was
  accessed. Tests only wrote synthetic records into temporary directories.
- Reported isolated Wine 11.21/Windows 11 terminal launch success is GUI
  evidence ONLY. Python MT5 import/broker API compatibility remains unknown.

### Stage 3B preflight evidence — 2026-11-12

The operator's next "go" authorized the **first Stage-3B read-only
environment preflight and import-only smoke test**, not a broker connection.

Two allowlisted workstation checks ran without invoking Wine/MT5:
- `mamba2-20261112-stage3b-isolated-preflight-v1` (result on
  `local-control-results` at `e97616f2200fd9ea9f717c40aff4069fb34ed3e2`):
  detected only system Wine 9.0, one older Windows 10 backup prefix,
  **no isolated Wine 11.21 binary or separate Python bridge** in the
  bounded standard candidate paths.
- `mamba2-20261112-stage3b-targeted-discovery-v1` (result on
  `local-control-results` at `219898b7d142ed32097e2831be9f46e59bd10dfa`):
  found no further Wine executable, isolated prefix, bridge Python or
  installed WineHQ package in the bounded locations checked. The search
  reached its **3,000-directory** limit and is **not exhaustive**.

**STATUS: BLOCKED AT ENVIRONMENT DISCOVERY.** The reported isolated Wine
11.21 GUI test is not disputed, but its binary and prefix locations are not
yet established in the current local-agent environment. No Python import
was attempted; no broker/data tests were performed.

Do not silently fall back to Wine 9.0, the original `~/.mt5` prefix or
`.venv-wine`. The next step is to obtain the actual isolated Wine 11.21
executable path and isolated prefix directory, and establish whether a
separate Python 3.10 interpreter exists there. If the ephemeral test
environment was deleted, a separately isolated bridge must be recreated
before any import check.

### Next gate — Stage 3B, import-only smoke not yet executed

Once the isolated runtime paths are established, the remaining sequence is
**bounded and read-only**, stopping on any unsuccessful step. The user's
current authorization covers environment preflight/import-only, not broker
initialization or quote/margin reads:

1. **Environment preflight:** inspect only isolated Wine 11.21 Staging and
   copied Windows 11 compatibility prefix, separate bridge interpreter and
   accepted package pins; do not modify original `~/.mt5`, system Wine 9.0,
   existing `.venv-wine` / `.venv-native-control`, or project strategy.
2. **Import-only smoke:** launch isolated bridge Python and import
   `MetaTrader5` without `initialize`, account login, broker connection,
   order checks, account reads or data downloads. Record version/error class
   only, never secrets.
3. **Real broker connectivity** only if separately authorized for a suitable
   isolated demo session with no copied credentials: fixed, allowlisted
   `symbol_info`, `symbol_info_tick`, and `order_calc_margin` for eight
   frozen direct-USD symbols. No `symbol_select`, positions, history,
   `account_info`, `order_check`, `order_send` or live actions.
4. **Fixed-source metadata readiness** only if separately approved: inspect
   BIS XRU/OECD IR3TIB source cutoff dates and SHA-256, no formation signs,
   no target lots, no strategy economics; confirm actual acquisition timestamps
   and source publication metadata when available.
5. Capture deterministic/filtered evidence and close Stage 3B before
   considering Stage 3C. Do not silently turn a read-only check into paper
   decision or scheduler activation.

### Stage 3C — NOT AUTHORIZED

No live-source trading signal, paper record, broker position or scheduled
decision. The first potentially eligible paper window remains
**2026-12-07T12:00:00Z** to strictly before **12:10:00Z**
(15:00–15:10 EAT); this is not an enabled automation. Missing that
window permanently forbids reconstruction. October and November were
already missed; never backfill.

Retain M027/M028 fixed strategy and eight currencies, unknown actual
commission/slippage/swap, and the minimum **12 completed prospective**
paper holding periods before a performance conclusion. Neither live trading
nor net executable profitability is supported.
