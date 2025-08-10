"""
Portfolio tab for displaying and managing assets.
"""
import logging
from typing import Dict, List, Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QHeaderView, QMenu, QAction,
    QAbstractItemView, QInputDialog, QMessageBox, QSplitter, QFrame
)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
from PyQt5.QtGui import QColor, QBrush, QFont, QIcon

from app.services.binance_service import BinanceService
from app.services.portfolio_manager import PortfolioManager
from app.services.strategy_manager import StrategyManager
from app.models.asset import Asset, AssetPrice
from app.ui.theme import DarkThemeColors, apply_dark_theme_to_table, get_color_for_change


class PortfolioTab(QWidget):
    """Tab for portfolio management."""
    
    # Column indices
    COL_SYMBOL = 0
    COL_PRICE = 1
    COL_CHANGE_24H = 2
    COL_VOLUME = 3
    COL_BALANCE = 4
    COL_VALUE = 5
    
    def __init__(
        self, 
        binance_service: BinanceService, 
        portfolio_manager: PortfolioManager,
        strategy_manager: StrategyManager
    ):
        """Initialize the portfolio tab.
        
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
        
        # Setup UI
        self._setup_ui()
        
        # Connect signals
        self._connect_signals()
        
        # Load initial data
        self.refresh_assets()
        
    def _setup_ui(self):
        """Setup the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # Header with controls
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # Watchlist label with styling
        self.watchlist_label = QLabel("Active Watchlist: Default")
        title_font = QFont("Segoe UI", 12, QFont.Bold)
        self.watchlist_label.setFont(title_font)
        self.watchlist_label.setStyleSheet(f"color: {DarkThemeColors.ACCENT};")
        header_layout.addWidget(self.watchlist_label)
        
        header_layout.addStretch()
        
        # Futures positions button
        self.futures_btn = QPushButton("My Futures Positions")
        self.futures_btn.setMinimumHeight(32)
        self.futures_btn.setStyleSheet(f"""
            background-color: {DarkThemeColors.SUCCESS};
            color: black;
            font-weight: bold;
        """)
        self.futures_btn.clicked.connect(self._show_futures_positions)
        header_layout.addWidget(self.futures_btn)
        
        # Filter combo with styling
        self.filter_combo = QComboBox()
        self.filter_combo.setMinimumHeight(32)
        self.filter_combo.addItem("All Assets")
        self.filter_combo.addItem("Watchlist Only")
        self.filter_combo.addItem("With Balance Only")
        self.filter_combo.addItem("Top Gainers (24h)")
        self.filter_combo.addItem("Top Gainers (4h)")
        self.filter_combo.addItem("Futures Positions")
        
        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet(f"color: {DarkThemeColors.TEXT_SECONDARY};")
        header_layout.addWidget(filter_label)
        header_layout.addWidget(self.filter_combo)
        
        # Refresh button with styling
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setMinimumHeight(32)
        self.refresh_button.setMinimumWidth(100)
        self.refresh_button.setIcon(QIcon("app/ui/assets/refresh.png"))  # You may need to create this asset
        header_layout.addWidget(self.refresh_button)
        
        # Add to main layout
        main_layout.addLayout(header_layout)
        
        # Create a card-like container for the tables
        container = QFrame()
        container.setFrameShape(QFrame.StyledPanel)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {DarkThemeColors.CARD_BACKGROUND};
                border-radius: 8px;
                border: 1px solid {DarkThemeColors.BORDER};
            }}
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(15, 15, 15, 15)
        container_layout.setSpacing(15)
        
        # Create splitter for tables
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {DarkThemeColors.BORDER};
            }}
        """)
        container_layout.addWidget(splitter)
        
        # Assets table with styling
        self.assets_table = QTableWidget()
        self.assets_table.setColumnCount(6)
        self.assets_table.setHorizontalHeaderLabels([
            "Symbol", "Price", "24h Change", "Volume", "Balance", "Value (USDT)"
        ])
        self.assets_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.assets_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.assets_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.assets_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.assets_table.verticalHeader().setVisible(False)
        self.assets_table.setAlternatingRowColors(True)
        # Apply dark theme to table
        apply_dark_theme_to_table(self.assets_table)
        
        splitter.addWidget(self.assets_table)
        
        # Portfolio summary with styling
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)
        summary_layout.setContentsMargins(0, 10, 0, 0)
        
        summary_label = QLabel("Portfolio Summary")
        summary_font = QFont("Segoe UI", 12, QFont.Bold)
        summary_label.setFont(summary_font)
        summary_label.setStyleSheet(f"color: {DarkThemeColors.ACCENT}; margin-bottom: 5px;")
        summary_layout.addWidget(summary_label)
        
        # Summary table with styling
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(2)
        self.summary_table.setRowCount(3)
        self.summary_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.summary_table.setItem(0, 0, QTableWidgetItem("Total Assets"))
        self.summary_table.setItem(1, 0, QTableWidgetItem("Total Value (USDT)"))
        self.summary_table.setItem(2, 0, QTableWidgetItem("24h Change"))
        self.summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.summary_table.verticalHeader().setVisible(False)
        self.summary_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.summary_table.setAlternatingRowColors(True)
        self.summary_table.setMaximumHeight(150)
        apply_dark_theme_to_table(self.summary_table)
        summary_layout.addWidget(self.summary_table)
        
        splitter.addWidget(summary_widget)
        
        # Add the container to the main layout
        main_layout.addWidget(container)
        
        # Set splitter sizes
        splitter.setSizes([600, 100])
        
    def _connect_signals(self):
        """Connect signals from services and widgets."""
        # Connect portfolio manager signals
        self.portfolio_manager.portfolio_updated.connect(self.refresh_assets)
        self.portfolio_manager.asset_updated.connect(self._update_asset_row)
        self.portfolio_manager.watchlist_updated.connect(self._on_watchlist_updated)
        
        # Connect widget signals
        self.refresh_button.clicked.connect(self.refresh_assets)
        self.filter_combo.currentIndexChanged.connect(self.refresh_assets)
        self.assets_table.customContextMenuRequested.connect(self._show_context_menu)
        
    def _show_futures_positions(self):
        """Show the futures positions in the table."""
        # Set filter to Futures Positions
        self.filter_combo.setCurrentIndex(5)  # Index for Futures Positions
        
    def refresh_assets(self):
        """Refresh the assets table with current data."""
        # Update watchlist label
        active_watchlist = self.portfolio_manager.get_active_watchlist()
        self.watchlist_label.setText(f"Active Watchlist: {active_watchlist.name}")
        
        # Get assets based on filter
        filter_index = self.filter_combo.currentIndex()
        assets = []
        
        if filter_index == 0:  # All Assets
            assets = self.portfolio_manager.get_all_assets()
        elif filter_index == 1:  # Watchlist Only
            assets = self.portfolio_manager.get_watchlist_assets()
        elif filter_index == 2:  # With Balance Only
            assets = [a for a in self.portfolio_manager.get_all_assets() if a.balance > 0]
        elif filter_index == 3:  # Top Gainers (24h)
            assets = self.portfolio_manager.get_top_gainers(timeframe='24h', limit=20)
        elif filter_index == 4:  # Top Gainers (4h)
            assets = self.portfolio_manager.get_top_gainers(timeframe='4h', limit=20)
        elif filter_index == 5:  # Futures Positions
            # Update futures positions before displaying
            self.portfolio_manager.update_futures_positions()
            assets = self.portfolio_manager.get_watchlist_assets('futures_positions')
            
        # Update table
        self.assets_table.setRowCount(len(assets))
        
        for row, asset in enumerate(assets):
            self._update_asset_row(asset, row)
            
        # Update summary
        self._update_summary()
        
    def _update_asset_row(self, asset: Asset, row: Optional[int] = None):
        """Update or add a row for an asset.
        
        Args:
            asset: The asset to update
            row: Optional row index (searched if None)
        """
        # Find row if not provided
        if row is None:
            for i in range(self.assets_table.rowCount()):
                if self.assets_table.item(i, self.COL_SYMBOL).text() == asset.symbol:
                    row = i
                    break
                    
            # Not found - may be filtered out
            if row is None:
                return
        
        # Get active watchlist for reference
        active_watchlist = self.portfolio_manager.get_active_watchlist()
                
        # Create symbol item - store the actual symbol for API calls but display the formatted name
        symbol_item = QTableWidgetItem(asset.display_name)
        symbol_item.setData(Qt.UserRole, asset.symbol)  # Keep the raw symbol for API operations
        
        # Style based on position type for futures positions
        if asset.is_long or asset.is_short:
            position_color = DarkThemeColors.SUCCESS if asset.is_long else DarkThemeColors.ERROR
            symbol_item.setForeground(QBrush(QColor(position_color)))
            symbol_item.setToolTip(f"{asset.position_type} position with {asset.leverage}x leverage")
        # Set watchlist indicator with color
        elif active_watchlist.contains(asset.symbol):
            symbol_item.setForeground(QBrush(QColor(DarkThemeColors.SUCCESS)))
            symbol_item.setToolTip("In watchlist")
        
        self.assets_table.setItem(row, self.COL_SYMBOL, symbol_item)
        
        # Price data
        if asset.price_data:
            # Price
            price_item = QTableWidgetItem(f"{asset.price_data.price:.8f}")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.assets_table.setItem(row, self.COL_PRICE, price_item)
            
            # 24h Change with color
            change_24h = asset.price_data.change_24h_percent
            change_item = QTableWidgetItem(f"{change_24h:.2f}%")
            change_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            # Apply color based on change value
            change_item.setForeground(QBrush(get_color_for_change(change_24h)))
            self.assets_table.setItem(row, self.COL_CHANGE_24H, change_item)
            
            # Volume
            volume_item = QTableWidgetItem(f"{asset.price_data.volume_24h:.2f}")
            volume_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.assets_table.setItem(row, self.COL_VOLUME, volume_item)
        else:
            # No price data
            self.assets_table.setItem(row, self.COL_PRICE, QTableWidgetItem("N/A"))
            self.assets_table.setItem(row, self.COL_CHANGE_24H, QTableWidgetItem("N/A"))
            self.assets_table.setItem(row, self.COL_VOLUME, QTableWidgetItem("N/A"))
            
        # Balance
        balance_item = QTableWidgetItem(f"{asset.balance:.8f}")
        balance_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.assets_table.setItem(row, self.COL_BALANCE, balance_item)
        
        # Value
        value_item = QTableWidgetItem(f"{asset.value_usd:.2f}")
        value_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.assets_table.setItem(row, self.COL_VALUE, value_item)
        
    def _update_summary(self):
        """Update portfolio summary statistics."""
        assets = self.portfolio_manager.get_all_assets()
        
        # Total assets with balance
        assets_with_balance = sum(1 for asset in assets if asset.balance > 0)
        self.summary_table.setItem(0, 1, QTableWidgetItem(str(assets_with_balance)))
        
        # Total value
        total_value = sum(asset.value_usd for asset in assets)
        value_item = QTableWidgetItem(f"{total_value:.2f} USDT")
        self.summary_table.setItem(1, 1, value_item)
        
        # 24h change
        # Calculate weighted change based on asset values
        if total_value > 0:
            weighted_change = sum(
                asset.price_data.change_24h * asset.value_usd / total_value
                for asset in assets
                if asset.price_data and asset.value_usd > 0
            ) * 100
        else:
            weighted_change = 0
            
        change_item = QTableWidgetItem(f"{weighted_change:.2f}%")
        
        if weighted_change > 0:
            change_item.setForeground(QBrush(QColor(46, 204, 113)))  # Green
        elif weighted_change < 0:
            change_item.setForeground(QBrush(QColor(231, 76, 60)))  # Red
            
        self.summary_table.setItem(2, 1, change_item)
        
    def _show_context_menu(self, position):
        """Show context menu for asset table.
        
        Args:
            position: Position where menu should appear
        """
        menu = QMenu()
        
        # Get selected item
        selected_indexes = self.assets_table.selectedIndexes()
        if not selected_indexes:
            return
            
        # Get symbol from the selected row
        row = selected_indexes[0].row()
        symbol_item = self.assets_table.item(row, self.COL_SYMBOL)
        if not symbol_item:
            return
            
        symbol = symbol_item.text()
        active_watchlist = self.portfolio_manager.get_active_watchlist()
        
        # Add/remove from watchlist
        if active_watchlist.contains(symbol):
            remove_action = QAction(f"Remove from {active_watchlist.name}", self)
            remove_action.triggered.connect(
                lambda: self._remove_from_watchlist(symbol)
            )
            menu.addAction(remove_action)
        else:
            add_action = QAction(f"Add to {active_watchlist.name}", self)
            add_action.triggered.connect(
                lambda: self._add_to_watchlist(symbol)
            )
            menu.addAction(add_action)
            
        # Add to other watchlists submenu
        other_watchlists = [
            name for name in self.portfolio_manager.get_watchlists()
            if name != active_watchlist.name
        ]
        
        if other_watchlists:
            other_menu = menu.addMenu("Add to Other Watchlist")
            
            for name in other_watchlists:
                watchlist_action = QAction(name, self)
                watchlist_action.triggered.connect(
                    lambda checked=False, n=name: self._add_to_watchlist(symbol, n)
                )
                other_menu.addAction(watchlist_action)
                
        menu.addSeparator()
        
        # Strategy actions
        strategy_menu = menu.addMenu("Strategies")
        
        # Get assigned strategies
        assigned_strategies = self.strategy_manager.get_asset_strategy_ids(symbol)
        
        # Add strategies submenu
        if assigned_strategies:
            for strategy in self.strategy_manager.get_all_strategies():
                strategy_action = QAction(strategy.name, self)
                strategy_action.setCheckable(True)
                strategy_action.setChecked(strategy.strategy_id in assigned_strategies)
                strategy_action.triggered.connect(
                    lambda checked, s=strategy.strategy_id: 
                    self._toggle_strategy(symbol, s, checked)
                )
                strategy_menu.addAction(strategy_action)
        else:
            # No strategies assigned
            for strategy in self.strategy_manager.get_all_strategies():
                strategy_action = QAction(f"Assign {strategy.name}", self)
                strategy_action.triggered.connect(
                    lambda checked=False, s=strategy.strategy_id: 
                    self._assign_strategy(symbol, s)
                )
                strategy_menu.addAction(strategy_action)
                
        # Show menu
        menu.exec_(self.assets_table.mapToGlobal(position))
        
    def _add_to_watchlist(self, symbol: str, watchlist_name: Optional[str] = None):
        """Add a symbol to a watchlist.
        
        Args:
            symbol: Symbol to add
            watchlist_name: Optional watchlist name (uses active if None)
        """
        self.portfolio_manager.add_to_watchlist(symbol, watchlist_name)
        
    def _remove_from_watchlist(self, symbol: str, watchlist_name: Optional[str] = None):
        """Remove a symbol from a watchlist.
        
        Args:
            symbol: Symbol to remove
            watchlist_name: Optional watchlist name (uses active if None)
        """
        self.portfolio_manager.remove_from_watchlist(symbol, watchlist_name)
        
    def _assign_strategy(self, symbol: str, strategy_id: str):
        """Assign a strategy to an asset.
        
        Args:
            symbol: Asset symbol
            strategy_id: Strategy ID
        """
        self.strategy_manager.assign_strategy(symbol, strategy_id)
        
    def _remove_strategy(self, symbol: str, strategy_id: str):
        """Remove a strategy from an asset.
        
        Args:
            symbol: Asset symbol
            strategy_id: Strategy ID
        """
        self.strategy_manager.remove_strategy(symbol, strategy_id)
        
    def _toggle_strategy(self, symbol: str, strategy_id: str, assign: bool):
        """Toggle a strategy assignment.
        
        Args:
            symbol: Asset symbol
            strategy_id: Strategy ID
            assign: Whether to assign or remove
        """
        if assign:
            self._assign_strategy(symbol, strategy_id)
        else:
            self._remove_strategy(symbol, strategy_id)
            
    def _on_watchlist_updated(self, watchlist_name: str):
        """Handle watchlist updates.
        
        Args:
            watchlist_name: Name of the updated watchlist
        """
        # Update watchlist label if active watchlist changed
        active_watchlist = self.portfolio_manager.get_active_watchlist()
        if active_watchlist.name == watchlist_name:
            self.watchlist_label.setText(f"Active Watchlist: {active_watchlist.name}")
            
        # Refresh assets if we're showing watchlist only
        if self.filter_combo.currentIndex() == 1:
            self.refresh_assets()
