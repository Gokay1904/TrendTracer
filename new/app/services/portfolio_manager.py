"""
Portfolio manager service for handling watchlists and assets.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from app.models.asset import Asset, AssetPrice, AssetType
from app.models.portfolio import Portfolio, Watchlist
from app.services.binance_service import BinanceService
from app.config.settings import Settings


class PortfolioManager(QObject):
    """Service for managing portfolio and watchlists."""
    
    # Define signals for portfolio updates
    portfolio_updated = pyqtSignal()
    watchlist_updated = pyqtSignal(str)  # watchlist_name
    asset_updated = pyqtSignal(Asset)
    
    def __init__(self, settings: Settings, binance_service: BinanceService):
        """Initialize the portfolio manager.
        
        Args:
            settings: Application settings
            binance_service: Binance API service
        """
        super().__init__()
        self.settings = settings
        self.binance_service = binance_service
        self.portfolio = Portfolio()
        self.logger = logging.getLogger(__name__)
        
        # Create data directory if it doesn't exist
        self.data_dir = self.settings.ensure_data_directory()
        
        # Load portfolio from file
        self._load_portfolio()
        
        # Connect to Binance service signals
        self.binance_service.price_updated.connect(self._handle_price_update)
        self.binance_service.account_updated.connect(self._handle_account_update)
        
    def _get_portfolio_file_path(self) -> Path:
        """Get the path to the portfolio data file."""
        return Path(self.data_dir) / 'portfolio.json'
        
    def _load_portfolio(self):
        """Load portfolio data from file."""
        file_path = self._get_portfolio_file_path()
        
        try:
            if file_path.exists():
                self.portfolio = Portfolio.load_from_file(file_path)
                self.logger.info(f"Loaded portfolio from {file_path}")
                
                # Set the active watchlist from settings if available
                active_watchlist = self.settings.get('active_watchlist')
                if active_watchlist and active_watchlist in self.portfolio.watchlists:
                    self.portfolio.active_watchlist_name = active_watchlist
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Error loading portfolio: {e}")
            # Create a new portfolio if loading fails
            self.portfolio = Portfolio()
            
    def save_portfolio(self):
        """Save portfolio data to file."""
        file_path = self._get_portfolio_file_path()
        
        try:
            self.portfolio.save_to_file(file_path)
            self.logger.info(f"Saved portfolio to {file_path}")
            
            # Save active watchlist to settings
            self.settings.set('active_watchlist', self.portfolio.active_watchlist_name)
        except IOError as e:
            self.logger.error(f"Error saving portfolio: {e}")
            
    def get_portfolio(self) -> Portfolio:
        """Get the current portfolio instance."""
        return self.portfolio
        
    def get_all_assets(self) -> List[Asset]:
        """Get all assets in the portfolio."""
        return list(self.portfolio.assets.values())
        
    def get_watchlist_assets(self, watchlist_name: Optional[str] = None) -> List[Asset]:
        """Get assets in the specified watchlist.
        
        Args:
            watchlist_name: Name of watchlist (uses active if None)
            
        Returns:
            List[Asset]: List of assets in the watchlist
        """
        return self.portfolio.get_watchlist_assets(watchlist_name)
        
    def get_watchlists(self) -> Dict[str, Watchlist]:
        """Get all watchlists in the portfolio."""
        return self.portfolio.watchlists
        
    def get_active_watchlist(self) -> Watchlist:
        """Get the active watchlist."""
        return self.portfolio.active_watchlist
        
    def set_active_watchlist(self, name: str) -> bool:
        """Set the active watchlist.
        
        Args:
            name: Name of the watchlist to set as active
            
        Returns:
            bool: True if successful, False if not found
        """
        result = self.portfolio.set_active_watchlist(name)
        if result:
            self.settings.set('active_watchlist', name)
            self.watchlist_updated.emit(name)
            
        return result
        
    def create_watchlist(self, name: str) -> bool:
        """Create a new watchlist.
        
        Args:
            name: Name for the new watchlist
            
        Returns:
            bool: True if created, False if name already exists
        """
        result = self.portfolio.create_watchlist(name)
        if result:
            self.save_portfolio()
            self.portfolio_updated.emit()
            
        return result
        
    def delete_watchlist(self, name: str) -> bool:
        """Delete a watchlist.
        
        Args:
            name: Name of the watchlist to delete
            
        Returns:
            bool: True if deleted, False if not found or is default
        """
        result = self.portfolio.delete_watchlist(name)
        if result:
            self.save_portfolio()
            self.portfolio_updated.emit()
            
        return result
        
    def add_to_watchlist(self, symbol: str, watchlist_name: Optional[str] = None) -> bool:
        """Add a symbol to a watchlist.
        
        Args:
            symbol: Symbol to add
            watchlist_name: Watchlist name (uses active if None)
            
        Returns:
            bool: True if added, False if already in watchlist
        """
        result = self.portfolio.add_to_watchlist(symbol, watchlist_name)
        if result:
            # Ensure we have the asset in our portfolio
            if symbol not in self.portfolio.assets:
                asset = Asset(symbol)
                self.portfolio.add_asset(asset)
                
                # Fetch initial price data
                self._fetch_asset_price(symbol)
                
            self.save_portfolio()
            target_list = watchlist_name or self.portfolio.active_watchlist_name
            self.watchlist_updated.emit(target_list)
            
        return result
        
    def remove_from_watchlist(self, symbol: str, watchlist_name: Optional[str] = None) -> bool:
        """Remove a symbol from a watchlist.
        
        Args:
            symbol: Symbol to remove
            watchlist_name: Watchlist name (uses active if None)
            
        Returns:
            bool: True if removed, False if not in watchlist
        """
        result = self.portfolio.remove_from_watchlist(symbol, watchlist_name)
        if result:
            self.save_portfolio()
            target_list = watchlist_name or self.portfolio.active_watchlist_name
            self.watchlist_updated.emit(target_list)
            
        return result
        
    def _fetch_asset_price(self, symbol: str):
        """Fetch current price for an asset.
        
        Args:
            symbol: Asset symbol
        """
        try:
            ticker = self.binance_service.client.get_symbol_ticker(symbol=symbol)
            price = float(ticker['price'])
            
            # Get 24h stats for change percentage
            stats = self.binance_service.get_24h_stats(symbol)
            if stats and len(stats) > 0:
                change_24h = float(stats[0]['priceChangePercent']) / 100
                volume_24h = float(stats[0]['volume'])
            else:
                change_24h = 0.0
                volume_24h = 0.0
                
            price_data = AssetPrice(
                symbol=symbol,
                price=price,
                timestamp=stats[0]['closeTime'] if stats and len(stats) > 0 else None,
                change_24h=change_24h,
                volume_24h=volume_24h
            )
            
            asset = self.portfolio.get_asset(symbol)
            if asset:
                asset.update_price(price_data)
                self.asset_updated.emit(asset)
        except Exception as e:
            self.logger.error(f"Error fetching price for {symbol}: {e}")
            
    def sync_with_binance_account(self):
        """Synchronize portfolio with Binance account balances."""
        account_info = self.binance_service.get_account_info()
        if not account_info:
            return
            
        for balance in account_info['balances']:
            asset_name = balance['asset']
            free = float(balance['free'])
            locked = float(balance['locked'])
            total = free + locked
            
            # Skip zero balances
            if total <= 0:
                continue
                
            # Try to find a USDT pair
            symbol = f"{asset_name}USDT"
            
            # Update or create asset
            asset = self.portfolio.get_asset(symbol)
            if not asset:
                asset = Asset(symbol)
                self.portfolio.add_asset(asset)
                
            asset.update_balance(total)
            
            # Fetch price data
            self._fetch_asset_price(symbol)
            
        self.portfolio_updated.emit()
        self.save_portfolio()
        
    @pyqtSlot(AssetPrice)
    def _handle_price_update(self, price_data: AssetPrice):
        """Handle real-time price updates from Binance service.
        
        Args:
            price_data: Updated price data
        """
        asset = self.portfolio.get_asset(price_data.symbol)
        if asset:
            asset.update_price(price_data)
            self.asset_updated.emit(asset)
            
    @pyqtSlot(dict)
    def _handle_account_update(self, account_data: dict):
        """Handle account updates from Binance service.
        
        Args:
            account_data: Account update data
        """
        if 'B' in account_data:  # Balances
            for balance in account_data['B']:
                asset_name = balance['a']  # Asset
                free = float(balance['f'])  # Free
                locked = float(balance['l'])  # Locked
                total = free + locked
                
                # Skip zero balances
                if total <= 0:
                    continue
                    
                # Try to find a USDT pair
                symbol = f"{asset_name}USDT"
                
                # Update or create asset
                asset = self.portfolio.get_asset(symbol)
                if not asset:
                    asset = Asset(symbol)
                    self.portfolio.add_asset(asset)
                    
                asset.update_balance(total)
                self.asset_updated.emit(asset)
                
            self.portfolio_updated.emit()
            self.save_portfolio()
            
    def get_top_gainers(self, timeframe: str = '24h', limit: int = 10) -> List[Asset]:
        """Get top gaining assets by price change.
        
        Args:
            timeframe: Timeframe for price change ('4h' or '24h')
            limit: Maximum number of assets to return
            
        Returns:
            List[Asset]: List of top gaining assets
        """
        # Convert timeframe to hours
        hours = 24
        if timeframe == '4h':
            hours = 4
            
        # Get top movers from Binance
        movers = self.binance_service.get_top_movers(
            lookback_hours=hours,
            limit=limit
        )
        
        result = []
        for mover in movers:
            symbol = mover['symbol']
            
            # Get or create asset
            asset = self.portfolio.get_asset(symbol)
            if not asset:
                asset = Asset(symbol)
                self.portfolio.add_asset(asset)
                
            # Update price data
            price = float(mover['lastPrice'])
            change = float(mover['priceChangePercent']) / 100
            volume = float(mover['volume'])
            
            price_data = AssetPrice(
                symbol=symbol,
                price=price,
                timestamp=None,  # Binance doesn't provide timestamp in this API
                change_24h=change if hours == 24 else 0.0,
                change_4h=change if hours == 4 else 0.0,
                volume_24h=volume
            )
            
            asset.update_price(price_data)
            result.append(asset)
            
        return result
        
    def start_price_updates(self):
        """Start real-time price updates for watched assets."""
        # Get all symbols in watchlists
        all_symbols = set()
        for watchlist in self.portfolio.watchlists.values():
            all_symbols.update(watchlist.symbols)
            
        # Start ticker stream for these symbols
        if all_symbols:
            self.binance_service.start_ticker_stream(list(all_symbols))
            
    def refresh_all_prices(self):
        """Manually refresh prices for all assets in the portfolio."""
        for symbol in self.portfolio.assets:
            self._fetch_asset_price(symbol)
            
    def update_futures_positions(self) -> bool:
        """Update the Futures Positions watchlist with current positions.
        
        Returns:
            bool: True if successful, False if API error
        """
        # Get futures positions from Binance
        positions = self.binance_service.get_futures_positions()
        if not positions:
            return False
            
        # Get the futures positions watchlist
        futures_watchlist = self.portfolio.watchlists.get('futures_positions')
        if not futures_watchlist:
            futures_watchlist = self.portfolio.create_watchlist('Futures Positions')
            self.portfolio.watchlists['futures_positions'] = futures_watchlist
            
        # Clear previous positions
        futures_watchlist.symbols.clear()
        
        # Add current positions
        for position in positions:
            symbol = position['symbol']
            position_amt = float(position.get('positionAmt', 0))
            
            # Skip positions with zero amount
            if position_amt == 0:
                continue
                
            # Add to watchlist
            futures_watchlist.add_symbol(symbol)
            
            # Create or update asset
            asset = self.portfolio.get_asset(symbol)
            if not asset:
                asset = Asset(symbol, AssetType.FUTURES)
                self.portfolio.add_asset(asset)
            
            # Calculate position value
            position_value = abs(position_amt) * float(position.get('markPrice', 0))
            leverage = float(position.get('leverage', 1))
            
            # Update asset with position info
            asset.update_balance(abs(position_amt))
            asset.is_long = position_amt > 0
            asset.is_short = position_amt < 0
            asset.leverage = leverage
            
            # Fetch full price data
            self._fetch_asset_price(symbol)
            
            # Emit update signal
            self.asset_updated.emit(asset)
            
        # Update timestamp
        self.portfolio.futures_positions_updated = datetime.now()
        
        # Emit signals
        self.watchlist_updated.emit('futures_positions')
        
        return True
