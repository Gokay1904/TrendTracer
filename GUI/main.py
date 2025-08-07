
import sys
import requests
import pandas as pd
import mplfinance as mpf
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QTabWidget

STOCKS = [
    "btcusdt", "ethusdt", "bnbusdt", "adausdt", "solusdt", "xrpusdt", "dogeusdt", "maticusdt", "ltcusdt", "trxusdt",
    "dotusdt", "shibusdt", "avaxusdt", "uniusdt", "linkusdt", "atomusdt", "etcusdt", "filusdt", "aptusdt", "nearusdt"
]
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QLineEdit, QFormLayout, QDialog, QSizePolicy, QComboBox, QListWidget, QListWidgetItem, QGridLayout, QSplitter, QApplication
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QSize
from PyQt5.QtGui import QColor, QIcon, QPainter, QBrush, QFont
class GlowCircle(QLabel):
    def __init__(self, color=QColor("gray")):
        super().__init__()
        self._color = color
        self.setFixedSize(32, 32)
        self.setStyleSheet("background: transparent;")
        self._glow = False
    def setColor(self, color, glow=False):
        self._color = QColor(color)
        self._glow = glow
        self.update()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if self._glow:
            glow_color = QColor(self._color)
            glow_color.setAlpha(120)
            painter.setBrush(QBrush(glow_color))
            painter.drawEllipse(2, 2, 28, 28)
        painter.setBrush(QBrush(self._color))
        painter.drawEllipse(6, 6, 20, 20)

class StrategySettings(QWidget):
    def __init__(self, strategy_name, on_params_changed=None):
        super().__init__()
        self.strategy_name = strategy_name
        self.on_params_changed = on_params_changed
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(QLabel(f"Settings for {strategy_name}"))
        if strategy_name == "Momentum":
            self.momentum_edit = QLineEdit("0")
            form = QFormLayout()
            form.addRow("Momentum:", self.momentum_edit)
            self.layout().addLayout(form)
            self.momentum_edit.textChanged.connect(self.params_changed)
        elif strategy_name == "Stick Strategy":
            self.stick_count_edit = QLineEdit("3")
            self.avg_edit = QLineEdit("0")
            form = QFormLayout()
            form.addRow("Peşpeşe stick sayısı:", self.stick_count_edit)
            form.addRow("Sticklerin ortalaması:", self.avg_edit)
            self.layout().addLayout(form)
            self.stick_count_edit.textChanged.connect(self.params_changed)
            self.avg_edit.textChanged.connect(self.params_changed)
    def get_params(self):
        try:
            stick_count = int(self.stick_count_edit.text())
        except Exception:
            stick_count = 3
        try:
            avg = float(self.avg_edit.text())
        except Exception:
            avg = 0.0
        try:
            momentum = float(self.momentum_edit.text())
        except Exception:
            momentum = 0.0
        return {"stick_count": stick_count, "avg": avg, "momentum": momentum}
    def params_changed(self):
        if self.on_params_changed:
            self.on_params_changed()
        # Strategy signal logic should be handled in the agent, not here

    def update_strategy_signal(self, symbol, price, prev_price):
        pass
