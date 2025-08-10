"""
Portfolio model for managing watchlists and asset collections.
"""
from typing import Dict, List, Set, Optional
import json
from datetime import datetime
from pathlib import Path

from app.models.asset import Asset


class Watchlist:
    """A named collection of asset symbols."""
    
    def __init__(self, name: str, symbols: Optional[Set[str]] = None):
        """Initialize a watchlist.
        
        Args:
            name: The name of the watchlist
            symbols: Optional set of initial symbols
        """
        self.name = name
        self.symbols = symbols if symbols is not None else set()
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
    def add_symbol(self, symbol: str) -> bool:
        """Add a symbol to the watchlist.
        
        Args:
            symbol: The asset symbol to add
            
        Returns:
            bool: True if added, False if already present
        """
        if symbol in self.symbols:
            return False
            
        self.symbols.add(symbol)
        self.updated_at = datetime.now()
        return True
        
    def remove_symbol(self, symbol: str) -> bool:
        """Remove a symbol from the watchlist.
        
        Args:
            symbol: The asset symbol to remove
            
        Returns:
            bool: True if removed, False if not found
        """
        if symbol not in self.symbols:
            return False
            
        self.symbols.remove(symbol)
        self.updated_at = datetime.now()
        return True
        
    def contains(self, symbol: str) -> bool:
        """Check if a symbol is in the watchlist."""
        return symbol in self.symbols
        
    def to_dict(self) -> dict:
        """Convert watchlist to dictionary for serialization."""
        return {
            'name': self.name,
            'symbols': list(self.symbols),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
    @classmethod
    def from_dict(cls, data: dict) -> 'Watchlist':
        """Create a watchlist from a dictionary."""
        watchlist = cls(
            name=data['name'],
            symbols=set(data['symbols'])
        )
        watchlist.created_at = datetime.fromisoformat(data['created_at'])
        watchlist.updated_at = datetime.fromisoformat(data['updated_at'])
        return watchlist


class Portfolio:
    """Manages a collection of assets and watchlists."""
    
    def __init__(self):
        """Initialize an empty portfolio."""
        self.assets: Dict[str, Asset] = {}
        self.watchlists: Dict[str, Watchlist] = {
            'default': Watchlist('Default'),
            'futures_positions': Watchlist('Futures Positions')
        }
        self.active_watchlist_name = 'default'
        # Special flag for the futures positions watchlist
        self.futures_positions_updated = datetime.now()
        
    @property
    def active_watchlist(self) -> Watchlist:
        """Get the currently active watchlist."""
        return self.watchlists.get(
            self.active_watchlist_name, 
            self.watchlists['default']
        )
        
    def set_active_watchlist(self, name: str) -> bool:
        """Set the active watchlist by name.
        
        Args:
            name: The name of the watchlist to set as active
            
        Returns:
            bool: True if successful, False if watchlist not found
        """
        if name not in self.watchlists:
            return False
            
        self.active_watchlist_name = name
        return True
        
    def create_watchlist(self, name: str) -> bool:
        """Create a new watchlist.
        
        Args:
            name: The name for the new watchlist
            
        Returns:
            bool: True if created, False if name already exists
        """
        if name in self.watchlists:
            return False
            
        self.watchlists[name] = Watchlist(name)
        return True
        
    def delete_watchlist(self, name: str) -> bool:
        """Delete a watchlist by name.
        
        Args:
            name: The name of the watchlist to delete
            
        Returns:
            bool: True if deleted, False if not found or is default
        """
        if name == 'default' or name not in self.watchlists:
            return False
            
        if self.active_watchlist_name == name:
            self.active_watchlist_name = 'default'
            
        del self.watchlists[name]
        return True
        
    def add_to_watchlist(self, symbol: str, watchlist_name: Optional[str] = None) -> bool:
        """Add a symbol to a watchlist.
        
        Args:
            symbol: The symbol to add
            watchlist_name: The watchlist name (uses active if None)
            
        Returns:
            bool: True if added, False otherwise
        """
        target_list = watchlist_name or self.active_watchlist_name
        if target_list not in self.watchlists:
            return False
            
        return self.watchlists[target_list].add_symbol(symbol)
        
    def remove_from_watchlist(self, symbol: str, watchlist_name: Optional[str] = None) -> bool:
        """Remove a symbol from a watchlist.
        
        Args:
            symbol: The symbol to remove
            watchlist_name: The watchlist name (uses active if None)
            
        Returns:
            bool: True if removed, False otherwise
        """
        target_list = watchlist_name or self.active_watchlist_name
        if target_list not in self.watchlists:
            return False
            
        return self.watchlists[target_list].remove_symbol(symbol)
        
    def get_asset(self, symbol: str) -> Optional[Asset]:
        """Get an asset by symbol."""
        return self.assets.get(symbol)
        
    def add_asset(self, asset: Asset):
        """Add or update an asset in the portfolio."""
        self.assets[asset.symbol] = asset
        
    def remove_asset(self, symbol: str) -> bool:
        """Remove an asset from the portfolio.
        
        Args:
            symbol: The asset symbol to remove
            
        Returns:
            bool: True if removed, False if not found
        """
        if symbol not in self.assets:
            return False
            
        del self.assets[symbol]
        return True
        
    def get_watchlist_assets(self, watchlist_name: Optional[str] = None) -> List[Asset]:
        """Get assets that are in the specified watchlist.
        
        Args:
            watchlist_name: The watchlist name (uses active if None)
            
        Returns:
            List[Asset]: List of assets in the watchlist
        """
        target_list = watchlist_name or self.active_watchlist_name
        if target_list not in self.watchlists:
            return []
            
        return [
            self.assets[symbol] for symbol in self.watchlists[target_list].symbols
            if symbol in self.assets
        ]
        
    def get_total_value(self) -> float:
        """Calculate the total portfolio value in USD."""
        return sum(asset.value_usd for asset in self.assets.values())
        
    def save_to_file(self, file_path: Path):
        """Save portfolio data to a JSON file.
        
        Args:
            file_path: Path to save the portfolio data
        """
        data = {
            'active_watchlist': self.active_watchlist_name,
            'watchlists': {
                name: wl.to_dict() 
                for name, wl in self.watchlists.items()
                if name != 'futures_positions'  # Don't persist futures positions
            }
            # Assets are loaded dynamically from Binance, so we don't save them
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
            
    @classmethod
    def load_from_file(cls, file_path: Path) -> 'Portfolio':
        """Load portfolio data from a JSON file.
        
        Args:
            file_path: Path to the portfolio data file
            
        Returns:
            Portfolio: The loaded portfolio instance
        """
        portfolio = cls()
        
        if not file_path.exists():
            return portfolio
            
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        portfolio.active_watchlist_name = data.get('active_watchlist', 'default')
        
        for name, wl_data in data.get('watchlists', {}).items():
            if name != 'futures_positions':  # Don't load futures positions from file
                portfolio.watchlists[name] = Watchlist.from_dict(wl_data)
        
        # Make sure we always have the special futures positions watchlist
        if 'futures_positions' not in portfolio.watchlists:
            portfolio.watchlists['futures_positions'] = Watchlist('Futures Positions')
            
        return portfolio
