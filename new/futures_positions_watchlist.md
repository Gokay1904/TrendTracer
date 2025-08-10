# Binance Futures Positions Watchlist Implementation

This update adds a special watchlist that pulls and displays your active Binance Futures positions directly from the API.

## Features Added:

1. Special "Futures Positions" watchlist that automatically fetches your active futures positions
2. Position details including position type (LONG/SHORT), leverage, and current prices
3. Visual indicators for position types (green for LONG, red for SHORT)
4. Quick access button in the portfolio tab and menu item in the View menu
5. Automatic updates whenever data is refreshed

## Changes Made:

### BinanceService (binance_service.py)
- Added `get_futures_positions()` method to fetch active futures positions from Binance
- Retrieves position data including position amount, symbol, leverage, and mark price
- Handles API authentication and error cases

### Asset Model (asset.py)
- Added new futures-specific fields:
  - `is_long` and `is_short` flags to indicate position type
  - `leverage` to store the position's leverage multiplier
  - `unrealized_pnl` to track profit/loss
- Added serialization support for the new fields
- Added a new `position_type` property that returns "LONG" or "SHORT"

### Portfolio Model (portfolio.py)
- Added a special "Futures Positions" watchlist that's always available
- Modified serialization to not persist the futures positions watchlist (it's refreshed from API)
- Added tracking for when futures positions were last updated

### PortfolioManager (portfolio_manager.py)
- Added `update_futures_positions()` method to refresh the futures positions watchlist
- Synchronizes futures position data with the watchlist and asset models
- Updates asset properties with position details (leverage, position type)

### UI Changes
- Added a "Futures Positions" filter option in the portfolio tab
- Added a dedicated button for quick access to futures positions
- Extended the asset display to show position type and leverage
- Added color coding (green for long positions, red for short positions)
- Added a menu item in the View menu to access futures positions

### MainWindow (main_window.py)
- Added menu item for futures positions in View menu
- Added futures positions refresh to data refresh flow
- Added method to quickly navigate to futures positions view

## Usage:
1. Configure your Binance API keys with futures trading permissions
2. Click the "My Futures Positions" button or menu item to view your active positions
3. Positions are automatically refreshed when data is refreshed (F5)

## Notes:
- Requires valid Binance API keys with permission to read futures account data
- Positions watchlist is not persisted to disk (always loaded fresh from API)
- Position data includes leverage information from your account
