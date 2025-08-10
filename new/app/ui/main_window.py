"""
Main window of the application.
"""
import sys
import logging
from typing import Optional

from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QWidget, 
    QStatusBar, QAction, QMenu, QMenuBar, QMessageBox,
    QDialog, QDialogButtonBox, QFormLayout, QLabel,
    QLineEdit, QCheckBox
)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QIcon, QFont

from app.ui.portfolio_tab import PortfolioTab
from app.ui.signals_tab import SignalsTab
from app.ui.strategies_tab import StrategiesTab
from app.ui.theme import DarkThemeColors, apply_dark_theme_to_table

from app.services.binance_service import BinanceService
from app.services.portfolio_manager import PortfolioManager
from app.services.strategy_manager import StrategyManager

from app.config.settings import Settings


class ApiKeyDialog(QDialog):
    """Dialog for entering Binance API keys."""
    
    def __init__(self, parent=None, current_key="", current_secret=""):
        """Initialize API key dialog.
        
        Args:
            parent: Parent widget
            current_key: Current API key
            current_secret: Current API secret
        """
        super().__init__(parent)
        self.setWindowTitle("Binance API Keys")
        self.setMinimumWidth(450)
        
        # Setup layout
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Create widgets
        self.api_key_edit = QLineEdit(current_key)
        self.api_key_edit.setMinimumHeight(36)
        self.api_secret_edit = QLineEdit(current_secret)
        self.api_secret_edit.setMinimumHeight(36)
        self.api_secret_edit.setEchoMode(QLineEdit.Password)
        self.show_secret_check = QCheckBox("Show Secret")
        
        # Add widgets to layout
        layout.addRow("API Key:", self.api_key_edit)
        layout.addRow("API Secret:", self.api_secret_edit)
        layout.addRow("", self.show_secret_check)
        
        # Add information label
        info_label = QLabel(
            "Enter your Binance API key and secret to access your account data.\n"
            "For read-only access, ensure your API key has only 'Read' permissions."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {DarkThemeColors.TEXT_SECONDARY}; font-style: italic;")
        layout.addRow(info_label)
        
        # Add buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        layout.addRow(button_box)
        
        # Connect signals
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.show_secret_check.stateChanged.connect(self._toggle_secret_visibility)
        
    def _toggle_secret_visibility(self, state):
        """Toggle visibility of API secret."""
        self.api_secret_edit.setEchoMode(
            QLineEdit.Normal if state == Qt.Checked else QLineEdit.Password
        )
        
    def get_api_credentials(self):
        """Get the entered API credentials.
        
        Returns:
            tuple: (API key, API secret)
        """
        return (self.api_key_edit.text(), self.api_secret_edit.text())


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        # Configure logging
        self._setup_logging()
        
        # Initialize settings
        self.settings = Settings()
        
        # Initialize services
        self.binance_service = BinanceService(self.settings)
        self.portfolio_manager = PortfolioManager(self.settings, self.binance_service)
        self.strategy_manager = StrategyManager(self.settings, self.binance_service)
        
        # Setup UI
        self._setup_ui()
        
        # Connect signals
        self._connect_signals()
        
        # Start data updates
        self._start_data_updates()
        
    def _setup_logging(self):
        """Setup logging for the application."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def _setup_ui(self):
        """Setup the user interface."""
        # Configure window
        self.setWindowTitle("Crypto Portfolio Manager")
        self.setMinimumSize(1000, 700)
        self.setWindowIcon(QIcon("app/ui/assets/icon.png"))
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Create app title label
        title_label = QLabel("Crypto Portfolio Manager")
        title_font = QFont("Segoe UI", 16, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {DarkThemeColors.ACCENT}; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Create tab widget with styling
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)  # Cleaner look
        self.tab_widget.setTabPosition(QTabWidget.North)
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.portfolio_tab = PortfolioTab(
            self.binance_service, 
            self.portfolio_manager, 
            self.strategy_manager
        )
        self.signals_tab = SignalsTab(
            self.binance_service, 
            self.portfolio_manager, 
            self.strategy_manager
        )
        self.strategies_tab = StrategiesTab(
            self.binance_service, 
            self.portfolio_manager, 
            self.strategy_manager
        )
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.portfolio_tab, "Portfolio")
        self.tab_widget.addTab(self.signals_tab, "Signals")
        self.tab_widget.addTab(self.strategies_tab, "Strategies")
        
        # Create status bar with styling
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(f"background-color: {DarkThemeColors.CARD_BACKGROUND};")
        self.setStatusBar(self.status_bar)
        
        # Create connection status label
        self.connection_status_label = QLabel("Not connected")
        self.connection_status_label.setStyleSheet(f"color: {DarkThemeColors.WARNING};")
        self.status_bar.addPermanentWidget(self.connection_status_label)
        
        # Create menu bar
        self._create_menus()
        
        # Load window state
        self._load_window_state()
        
    def _create_menus(self):
        """Create application menus."""
        # File menu
        file_menu = self.menuBar().addMenu("&File")
        
        api_keys_action = QAction("Binance API Keys...", self)
        api_keys_action.triggered.connect(self._show_api_key_dialog)
        file_menu.addAction(api_keys_action)
        
        refresh_action = QAction("Refresh Data", self)
        refresh_action.triggered.connect(self._refresh_data)
        refresh_action.setShortcut("F5")
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = self.menuBar().addMenu("&View")
        
        # Futures positions action
        futures_positions_action = QAction("My Futures Positions", self)
        futures_positions_action.setIcon(QIcon("app/ui/assets/futures.png"))  # You may need to create this asset
        futures_positions_action.triggered.connect(self._show_futures_positions)
        futures_positions_action.setStatusTip("View your active Binance Futures positions")
        view_menu.addAction(futures_positions_action)
        
        view_menu.addSeparator()
        
        watchlist_menu = QMenu("Watchlists", self)
        view_menu.addMenu(watchlist_menu)
        
        self.watchlist_actions = {}
        for name in self.portfolio_manager.get_watchlists():
            action = QAction(name, self)
            action.setCheckable(True)
            action.setData(name)
            action.triggered.connect(self._on_watchlist_selected)
            watchlist_menu.addAction(action)
            self.watchlist_actions[name] = action
            
        watchlist_menu.addSeparator()
        
        new_watchlist_action = QAction("New Watchlist...", self)
        new_watchlist_action.triggered.connect(self._create_new_watchlist)
        watchlist_menu.addAction(new_watchlist_action)
        
        # Help menu
        help_menu = self.menuBar().addMenu("&Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)
        
    def _connect_signals(self):
        """Connect signals from services."""
        # Connect Binance service signals
        self.binance_service.connection_status_changed.connect(
            self._on_connection_status_changed
        )
        self.binance_service.error_occurred.connect(
            self._on_error_occurred
        )
        
        # Connect portfolio manager signals
        self.portfolio_manager.portfolio_updated.connect(
            self._on_portfolio_updated
        )
        self.portfolio_manager.watchlist_updated.connect(
            self._on_watchlist_updated
        )
        
    def _start_data_updates(self):
        """Start automatic data updates."""
        # Start price updates for watched assets
        self.portfolio_manager.start_price_updates()
        
        # Start auto-refresh for signals
        self.strategy_manager.start_auto_refresh()
        
    def _load_window_state(self):
        """Load window state from settings."""
        qsettings = QSettings("CryptoPortfolioManager", "MainWindow")
        if qsettings.contains("geometry"):
            self.restoreGeometry(qsettings.value("geometry"))
        if qsettings.contains("windowState"):
            self.restoreState(qsettings.value("windowState"))
            
    def _save_window_state(self):
        """Save window state to settings."""
        qsettings = QSettings("CryptoPortfolioManager", "MainWindow")
        qsettings.setValue("geometry", self.saveGeometry())
        qsettings.setValue("windowState", self.saveState())
        
    def closeEvent(self, event):
        """Handle window close event."""
        # Save window state
        self._save_window_state()
        
        # Save settings and portfolio
        self.portfolio_manager.save_portfolio()
        
        # Close connections
        self.binance_service.close_connections()
        
        # Accept the event
        event.accept()
        
    def _show_api_key_dialog(self):
        """Show dialog for entering API keys."""
        api_key = self.settings.get('api_key', '')
        api_secret = self.settings.get('api_secret', '')
        
        dialog = ApiKeyDialog(self, api_key, api_secret)
        if dialog.exec_() == QDialog.Accepted:
            new_key, new_secret = dialog.get_api_credentials()
            self.binance_service.update_credentials(new_key, new_secret)
            
            # Sync portfolio with Binance account
            if new_key and new_secret:
                self.portfolio_manager.sync_with_binance_account()
                
    def _refresh_data(self):
        """Refresh all data."""
        # Refresh prices
        self.portfolio_manager.refresh_all_prices()
        
        # Refresh futures positions if we have API keys
        if self.settings.get('api_key') and self.settings.get('api_secret'):
            self.portfolio_manager.update_futures_positions()
        
        # Refresh signals
        self.strategy_manager.refresh_all_signals()
        
        # Update status bar
        self.status_bar.showMessage("Data refreshed", 3000)
        
    def _show_futures_positions(self):
        """Show futures positions tab."""
        # Switch to portfolio tab and show futures positions
        self.tab_widget.setCurrentWidget(self.portfolio_tab)
        self.portfolio_tab._show_futures_positions()
    def _create_new_watchlist(self):
        """Create a new watchlist."""
        from PyQt5.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(
            self, "New Watchlist", "Enter watchlist name:"
        )
        
        if ok and name:
            if self.portfolio_manager.create_watchlist(name):
                # Add to menu
                action = QAction(name, self)
                action.setCheckable(True)
                action.setData(name)
                action.triggered.connect(self._on_watchlist_selected)
                
                watchlist_menu = None
                for menu in self.menuBar().findChildren(QMenu):
                    if menu.title() == "Watchlists":
                        watchlist_menu = menu
                        break
                        
                if watchlist_menu:
                    # Find position before the separator
                    actions = watchlist_menu.actions()
                    sep_index = next(
                        (i for i, a in enumerate(actions) if a.isSeparator()), 
                        len(actions)
                    )
                    watchlist_menu.insertAction(actions[sep_index], action)
                    
                self.watchlist_actions[name] = action
                
                # Set as active
                self.portfolio_manager.set_active_watchlist(name)
            else:
                QMessageBox.warning(
                    self, 
                    "Watchlist Error", 
                    f"Watchlist '{name}' already exists"
                )
                
    def _show_about_dialog(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Crypto Portfolio Manager",
            "Crypto Portfolio Manager\n\n"
            "A PyQt5 application for managing cryptocurrency portfolios, "
            "tracking signals, and configuring trading strategies.\n\n"
            "Uses Binance API for market data and account information."
        )
        
    def _on_connection_status_changed(self, connected, message):
        """Handle connection status changes.
        
        Args:
            connected: Whether connected to the API
            message: Status message
        """
        if connected:
            self.connection_status_label.setText(f"✓ {message}")
            self.connection_status_label.setStyleSheet(f"color: {DarkThemeColors.SUCCESS}; font-weight: bold;")
        else:
            self.connection_status_label.setText(f"✗ {message}")
            self.connection_status_label.setStyleSheet(f"color: {DarkThemeColors.ERROR}; font-weight: bold;")
            
    def _on_error_occurred(self, error_message):
        """Handle errors from services.
        
        Args:
            error_message: Error message
        """
        self.status_bar.showMessage(error_message, 5000)
        # Create a more visible error notification
        QMessageBox.warning(
            self,
            "Error",
            error_message,
            QMessageBox.Ok
        )
        self.logger.error(error_message)
        
    def _on_portfolio_updated(self):
        """Handle portfolio updates."""
        # Update watchlist actions
        watchlists = self.portfolio_manager.get_watchlists()
        
        # Add new watchlists
        for name in watchlists:
            if name not in self.watchlist_actions:
                action = QAction(name, self)
                action.setCheckable(True)
                action.setData(name)
                action.triggered.connect(self._on_watchlist_selected)
                
                watchlist_menu = None
                for menu in self.menuBar().findChildren(QMenu):
                    if menu.title() == "Watchlists":
                        watchlist_menu = menu
                        break
                        
                if watchlist_menu:
                    # Find position before the separator
                    actions = watchlist_menu.actions()
                    sep_index = next(
                        (i for i, a in enumerate(actions) if a.isSeparator()), 
                        len(actions)
                    )
                    watchlist_menu.insertAction(actions[sep_index], action)
                    
                self.watchlist_actions[name] = action
                
        # Remove deleted watchlists
        for name in list(self.watchlist_actions.keys()):
            if name not in watchlists:
                action = self.watchlist_actions[name]
                
                watchlist_menu = None
                for menu in self.menuBar().findChildren(QMenu):
                    if menu.title() == "Watchlists":
                        watchlist_menu = menu
                        break
                        
                if watchlist_menu:
                    watchlist_menu.removeAction(action)
                    
                del self.watchlist_actions[name]
                
    def _on_watchlist_updated(self, watchlist_name):
        """Handle watchlist updates.
        
        Args:
            watchlist_name: Name of the updated watchlist
        """
        # Update watchlist action check state
        active_watchlist = self.portfolio_manager.get_active_watchlist().name
        
        for name, action in self.watchlist_actions.items():
            action.setChecked(name == active_watchlist)
            
    def _on_watchlist_selected(self):
        """Handle watchlist selection from menu."""
        action = self.sender()
        if action and action.isCheckable():
            name = action.data()
            if name:
                self.portfolio_manager.set_active_watchlist(name)
                
                # Update tabs
                self.portfolio_tab.refresh_assets()
                self.signals_tab.refresh_signals()