class StrategiesTab(QWidget):
    def __init__(self, agent, get_selected_stocks):
        super().__init__()
        self.agent = agent
        self.get_selected_stocks = get_selected_stocks
        self.strategies = [
            ("Momentum", "./momentum.png"),
            ("Stick Strategy", "./stick.png"),
            ("Mean Reversion", "./meanreversion.png"),
            ("Breakout", "./breakout.png"),
            ("Scalping", "./scalping.png")
        ]
        vbox = QVBoxLayout()
        self.button_bar = QHBoxLayout()
        self.settings_stack = QStackedWidget()
        self.signal_labels = []
        self.strategy_settings = []
        self.detail_labels = []
        for idx, (name, icon_path) in enumerate(self.strategies):
            btn = QPushButton()
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(48, 48))
            btn.setText(name)
            btn.setStyleSheet("font-size: 16px; padding: 10px;")
            btn.clicked.connect(lambda checked, i=idx: self.settings_stack.setCurrentIndex(i))
            self.button_bar.addWidget(btn)

            # Settings panel with signals
            panel = QWidget()
            panel_layout = QVBoxLayout()
            settings_widget = StrategySettings(name, on_params_changed=self.on_params_changed)
            self.strategy_settings.append(settings_widget)
            panel_layout.addWidget(settings_widget)
            set_btn = QPushButton("Apply for all stocks")
            set_btn.setStyleSheet("font-size: 14px; margin: 8px;")
            set_btn.clicked.connect(lambda checked, n=name, i=idx: self.apply_for_all(n, i))
            panel_layout.addWidget(set_btn)
            signals_label = QLabel("Signals:")
            panel_layout.addWidget(signals_label)
            self.signal_labels.append(QLabel("No signals yet."))
            panel_layout.addWidget(self.signal_labels[-1])
            detail_label = QLabel("")
            self.detail_labels.append(detail_label)
            panel_layout.addWidget(detail_label)
            panel.setLayout(panel_layout)
            self.settings_stack.addWidget(panel)
        # Strategy Matrix Tab
        self.matrix_tab = QWidget()
        matrix_layout = QVBoxLayout()
        self.matrix_table = QTableWidget()
        self.matrix_table.setColumnCount(len(self.strategies)+1)
        self.matrix_table.setHorizontalHeaderLabels(["Hisse"] + [s[0] for s in self.strategies])
        self.matrix_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        matrix_layout.addWidget(self.matrix_table)
        self.matrix_table.setColumnCount(len(self.strategies)+2)
        self.matrix_table.setHorizontalHeaderLabels(["Hisse", "Fiyat"] + [s[0] for s in self.strategies])
        # Strateji toggle butonları
        self.strategy_active = {s[0]: True for s in self.strategies}
        self.strategy_buttons = []
        btn_bar = QHBoxLayout()
        for idx, (name, _) in enumerate(self.strategies):
            btn = QPushButton(f"{name} Aktif")
            btn.setCheckable(True)
            btn.setChecked(True)
            btn.clicked.connect(lambda checked, i=idx, n=name: self.toggle_strategy(i, n, checked))
            self.strategy_buttons.append(btn)
            btn_bar.addWidget(btn)
        matrix_layout.addLayout(btn_bar)
        self.matrix_tab.setLayout(matrix_layout)
        # Tabları ekle
        self.tabs = QTabWidget()
        self.tabs.addTab(QWidget(), "Strateji Paneli")
        self.tabs.addTab(self.matrix_tab, "Strategy Matrix")
        vbox.addLayout(self.button_bar)
        vbox.addWidget(self.settings_stack)
        vbox.addWidget(self.tabs)
        self.setLayout(vbox)
        self.update_matrix()

    def toggle_strategy(self, idx, name, checked):
        self.strategy_active[name] = checked
        self.strategy_buttons[idx].setText(f"{name} {'Aktif' if checked else 'Deaktif'}")
        self.update_matrix()

    def update_matrix(self):
        stocks = self.get_selected_stocks()
        self.matrix_table.setRowCount(len(stocks))
        for row, symbol in enumerate(stocks):
            self.matrix_table.setItem(row, 0, QTableWidgetItem(symbol.upper()))
            for col, (strategy, _) in enumerate(self.strategies):
                cell = QTableWidgetItem()
                if self.strategy_active[strategy]:
                    sig = getattr(self.agent, 'strategy_signals', {}).get(symbol, "WAIT")
                    if sig == "ACTIVE" or sig == "BUY":
                        cell.setBackground(QColor("green"))
                        cell.setText(sig)
                    elif sig == "SELL":
                        cell.setBackground(QColor("red"))
                        cell.setText(sig)
                    else:
                        cell.setBackground(QColor("gray"))
                        cell.setText(sig)
                else:
                    cell.setText("–")
                self.matrix_table.setItem(row, col+1, cell)

    def on_params_changed(self):
        self.update_signals()

    def apply_for_all(self, strategy_name, idx):
        params = self.strategy_settings[idx].get_params()
        stocks = self.get_selected_stocks()
