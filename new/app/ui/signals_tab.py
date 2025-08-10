"""
Signals tab for displaying trading signals.
"""
import logging
from typing import Dict, List, Optional, Tuple

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QHeaderView, QMenu, QAction,
    QAbstractItemView, QCheckBox, QFrame, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
from PyQt5.QtGui import QColor, QBrush, QFont, QIcon

from app.services.binance_service import BinanceService
from app.services.portfolio_manager import PortfolioManager
from app.services.strategy_manager import StrategyManager
from app.models.asset import Asset
from app.models.strategy import Signal, SignalType, Strategy
from app.ui.theme import DarkThemeColors, apply_dark_theme_to_table, get_color_for_change


class SignalsTab(QWidget):
    """Tab for signal dashboard."""
    
    def __init__(
        self, 
        binance_service: BinanceService, 
        portfolio_manager: PortfolioManager,
        strategy_manager: StrategyManager
    ):
        """Initialize the signals tab.
        
        Args:
            binance_service: Binance API service
            portfolio_manager: Portfolio manager service
            strategy_manager: Strategy manager service
        """
        super().__init__()
        
        self.binance_service = binance_service
        self.portfolio_manager = portfolio_manager
        self.strategy_manager = strategy_manager
        self.logger = logging.getLogger(__name__)
        
        # Keep track of active strategies (columns)
        self.active_strategies: List[Strategy] = []
        
        # Setup UI
        self._setup_ui()
        
        # Connect signals
        self._connect_signals()
        
        # Load initial data
        self.refresh_signals()
        
    def _setup_ui(self):
        """Setup the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Header with controls
        header_layout = QHBoxLayout()
        
        # Title label
        title_label = QLabel("Signal Dashboard")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Asset source combo
        self.source_combo = QComboBox()
        self.source_combo.addItem("Active Watchlist")
        self.source_combo.addItem("Portfolio Assets")
        self.source_combo.addItem("Assets with Strategies")
        header_layout.addWidget(QLabel("Show:"))
        header_layout.addWidget(self.source_combo)
        
        # Auto-refresh checkbox
        self.auto_refresh_check = QCheckBox("Auto-refresh")
        self.auto_refresh_check.setChecked(self.strategy_manager.is_auto_refresh_active())
        header_layout.addWidget(self.auto_refresh_check)
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        header_layout.addWidget(self.refresh_button)
        
        # Add to main layout
        main_layout.addLayout(header_layout)
        
        # Legend layout
        legend_layout = QHBoxLayout()
        legend_layout.addWidget(QLabel("Signal Legend:"))
        
        # Long signal
        long_indicator = QLabel("LONG")
        long_indicator.setStyleSheet("color: green; font-weight: bold;")
        legend_layout.addWidget(long_indicator)
        
        # Neutral signal
        neutral_indicator = QLabel("NEUTRAL")
        neutral_indicator.setStyleSheet("color: gray; font-weight: bold;")
        legend_layout.addWidget(neutral_indicator)
        
        # Short signal
        short_indicator = QLabel("SHORT")
        short_indicator.setStyleSheet("color: red; font-weight: bold;")
        legend_layout.addWidget(short_indicator)
        
        legend_layout.addStretch()
        
        main_layout.addLayout(legend_layout)
        
        # Signals table
        self.signals_table = QTableWidget()
        self.signals_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.signals_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.signals_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.signals_table.verticalHeader().setVisible(False)
        main_layout.addWidget(self.signals_table)
        
    def _connect_signals(self):
        """Connect signals from services and widgets."""
        # Connect strategy manager signals
        self.strategy_manager.signal_generated.connect(self._on_signal_generated)
        self.strategy_manager.strategy_assigned.connect(
            lambda symbol, strategy_id: self.refresh_signals()
        )
        self.strategy_manager.strategy_removed.connect(
            lambda symbol, strategy_id: self.refresh_signals()
        )
        
        # Connect portfolio manager signals
        self.portfolio_manager.portfolio_updated.connect(self.refresh_signals)
        self.portfolio_manager.watchlist_updated.connect(
            lambda name: self.refresh_signals() 
            if self.source_combo.currentIndex() == 0 else None
        )
        
        # Connect widget signals
        self.refresh_button.clicked.connect(self.refresh_signals)
        self.source_combo.currentIndexChanged.connect(self.refresh_signals)
        self.auto_refresh_check.stateChanged.connect(self._toggle_auto_refresh)
        self.signals_table.customContextMenuRequested.connect(self._show_context_menu)
        
    def refresh_signals(self):
        """Refresh the signals table with current data."""
        # Get assets based on source
        source_index = self.source_combo.currentIndex()
        symbols = []
        assets_map = {}  # Map of base_symbol -> asset for lookups
        
        if source_index == 0:  # Active Watchlist
            assets = self.portfolio_manager.get_watchlist_assets()
            # Store clean symbols for API operations but keep a map to assets for display
            for asset in assets:
                symbols.append(asset.base_symbol)
                assets_map[asset.base_symbol] = asset
        elif source_index == 1:  # Portfolio Assets
            assets = [a for a in self.portfolio_manager.get_all_assets() if a.balance > 0]
            # Store clean symbols for API operations but keep a map to assets for display
            for asset in assets:
                symbols.append(asset.base_symbol)
                assets_map[asset.base_symbol] = asset
        elif source_index == 2:  # Assets with Strategies
            symbols = self.strategy_manager.get_assets_with_strategies()
            
        # Get all strategies
        all_strategies = self.strategy_manager.get_all_strategies()
        
        # Filter for active strategies (those assigned to at least one asset)
        active_strategy_ids = set()
        for symbol in symbols:
            active_strategy_ids.update(
                self.strategy_manager.get_asset_strategy_ids(symbol)
            )
            
        self.active_strategies = [
            strategy for strategy in all_strategies 
            if strategy.strategy_id in active_strategy_ids
        ]
        
        # Configure table columns
        # First column is symbol, rest are strategies
        self.signals_table.setColumnCount(1 + len(self.active_strategies))
        
        headers = ["Symbol"]
        for strategy in self.active_strategies:
            headers.append(strategy.name)
            
        self.signals_table.setHorizontalHeaderLabels(headers)
        
        # Update table rows
        self.signals_table.setRowCount(len(symbols))
        
        for row, symbol in enumerate(symbols):
            # Set symbol - display the formatted name but store the base symbol for API calls
            display_text = symbol
            if symbol in assets_map:
                display_text = assets_map[symbol].display_name
                
            symbol_item = QTableWidgetItem(display_text)
            symbol_item.setData(Qt.UserRole, symbol)  # Store clean symbol for API operations
            self.signals_table.setItem(row, 0, symbol_item)
            
            # Get asset strategies
            asset_strategy_ids = self.strategy_manager.get_asset_strategy_ids(symbol)
            
            # Set signal cells
            for col, strategy in enumerate(self.active_strategies, start=1):
                if strategy.strategy_id in asset_strategy_ids:
                    # Get signal
                    signal = self.strategy_manager.get_signal(symbol, strategy.strategy_id)
                    
                    if signal:
                        self._set_signal_cell(row, col, signal)
                    else:
                        # No signal yet
                        self.signals_table.setItem(row, col, QTableWidgetItem("..."))
                else:
                    # Strategy not assigned
                    self.signals_table.setItem(row, col, QTableWidgetItem("-"))
                    
        # Resize columns
        self.signals_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for col in range(1, self.signals_table.columnCount()):
            self.signals_table.horizontalHeader().setSectionResizeMode(
                col, QHeaderView.ResizeToContents
            )
            
    def _set_signal_cell(self, row: int, col: int, signal: Signal):
        """Set the cell content for a signal.
        
        Args:
            row: Table row
            col: Table column
            signal: The signal to display
        """
        # Create item with signal type
        item = QTableWidgetItem(signal.signal_type.value)
        item.setTextAlignment(Qt.AlignCenter)
        
        # Set color based on signal type
        if signal.signal_type == SignalType.LONG:
            item.setForeground(QBrush(QColor(46, 204, 113)))  # Green
            item.setFont(QFont("", -1, QFont.Bold))
        elif signal.signal_type == SignalType.SHORT:
            item.setForeground(QBrush(QColor(231, 76, 60)))  # Red
            item.setFont(QFont("", -1, QFont.Bold))
        else:  # NEUTRAL
            item.setForeground(QBrush(QColor(149, 165, 166)))  # Gray
            
        # Add tooltip with signal details
        tooltip = f"Signal: {signal.signal_type.value}\n"
        tooltip += f"Strength: {signal.strength:.2f}\n"
        tooltip += f"Generated: {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if signal.params:
            tooltip += "\nParameters:\n"
            for key, value in signal.params.items():
                tooltip += f"- {key}: {value}\n"
                
        item.setToolTip(tooltip)
        
        # Set the item
        self.signals_table.setItem(row, col, item)
        
    def _on_signal_generated(self, signal: Signal):
        """Handle new signal from strategy manager.
        
        Args:
            signal: The new signal
        """
        # Find row for symbol
        symbol = signal.symbol
        row = -1
        
        for r in range(self.signals_table.rowCount()):
            if self.signals_table.item(r, 0).text() == symbol:
                row = r
                break
                
        if row == -1:
            # Symbol not in table
            return
            
        # Find column for strategy
        strategy_id = signal.strategy_id
        col = -1
        
        for c, strategy in enumerate(self.active_strategies, start=1):
            if strategy.strategy_id == strategy_id:
                col = c
                break
                
        if col == -1:
            # Strategy not in table
            return
            
        # Update the cell
        self._set_signal_cell(row, col, signal)
        
    def _toggle_auto_refresh(self, state):
        """Toggle auto-refresh of signals.
        
        Args:
            state: Checkbox state
        """
        if state == Qt.Checked:
            self.strategy_manager.start_auto_refresh()
        else:
            self.strategy_manager.stop_auto_refresh()
            
    def _show_context_menu(self, position):
        """Show context menu for signal table.
        
        Args:
            position: Position where menu should appear
        """
        menu = QMenu()
        
        # Get selected item
        selected_indexes = self.signals_table.selectedIndexes()
        if not selected_indexes:
            return
            
        # Get symbol from the selected row
        row = selected_indexes[0].row()
        symbol_item = self.signals_table.item(row, 0)
        if not symbol_item:
            return
            
        symbol = symbol_item.text()
        
        # Refresh signals action
        refresh_action = QAction(f"Refresh Signals for {symbol}", self)
        refresh_action.triggered.connect(
            lambda: self._refresh_asset_signals(symbol)
        )
        menu.addAction(refresh_action)
        
        menu.addSeparator()
        
        # Strategy management submenu
        strategy_menu = menu.addMenu("Strategies")
        
        # Get assigned strategies
        assigned_strategies = self.strategy_manager.get_asset_strategy_ids(symbol)
        
        # Add strategies
        for strategy in self.strategy_manager.get_all_strategies():
            strategy_action = QAction(strategy.name, self)
            strategy_action.setCheckable(True)
            strategy_action.setChecked(strategy.strategy_id in assigned_strategies)
            strategy_action.triggered.connect(
                lambda checked, s=strategy.strategy_id: 
                self._toggle_strategy(symbol, s, checked)
            )
            strategy_menu.addAction(strategy_action)
            
        # Show menu
        menu.exec_(self.signals_table.mapToGlobal(position))
        
    def _refresh_asset_signals(self, symbol: str):
        """Refresh signals for a specific asset.
        
        Args:
            symbol: Asset symbol
        """
        self.strategy_manager.refresh_asset_signals(symbol)
        
    def _toggle_strategy(self, symbol: str, strategy_id: str, assign: bool):
        """Toggle a strategy assignment.
        
        Args:
            symbol: Asset symbol
            strategy_id: Strategy ID
            assign: Whether to assign or remove
        """
        if assign:
            self.strategy_manager.assign_strategy(symbol, strategy_id)
        else:
            self.strategy_manager.remove_strategy(symbol, strategy_id)
