"""
Strategies tab for configuring trading strategies.
"""
import logging
from typing import Dict, List, Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QHeaderView, QMenu, QAction,
    QAbstractItemView, QDialog, QDialogButtonBox, QFormLayout,
    QLineEdit, QSpinBox, QDoubleSpinBox, QGroupBox, QListWidget,
    QListWidgetItem, QSplitter, QGridLayout, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QColor, QBrush, QFont, QIcon

from app.services.binance_service import BinanceService
from app.services.portfolio_manager import PortfolioManager
from app.services.strategy_manager import StrategyManager
from app.models.strategy import Strategy
from app.ui.theme import DarkThemeColors, apply_dark_theme_to_table, get_color_for_change


class StrategyConfigDialog(QDialog):
    """Dialog for configuring strategy parameters."""
    
    def __init__(self, parent=None, strategy: Optional[Strategy] = None):
        """Initialize strategy config dialog.
        
        Args:
            parent: Parent widget
            strategy: Strategy to configure
        """
        super().__init__(parent)
        
        if not strategy:
            self.reject()
            return
            
        self.strategy = strategy
        self.parameter_widgets = {}
        
        self.setWindowTitle(f"Configure {strategy.name}")
        self.setMinimumWidth(400)
        
        # Setup layout
        layout = QVBoxLayout(self)
        
        # Strategy info
        info_label = QLabel(strategy.description)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Parameters form
        form_layout = QFormLayout()
        
        for param_name, param_value in strategy.parameters.items():
            if isinstance(param_value, int):
                # Integer parameter
                spin_box = QSpinBox()
                spin_box.setMinimum(1)
                spin_box.setMaximum(1000)
                spin_box.setValue(param_value)
                form_layout.addRow(param_name, spin_box)
                self.parameter_widgets[param_name] = spin_box
            elif isinstance(param_value, float):
                # Float parameter
                double_spin = QDoubleSpinBox()
                double_spin.setMinimum(0.0)
                double_spin.setMaximum(100.0)
                double_spin.setSingleStep(0.1)
                double_spin.setValue(param_value)
                form_layout.addRow(param_name, double_spin)
                self.parameter_widgets[param_name] = double_spin
            else:
                # String parameter
                line_edit = QLineEdit(str(param_value))
                form_layout.addRow(param_name, line_edit)
                self.parameter_widgets[param_name] = line_edit
                
        layout.addLayout(form_layout)
        
        # Add buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        layout.addWidget(button_box)
        
        # Connect signals
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
    def get_parameters(self) -> Dict:
        """Get the configured parameters.
        
        Returns:
            Dict: Parameter name -> value mapping
        """
        result = {}
        
        for param_name, widget in self.parameter_widgets.items():
            if isinstance(widget, QSpinBox) or isinstance(widget, QDoubleSpinBox):
                result[param_name] = widget.value()
            else:
                result[param_name] = widget.text()
                
        return result