class StrategiesTab(QWidget):
    def __init__(self, agent, get_selected_stocks):
        super().__init__()
        self.agent = agent
        self.get_selected_stocks = get_selected_stocks
        self.strategies = [
            ("Momentum", "./momentum.png"),
            ("Stick Strategy", "./stick.png"),
            ("Mean Reversion", "./meanreversion.png"),
            ("Breakout", "./breakout.png"),
            ("Scalping", "./scalping.png")
        ]
        vbox = QVBoxLayout()
        self.button_bar = QHBoxLayout()
        self.settings_stack = QStackedWidget()
        self.signal_labels = []
        self.strategy_settings = []
        self.detail_labels = []
        for idx, (name, icon_path) in enumerate(self.strategies):
            btn = QPushButton()
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(48, 48))
            btn.setText(name)
            btn.setStyleSheet("font-size: 16px; padding: 10px;")
            btn.clicked.connect(lambda checked, i=idx: self.settings_stack.setCurrentIndex(i))
            self.button_bar.addWidget(btn)
            # Settings panel with signals
            panel = QWidget()
            panel_layout = QVBoxLayout()
            settings_widget = StrategySettings(name, on_params_changed=self.on_params_changed)
            self.strategy_settings.append(settings_widget)
            panel_layout.addWidget(settings_widget)
            set_btn = QPushButton("Apply for all stocks")
            set_btn.setStyleSheet("font-size: 14px; margin: 8px;")
            set_btn.clicked.connect(lambda checked, n=name, i=idx: self.apply_for_all(n, i))
            panel_layout.addWidget(set_btn)
            signals_label = QLabel("Signals:")
            panel_layout.addWidget(signals_label)
            self.signal_labels.append(QLabel("No signals yet."))
            panel_layout.addWidget(self.signal_labels[-1])
            detail_label = QLabel("")
            self.detail_labels.append(detail_label)
            panel_layout.addWidget(detail_label)
            panel.setLayout(panel_layout)
            self.settings_stack.addWidget(panel)
        # Strategy Matrix Tab
        self.matrix_tab = QWidget()
        matrix_layout = QVBoxLayout()
        self.matrix_table = QTableWidget()
        self.matrix_table.setColumnCount(len(self.strategies)+1)
        self.matrix_table.setHorizontalHeaderLabels(["Hisse"] + [s[0] for s in self.strategies])
        self.matrix_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        matrix_layout.addWidget(self.matrix_table)
        # Strateji toggle butonları
        self.strategy_active = {s[0]: True for s in self.strategies}
        self.strategy_buttons = []
        btn_bar = QHBoxLayout()
        for idx, (name, _) in enumerate(self.strategies):
            btn = QPushButton(f"{name} Aktif")
            btn.setCheckable(True)
            btn.setChecked(True)
            btn.clicked.connect(lambda checked, i=idx, n=name: self.toggle_strategy(i, n, checked))
            self.strategy_buttons.append(btn)
            btn_bar.addWidget(btn)
        matrix_layout.addLayout(btn_bar)
        self.matrix_tab.setLayout(matrix_layout)
        # Tabları ekle
        self.tabs = QTabWidget()
        self.tabs.addTab(QWidget(), "Strateji Paneli")
        self.tabs.addTab(self.matrix_tab, "Strategy Matrix")
        vbox.addLayout(self.button_bar)
        vbox.addWidget(self.settings_stack)
        vbox.addWidget(self.tabs)
        self.setLayout(vbox)
        self.update_matrix()

    def toggle_strategy(self, idx, name, checked):
        self.strategy_active[name] = checked
        self.strategy_buttons[idx].setText(f"{name} {'Aktif' if checked else 'Deaktif'}")
        self.update_matrix()

    def update_matrix(self):
        stocks = self.get_selected_stocks()
        self.matrix_table.setRowCount(len(stocks))
        for row, symbol in enumerate(stocks):
            self.matrix_table.setItem(row, 0, QTableWidgetItem(symbol.upper()))
            for col, (strategy, _) in enumerate(self.strategies):
                cell = QTableWidgetItem()
                if self.strategy_active[strategy]:
                    sig = getattr(self.agent, 'strategy_signals', {}).get(symbol, "WAIT")
                    if sig == "ACTIVE" or sig == "BUY":
                        cell.setBackground(QColor("green"))
                        cell.setText(sig)
                    elif sig == "SELL":
                        cell.setBackground(QColor("red"))
                        cell.setText(sig)
                    else:
                        cell.setBackground(QColor("gray"))
                        cell.setText(sig)
                else:
                    cell.setText("–")
                self.matrix_table.setItem(row, col+1, cell)

    def on_params_changed(self):
        self.update_signals()

    def apply_for_all(self, strategy_name, idx):
        params = self.strategy_settings[idx].get_params()
        stocks = self.get_selected_stocks()
        self.agent.set_strategy(strategy_name, stocks, params)
        self.update_signals()

    def set_strategy_for_all(self, strategy_name):
        stocks = self.get_selected_stocks()
        self.agent.set_strategy(strategy_name, stocks)
        self.update_signals()

    def update_signals(self):
        if not hasattr(self.agent, 'active_strategy') or self.agent.active_strategy is None:
            for label in self.signal_labels:
                label.setText("No signals yet.")
            return
        strategy_names = [s[0] for s in self.strategies]
        if self.agent.active_strategy not in strategy_names:
            for label in self.signal_labels:
                label.setText("No signals yet.")
            return
        idx = strategy_names.index(self.agent.active_strategy)
        signals = getattr(self.agent, 'strategy_signals', {})
        if not signals:
            self.signal_labels[idx].setText("No signals yet.")
        else:
            text = "<b>Signals:</b><br>" + "<br>".join([f"{sym.upper()}: {sig}" for sym, sig in signals.items()])
            self.signal_labels[idx].setText(text)

class StockWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Binance Stock Tracker")
        self.setStyleSheet("""
            QWidget { background-color: #232629; color: #e0e0e0; }
            QLabel { color: #e0e0e0; }
            QCheckBox { color: #e0e0e0; }
            QListWidget { background-color: #232629; color: #e0e0e0; border: 1px solid #444; }
            QPushButton { background-color: #333; color: #e0e0e0; border-radius: 8px; }
            QTabWidget::pane { background: #232629; border: 1px solid #444; }
            QTabBar::tab { background: #333; color: #e0e0e0; border: 1px solid #444; border-radius: 8px; padding: 8px; }
            QTabBar::tab:selected { background: #444; color: #fff; }
            QTableWidget, QHeaderView::section { background-color: #232629; color: #e0e0e0; border: 1px solid #444; }
            QTableWidget QTableCornerButton::section { background: #232629; border: 1px solid #444; }
            QComboBox { background-color: #232629; color: #e0e0e0; border: 1px solid #444; border-radius: 6px; }
            QComboBox QAbstractItemView { background-color: #232629; color: #e0e0e0; }
            QLineEdit { background-color: #232629; color: #e0e0e0; border: 1px solid #444; border-radius: 6px; }
            QFormLayout > QLabel { color: #e0e0e0; }
            QDialog { background-color: #232629; color: #e0e0e0; }
        """)
        self.setMinimumSize(900, 500)

        self.selected_symbols = []
        self.tabs = QTabWidget()
        self.stocks_tab = QWidget()
        # Pass agent and selected stocks getter to strategies tab
        self.strategies_tab = StrategiesTab(agent=None, get_selected_stocks=lambda: self.selected_symbols)
        self.tabs.addTab(self.stocks_tab, "Stocks")
        self.tabs.addTab(self.strategies_tab, "Strategies")

        # Stocks tab layout
        splitter = QSplitter()
        self.selector = QListWidget()
        self.selector.setMaximumWidth(200)
        self.selector.setStyleSheet("font-size: 14px;")
        for symbol in STOCKS:
            item = QListWidgetItem(symbol.upper())
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.selector.addItem(item)
        self.selector.itemDoubleClicked.connect(self.show_stock_details)
        self.selector.itemChanged.connect(self.update_selected)
        self.grid_widget = QWidget()
        self.grid = QGridLayout()
        self.grid_widget.setLayout(self.grid)
        splitter.addWidget(self.selector)
        splitter.addWidget(self.grid_widget)
        stocks_layout = QVBoxLayout()
        stocks_layout.addWidget(splitter)
        self.stocks_tab.setLayout(stocks_layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

        self.circles = {}
        self.labels = {}
        self.status_labels = {}
        self.selected_symbols = []

    def show_stock_details(self, item):
        symbol = item.text().lower()
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{symbol.upper()} - Zaman Aralığı İncele")
        dialog.setMinimumSize(400, 400)
        vbox = QVBoxLayout()
        interval_box = QComboBox()
        interval_box.addItems(["15dk", "1 saat", "4 saat"])
        interval_map = {"15dk": "15m", "1 saat": "1h", "4 saat": "4h"}
        canvas = FigureCanvas(Figure(figsize=(5, 4)))
        vbox.addWidget(interval_box)
        vbox.addWidget(canvas)
        dialog.setLayout(vbox)

        def fetch_and_show():
            interval = interval_map[interval_box.currentText()]
            url = f"https://api.binance.com/api/v3/klines?symbol={symbol.upper()}&interval={interval}&limit=50"
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    klines = r.json()
                    df = pd.DataFrame(klines, columns=[
                        'OpenTime', 'Open', 'High', 'Low', 'Close', 'Volume', 'CloseTime', 'QuoteAssetVolume',
                        'NumberOfTrades', 'TakerBuyBaseAssetVolume', 'TakerBuyQuoteAssetVolume', 'Ignore'])
                    df['OpenTime'] = pd.to_datetime(df['OpenTime'], unit='ms')
                    df.set_index('OpenTime', inplace=True)
                    df[['Open', 'High', 'Low', 'Close', 'Volume']] = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
                    canvas.figure.clear()
                    ax = canvas.figure.add_subplot(211)
                    axv = canvas.figure.add_subplot(212, sharex=ax)
                    mpf.plot(df, type='candle', ax=ax, volume=axv, style='charles', ylabel='Fiyat')
                    canvas.draw()
                else:
                    canvas.figure.clear()
                    ax = canvas.figure.add_subplot(111)
                    ax.text(0.5, 0.5, "Veri alınamadı.", ha='center', va='center', fontsize=12)
                    canvas.draw()
            except Exception as e:
                canvas.figure.clear()
                ax = canvas.figure.add_subplot(111)
                ax.text(0.5, 0.5, f"Hata: {e}", ha='center', va='center', fontsize=12)
                canvas.draw()

        interval_box.currentIndexChanged.connect(fetch_and_show)
        # Pencere ilk açıldığında grafik boş olacak
        canvas.figure.clear()
        ax = canvas.figure.add_subplot(111)
        ax.text(0.5, 0.5, "Zaman aralığı seçin.", ha='center', va='center', fontsize=12)
        canvas.draw()
        dialog.exec_()

    def update_selected(self):
        self.selected_symbols = [self.selector.item(i).text().lower() for i in range(self.selector.count()) if self.selector.item(i).checkState() == Qt.Checked]
        # Clear grid
        for i in reversed(range(self.grid.count())):
            widget = self.grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.circles.clear()
        self.labels.clear()
        self.status_labels.clear()
        # Add selected stocks to grid
        # Update strategies tab with new selected stocks
        self.strategies_tab.update_signals()
        cols = 4
        for idx, symbol in enumerate(self.selected_symbols):
            row = idx // cols
            col = idx % cols
            vbox = QVBoxLayout()
            label = QLabel(f"{symbol.upper()}")
            label.setFont(QFont("Arial", 14))
            label.setAlignment(Qt.AlignCenter)
            circle = GlowCircle()
            circle.setAlignment(Qt.AlignCenter)
            price_label = QLabel("---")
            price_label.setFont(QFont("Arial", 10))
            price_label.setAlignment(Qt.AlignCenter)
            vbox.addWidget(label)
            vbox.addWidget(circle)
            vbox.addWidget(price_label)
            container = QWidget()
            container.setLayout(vbox)
            self.grid.addWidget(container, row, col)
            self.circles[symbol] = circle
            self.labels[symbol] = label
            self.status_labels[symbol] = price_label

    def update_stock(self, symbol, price, status):
        if symbol not in self.circles:
            return
        if status == "RISE":
            self.circles[symbol].setColor("green", glow=True)
        elif status == "FALL":
            self.circles[symbol].setColor("red", glow=True)
        else:
            self.circles[symbol].setColor("gray", glow=False)
        self.status_labels[symbol].setText(f"{price:.4f}")
        self.strategies_tab.update_signals()

class StockAgent:
    def __init__(self):
        self.strategy_signals = {}
        self.active_strategy = None
    def set_strategy(self, strategy_name, stocks, params=None):
        self.active_strategy = strategy_name
        # Dummy signals for demonstration
        for symbol in stocks:
            self.strategy_signals[symbol] = "WAIT"
    def start(self):
        pass
    def update_signal(self, *args, **kwargs):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    agent = StockAgent()
    widget = StockWidget()
    widget.strategies_tab.agent = agent
    widget.show()
    # agent.update_signal.connect(widget.update_stock)  # Uncomment and implement signal if needed
    agent.start()
    sys.exit(app.exec_())
