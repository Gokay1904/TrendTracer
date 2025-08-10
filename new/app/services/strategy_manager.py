"""
Strategy manager service for handling trading strategies.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer

from app.models.asset import Asset
from app.models.strategy import Strategy, Signal, SignalType, StrategyRegistry
from app.services.binance_service import BinanceService
from app.config.settings import Settings


class StrategyManager(QObject):
    """Service for managing trading strategies and signals."""
    
    # Define signals for strategy updates
    strategy_assigned = pyqtSignal(str, str)  # symbol, strategy_id
    strategy_removed = pyqtSignal(str, str)  # symbol, strategy_id
    signal_generated = pyqtSignal(Signal)
    
    def __init__(self, settings: Settings, binance_service: BinanceService):
        """Initialize the strategy manager.
        
        Args:
            settings: Application settings
            binance_service: Binance API service
        """
        super().__init__()
        self.settings = settings
        self.binance_service = binance_service
        self.logger = logging.getLogger(__name__)
        
        # Store active signals
        self.active_signals: Dict[Tuple[str, str], Signal] = {}  # (symbol, strategy_id) -> Signal
        
        # Store strategy assignments
        self.asset_strategies: Dict[str, Set[str]] = {}  # symbol -> set of strategy_ids
        
        # Create data directory if it doesn't exist
        self.data_dir = self.settings.ensure_data_directory()
        
        # Load strategy assignments
        self._load_strategy_assignments()
        
        # Setup refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_all_signals)
        self.refresh_interval = self.settings.get('refresh_interval', 60000)  # ms
        
    def _get_assignments_file_path(self) -> Path:
        """Get the path to the strategy assignments file."""
        return Path(self.data_dir) / 'strategy_assignments.json'
        
    def _load_strategy_assignments(self):
        """Load strategy assignments from file."""
        file_path = self._get_assignments_file_path()
        
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    
                # Convert to sets of strategy IDs
                self.asset_strategies = {
                    symbol: set(strategy_ids)
                    for symbol, strategy_ids in data.items()
                }
                
                self.logger.info(f"Loaded strategy assignments from {file_path}")
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Error loading strategy assignments: {e}")
            self.asset_strategies = {}
            
    def _save_strategy_assignments(self):
        """Save strategy assignments to file."""
        file_path = self._get_assignments_file_path()
        
        try:
            # Convert sets to lists for JSON serialization
            data = {
                symbol: list(strategy_ids)
                for symbol, strategy_ids in self.asset_strategies.items()
            }
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
                
            self.logger.info(f"Saved strategy assignments to {file_path}")
        except IOError as e:
            self.logger.error(f"Error saving strategy assignments: {e}")
            
    def get_all_strategies(self) -> List[Strategy]:
        """Get all available strategies.
        
        Returns:
            List[Strategy]: List of all registered strategies
        """
        return StrategyRegistry.get_all_strategies()
        
    def get_strategy(self, strategy_id: str) -> Optional[Strategy]:
        """Get a strategy by ID.
        
        Args:
            strategy_id: ID of the strategy to retrieve
            
        Returns:
            Optional[Strategy]: The strategy or None if not found
        """
        return StrategyRegistry.get_strategy(strategy_id)
        
    def assign_strategy(self, symbol: str, strategy_id: str) -> bool:
        """Assign a strategy to an asset.
        
        Args:
            symbol: Asset symbol
            strategy_id: Strategy ID
            
        Returns:
            bool: True if assigned, False if already assigned or invalid
        """
        # Validate strategy exists
        strategy = self.get_strategy(strategy_id)
        if not strategy:
            self.logger.error(f"Strategy {strategy_id} not found")
            return False
            
        # Initialize set for this symbol if needed
        if symbol not in self.asset_strategies:
            self.asset_strategies[symbol] = set()
            
        # Check if already assigned
        if strategy_id in self.asset_strategies[symbol]:
            return False
            
        # Assign strategy
        self.asset_strategies[symbol].add(strategy_id)
        self._save_strategy_assignments()
        
        # Emit signal
        self.strategy_assigned.emit(symbol, strategy_id)
        
        # Generate initial signal
        self.generate_signal(symbol, strategy_id)
        
        return True
        
    def remove_strategy(self, symbol: str, strategy_id: str) -> bool:
        """Remove a strategy from an asset.
        
        Args:
            symbol: Asset symbol
            strategy_id: Strategy ID
            
        Returns:
            bool: True if removed, False if not assigned
        """
        # Check if assigned
        if (symbol not in self.asset_strategies or 
                strategy_id not in self.asset_strategies[symbol]):
            return False
            
        # Remove strategy
        self.asset_strategies[symbol].remove(strategy_id)
        
        # Remove empty sets
        if not self.asset_strategies[symbol]:
            del self.asset_strategies[symbol]
            
        self._save_strategy_assignments()
        
        # Remove any active signals for this assignment
        signal_key = (symbol, strategy_id)
        if signal_key in self.active_signals:
            del self.active_signals[signal_key]
            
        # Emit signal
        self.strategy_removed.emit(symbol, strategy_id)
        
        return True
        
    def get_asset_strategies(self, symbol: str) -> List[Strategy]:
        """Get all strategies assigned to an asset.
        
        Args:
            symbol: Asset symbol
            
        Returns:
            List[Strategy]: List of assigned strategies
        """
        if symbol not in self.asset_strategies:
            return []
            
        return [
            self.get_strategy(strategy_id)
            for strategy_id in self.asset_strategies[symbol]
            if self.get_strategy(strategy_id) is not None
        ]
        
    def get_asset_strategy_ids(self, symbol: str) -> Set[str]:
        """Get IDs of all strategies assigned to an asset.
        
        Args:
            symbol: Asset symbol
            
        Returns:
            Set[str]: Set of assigned strategy IDs
        """
        return self.asset_strategies.get(symbol, set())
        
    def get_assets_with_strategies(self) -> List[str]:
        """Get all assets that have strategies assigned.
        
        Returns:
            List[str]: List of asset symbols
        """
        return list(self.asset_strategies.keys())
        
    def generate_signal(self, symbol: str, strategy_id: str) -> Optional[Signal]:
        """Generate a signal for a symbol using a specific strategy.
        
        Args:
            symbol: Asset symbol
            strategy_id: Strategy ID
            
        Returns:
            Optional[Signal]: The generated signal or None on error
        """
        # Get the strategy
        strategy = self.get_strategy(strategy_id)
        if not strategy:
            self.logger.error(f"Strategy {strategy_id} not found")
            return None
            
        try:
            # Clean the symbol for API call - extract only valid characters
            clean_symbol = self._clean_symbol(symbol)
            
            # Get historical data
            klines = self.binance_service.get_klines(
                symbol=clean_symbol,
                interval='1h',  # Default interval
                limit=100  # Enough for most strategies
            )
            
            if klines is None or len(klines) == 0:
                self.logger.error(f"Failed to get klines for {symbol}")
                return None
                
            # Generate signal using the strategy but keep the original symbol for display
            signal = strategy.generate_signal(symbol, klines)
            
            # Store and emit the signal
            signal_key = (symbol, strategy_id)
            self.active_signals[signal_key] = signal
            self.signal_generated.emit(signal)
            
            return signal
        except Exception as e:
            self.logger.error(f"Error generating signal for {symbol} using {strategy_id}: {e}")
            return None
            
    def get_signal(self, symbol: str, strategy_id: str) -> Optional[Signal]:
        """Get the most recent signal for a symbol and strategy.
        
        Args:
            symbol: Asset symbol
            strategy_id: Strategy ID
            
        Returns:
            Optional[Signal]: The signal or None if not available
        """
        signal_key = (symbol, strategy_id)
        return self.active_signals.get(signal_key)
        
    def _clean_symbol(self, symbol: str) -> str:
        """Clean a symbol for API usage by removing illegal characters.
        
        Args:
            symbol: The raw symbol that might contain position information
            
        Returns:
            str: A clean symbol suitable for API calls
        """
        # If symbol contains spaces, extract just the first part before any spaces
        # This assumes symbol format like "BTCUSDT LONG 10x"
        if " " in symbol:
            return symbol.split()[0]
        return symbol
        
    def get_asset_signals(self, symbol: str) -> List[Signal]:
        """Get all active signals for an asset.
        
        Args:
            symbol: Asset symbol
            
        Returns:
            List[Signal]: List of active signals
        """
        return [
            signal for (sym, _), signal in self.active_signals.items()
            if sym == symbol
        ]
        
    def refresh_signal(self, symbol: str, strategy_id: str) -> Optional[Signal]:
        """Refresh a specific signal.
        
        Args:
            symbol: Asset symbol
            strategy_id: Strategy ID
            
        Returns:
            Optional[Signal]: The updated signal or None on error
        """
        return self.generate_signal(symbol, strategy_id)
        
    def refresh_asset_signals(self, symbol: str) -> List[Signal]:
        """Refresh all signals for an asset.
        
        Args:
            symbol: Asset symbol
            
        Returns:
            List[Signal]: List of updated signals
        """
        if symbol not in self.asset_strategies:
            return []
            
        result = []
        for strategy_id in self.asset_strategies[symbol]:
            signal = self.refresh_signal(symbol, strategy_id)
            if signal:
                result.append(signal)
                
        return result
        
    def refresh_all_signals(self):
        """Refresh all signals for all assets."""
        for symbol in self.asset_strategies:
            self.refresh_asset_signals(symbol)
            
    def start_auto_refresh(self, interval_ms: Optional[int] = None):
        """Start auto-refreshing signals.
        
        Args:
            interval_ms: Refresh interval in milliseconds (uses settings if None)
        """
        if interval_ms is not None:
            self.refresh_interval = interval_ms
            self.settings.set('refresh_interval', interval_ms)
            
        self.refresh_timer.start(self.refresh_interval)
        self.logger.info(f"Started auto-refresh with interval {self.refresh_interval}ms")
        
    def stop_auto_refresh(self):
        """Stop auto-refreshing signals."""
        self.refresh_timer.stop()
        self.logger.info("Stopped auto-refresh")
        
    def is_auto_refresh_active(self) -> bool:
        """Check if auto-refresh is active.
        
        Returns:
            bool: True if auto-refresh is active
        """
        return self.refresh_timer.isActive()