class StrategiesTab(QWidget):
    """Tab for strategy management."""
    
    def __init__(
        self, 
        binance_service: BinanceService, 
        portfolio_manager: PortfolioManager,
        strategy_manager: StrategyManager
    ):
        """Initialize the strategies tab.
        
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
        self.refresh_strategies()
        self.refresh_assignments()
        
    def _setup_ui(self):
        """Setup the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create splitter for two panels
        splitter = QSplitter()
        main_layout.addWidget(splitter)
        
        # Left panel - strategies list
        strategies_panel = QWidget()
        strategies_layout = QVBoxLayout(strategies_panel)
        
        # Strategies label
        strategies_label = QLabel("Available Strategies")
        strategies_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        strategies_layout.addWidget(strategies_label)
        
        # Strategies table
        self.strategies_table = QTableWidget()
        self.strategies_table.setColumnCount(2)
        self.strategies_table.setHorizontalHeaderLabels(["Strategy", "Description"])
        self.strategies_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.strategies_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.strategies_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.strategies_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )
        self.strategies_table.verticalHeader().setVisible(False)
        strategies_layout.addWidget(self.strategies_table)
        
        # Configure button
        self.configure_button = QPushButton("Configure Selected Strategy")
        strategies_layout.addWidget(self.configure_button)
        
        # Add to splitter
        splitter.addWidget(strategies_panel)
        
        # Right panel - assignments
        assignments_panel = QWidget()
        assignments_layout = QVBoxLayout(assignments_panel)
        
        # Assignments label
        assignments_label = QLabel("Strategy Assignments")
        assignments_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        assignments_layout.addWidget(assignments_label)
        
        # Assignments table
        self.assignments_table = QTableWidget()
        self.assignments_table.setColumnCount(2)
        self.assignments_table.setHorizontalHeaderLabels(["Asset", "Assigned Strategies"])
        self.assignments_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.assignments_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.assignments_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.assignments_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )
        self.assignments_table.verticalHeader().setVisible(False)
        assignments_layout.addWidget(self.assignments_table)
        
        # Assignment control buttons
        buttons_layout = QHBoxLayout()
        
        self.add_assignment_button = QPushButton("Add Assignment")
        buttons_layout.addWidget(self.add_assignment_button)
        
        self.remove_assignment_button = QPushButton("Remove Assignment")
        buttons_layout.addWidget(self.remove_assignment_button)
        
        assignments_layout.addLayout(buttons_layout)
        
        # Add to splitter
        splitter.addWidget(assignments_panel)
        
        # Set splitter sizes
        splitter.setSizes([400, 400])
        
    def _connect_signals(self):
        """Connect signals from services and widgets."""
        # Connect strategy manager signals
        self.strategy_manager.strategy_assigned.connect(
            lambda symbol, strategy_id: self.refresh_assignments()
        )
        self.strategy_manager.strategy_removed.connect(
            lambda symbol, strategy_id: self.refresh_assignments()
        )
        
        # Connect widget signals
        self.strategies_table.customContextMenuRequested.connect(
            self._show_strategy_context_menu
        )
        self.assignments_table.customContextMenuRequested.connect(
            self._show_assignment_context_menu
        )
        self.configure_button.clicked.connect(self._configure_selected_strategy)
        self.add_assignment_button.clicked.connect(self._add_assignment)
        self.remove_assignment_button.clicked.connect(self._remove_assignment)
        
    def refresh_strategies(self):
        """Refresh the strategies table."""
        strategies = self.strategy_manager.get_all_strategies()
        
        self.strategies_table.setRowCount(len(strategies))
        
        for row, strategy in enumerate(strategies):
            # Strategy name
            name_item = QTableWidgetItem(strategy.name)
            name_item.setData(Qt.UserRole, strategy.strategy_id)
            self.strategies_table.setItem(row, 0, name_item)
            
            # Strategy description
            desc_item = QTableWidgetItem(strategy.description)
            self.strategies_table.setItem(row, 1, desc_item)
            
    def refresh_assignments(self):
        """Refresh the assignments table."""
        # Get all assets with strategies
        assets_with_strategies = self.strategy_manager.get_assets_with_strategies()
        
        self.assignments_table.setRowCount(len(assets_with_strategies))
        
        for row, symbol in enumerate(assets_with_strategies):
            # Find the asset object to get display name
            asset = None
            for a in self.portfolio_manager.get_all_assets():
                if a.base_symbol == symbol:
                    asset = a
                    break
            
            # Asset symbol - display the formatted name but store the base symbol for API calls
            display_text = asset.display_name if asset else symbol
            symbol_item = QTableWidgetItem(display_text)
            symbol_item.setData(Qt.UserRole, symbol)  # Store the base symbol for API operations
            self.assignments_table.setItem(row, 0, symbol_item)
            
            # Assigned strategies
            strategy_ids = self.strategy_manager.get_asset_strategy_ids(symbol)
            strategy_names = []
            
            for strategy_id in strategy_ids:
                strategy = self.strategy_manager.get_strategy(strategy_id)
                if strategy:
                    strategy_names.append(strategy.name)
                    
            strategies_item = QTableWidgetItem(", ".join(strategy_names))
            self.assignments_table.setItem(row, 1, strategies_item)
            
    def _show_strategy_context_menu(self, position):
        """Show context menu for strategies table.
        
        Args:
            position: Position where menu should appear
        """
        menu = QMenu()
        
        # Get selected item
        selected_indexes = self.strategies_table.selectedIndexes()
        if not selected_indexes:
            return
            
        # Get strategy from the selected row
        row = selected_indexes[0].row()
        strategy_item = self.strategies_table.item(row, 0)
        if not strategy_item:
            return
            
        strategy_id = strategy_item.data(Qt.UserRole)
        strategy = self.strategy_manager.get_strategy(strategy_id)
        
        if not strategy:
            return
            
        # Configure action
        configure_action = QAction(f"Configure {strategy.name}", self)
        configure_action.triggered.connect(
            lambda: self._configure_strategy(strategy)
        )
        menu.addAction(configure_action)
        
        # Show menu
        menu.exec_(self.strategies_table.mapToGlobal(position))
        
    def _show_assignment_context_menu(self, position):
        """Show context menu for assignments table.
        
        Args:
            position: Position where menu should appear
        """
        menu = QMenu()
        
        # Get selected item
        selected_indexes = self.assignments_table.selectedIndexes()
        if not selected_indexes:
            return
            
        # Get symbol from the selected row
        row = selected_indexes[0].row()
        symbol_item = self.assignments_table.item(row, 0)
        if not symbol_item:
            return
            
        # Get the base symbol from user data for API operations
        symbol = symbol_item.data(Qt.UserRole)
        
        # Get assigned strategies
        assigned_strategies = self.strategy_manager.get_asset_strategy_ids(symbol)
        
        # Add strategies submenu
        strategy_menu = menu.addMenu("Manage Strategies")
        
        for strategy in self.strategy_manager.get_all_strategies():
            strategy_action = QAction(strategy.name, self)
            strategy_action.setCheckable(True)
            strategy_action.setChecked(strategy.strategy_id in assigned_strategies)
            strategy_action.triggered.connect(
                lambda checked, s=strategy.strategy_id: 
                self._toggle_strategy(symbol, s, checked)
            )
            strategy_menu.addAction(strategy_action)
            
        # Remove all strategies action
        menu.addSeparator()
        remove_all_action = QAction(f"Remove All Strategies from {symbol}", self)
        remove_all_action.triggered.connect(
            lambda: self._remove_all_strategies(symbol)
        )
        menu.addAction(remove_all_action)
        
        # Show menu
        menu.exec_(self.assignments_table.mapToGlobal(position))
        
    def _configure_selected_strategy(self):
        """Configure the selected strategy."""
        # Get selected strategy
        selected_indexes = self.strategies_table.selectedIndexes()
        if not selected_indexes:
            return
            
        # Get strategy from the selected row
        row = selected_indexes[0].row()
        strategy_item = self.strategies_table.item(row, 0)
        if not strategy_item:
            return
            
        strategy_id = strategy_item.data(Qt.UserRole)
        strategy = self.strategy_manager.get_strategy(strategy_id)
        
        if strategy:
            self._configure_strategy(strategy)
            
    def _configure_strategy(self, strategy: Strategy):
        """Show dialog to configure a strategy.
        
        Args:
            strategy: Strategy to configure
        """
        dialog = StrategyConfigDialog(self, strategy)
        
        if dialog.exec_() == QDialog.Accepted:
            # Update strategy parameters
            parameters = dialog.get_parameters()
            
            for name, value in parameters.items():
                strategy.set_parameter(name, value)
                
            # Refresh signals using this strategy
            self.strategy_manager.refresh_all_signals()
            
    def _add_assignment(self):
        """Add a new strategy assignment."""
        # Create dialog to select asset and strategy
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Strategy Assignment")
        dialog.setMinimumWidth(400)
        
        # Setup layout
        layout = QFormLayout(dialog)
        
        # Asset combo
        asset_combo = QComboBox()
        assets = self.portfolio_manager.get_all_assets()
        for asset in assets:
            # Use display_name for UI but store base_symbol as user data for API calls
            asset_combo.addItem(asset.display_name, asset.base_symbol)
            
        layout.addRow("Asset:", asset_combo)
        
        # Strategy combo
        strategy_combo = QComboBox()
        strategies = self.strategy_manager.get_all_strategies()
        for strategy in strategies:
            strategy_combo.addItem(strategy.name, strategy.strategy_id)
            
        layout.addRow("Strategy:", strategy_combo)
        
        # Add buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        layout.addRow(button_box)
        
        # Connect signals
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        
        if dialog.exec_() == QDialog.Accepted:
            # Get the base symbol from user data (for API calls) rather than display text
            symbol = asset_combo.currentData()
            strategy_id = strategy_combo.currentData()
            
            self.strategy_manager.assign_strategy(symbol, strategy_id)
            
    def _remove_assignment(self):
        """Remove a strategy assignment."""
        # Get selected assignment
        selected_indexes = self.assignments_table.selectedIndexes()
        if not selected_indexes:
            return
            
        # Get symbol from the selected row
        row = selected_indexes[0].row()
        symbol_item = self.assignments_table.item(row, 0)
        if not symbol_item:
            return
            
        # Get the base symbol from user data for API operations
        symbol = symbol_item.data(Qt.UserRole)
        
        # Create dialog to select strategy to remove
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Remove Strategy from {symbol}")
        dialog.setMinimumWidth(400)
        
        # Setup layout
        layout = QFormLayout(dialog)
        
        # Strategy combo
        strategy_combo = QComboBox()
        assigned_strategy_ids = self.strategy_manager.get_asset_strategy_ids(symbol)
        
        for strategy_id in assigned_strategy_ids:
            strategy = self.strategy_manager.get_strategy(strategy_id)
            if strategy:
                strategy_combo.addItem(strategy.name, strategy_id)
                
        layout.addRow("Strategy to Remove:", strategy_combo)
        
        # Add buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        layout.addRow(button_box)
        
        # Connect signals
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        
        if dialog.exec_() == QDialog.Accepted and strategy_combo.count() > 0:
            strategy_id = strategy_combo.currentData()
            
            self.strategy_manager.remove_strategy(symbol, strategy_id)
            
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
            
    def _remove_all_strategies(self, symbol: str):
        """Remove all strategies from an asset.
        
        Args:
            symbol: Asset symbol
        """
        assigned_strategy_ids = self.strategy_manager.get_asset_strategy_ids(symbol)
        
        for strategy_id in list(assigned_strategy_ids):
            self.strategy_manager.remove_strategy(symbol, strategy_id)
