"""
Models for asset and market data representation.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class AssetType(Enum):
    """Enum representing different types of crypto assets."""
    SPOT = "spot"
    FUTURES = "futures"
    MARGIN = "margin"


@dataclass
class AssetPrice:
    """Price and related data for an asset."""
    symbol: str
    price: float
    timestamp: datetime
    change_24h: float = 0.0
    change_4h: float = 0.0
    volume_24h: float = 0.0
    
    @property
    def change_24h_percent(self) -> float:
        """Return 24h price change as a percentage."""
        return self.change_24h * 100
        
    @property
    def change_4h_percent(self) -> float:
        """Return 4h price change as a percentage."""
        return self.change_4h * 100


class Asset:
    """Represents a crypto asset with its associated data."""
    
    def __init__(self, symbol: str, asset_type: AssetType = AssetType.SPOT):
        """Initialize a new asset.
        
        Args:
            symbol: The trading symbol (e.g., 'BTCUSDT')
            asset_type: The type of asset (spot, futures, margin)
        """
        self.symbol = symbol  # This is the raw symbol for API calls (e.g. 'BTCUSDT')
        self.asset_type = asset_type
        self.price_data: Optional[AssetPrice] = None
        self.balance: float = 0.0
        self.in_watchlist: bool = False
        self.strategies: List[str] = []  # IDs of assigned strategies
        # Futures position specific fields
        self.is_long: bool = False
        self.is_short: bool = False
        self.leverage: float = 1.0
        self.unrealized_pnl: float = 0.0
        
    @property
    def base_symbol(self) -> str:
        """Get the base symbol without any position information for API calls."""
        # Extract just the base symbol without position information
        # This is needed for API calls that require clean symbols
        
        # For futures positions, the symbol might contain LONG/SHORT and leverage info
        # Clean the symbol to match Binance API requirements: ^[A-Z0-9-_.]{1,20}$
        if self.is_long or self.is_short:
            # If symbol contains spaces, extract just the first part before any spaces
            # This assumes symbol format like "BTCUSDT LONG 10x"
            if " " in self.symbol:
                return self.symbol.split()[0]
        
        return self.symbol
    
    @property
    def display_name(self) -> str:
        """Get a formatted display name for the asset including position details if applicable."""
        if self.is_long or self.is_short:
            position_type = "LONG" if self.is_long else "SHORT"
            return f"{self.base_symbol} {position_type} {self.leverage}x"
        return self.symbol
        
    def update_price(self, price_data: AssetPrice):
        """Update the price data for this asset."""
        self.price_data = price_data
        
    def update_balance(self, balance: float):
        """Update the balance for this asset."""
        self.balance = balance
        
    def add_strategy(self, strategy_id: str):
        """Assign a strategy to this asset."""
        if strategy_id not in self.strategies:
            self.strategies.append(strategy_id)
            
    def remove_strategy(self, strategy_id: str):
        """Remove a strategy from this asset."""
        if strategy_id in self.strategies:
            self.strategies.remove(strategy_id)
            
    @property
    def value_usd(self) -> float:
        """Calculate the USD value of the asset holdings."""
        if self.price_data is None:
            return 0.0
        return self.balance * self.price_data.price
        
    @property
    def position_type(self) -> str:
        """Get the position type as a string."""
        if self.is_long:
            return "LONG"
        elif self.is_short:
            return "SHORT"
        return ""
        
    def to_dict(self) -> dict:
        """Convert asset to dictionary for serialization."""
        return {
            'symbol': self.symbol,
            'asset_type': self.asset_type.value,
            'balance': self.balance,
            'strategies': self.strategies,
            'is_long': self.is_long,
            'is_short': self.is_short,
            'leverage': self.leverage,
        }
        
    @classmethod
    def from_dict(cls, data: dict) -> 'Asset':
        """Create an asset from a dictionary."""
        asset = cls(
            symbol=data['symbol'],
            asset_type=AssetType(data.get('asset_type', AssetType.SPOT.value))
        )
        asset.balance = data.get('balance', 0.0)
        asset.strategies = data.get('strategies', [])
        asset.is_long = data.get('is_long', False)
        asset.is_short = data.get('is_short', False)
        asset.leverage = data.get('leverage', 1.0)
        return asset
        
    def __str__(self) -> str:
        return f"{self.symbol} ({self.balance})"
        
    def __repr__(self) -> str:
        return f"Asset({self.symbol}, {self.asset_type})"
