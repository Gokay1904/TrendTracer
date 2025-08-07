import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QSpinBox, QGroupBox, QFormLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import mplfinance as mpf
import pandas as pd
import requests
class BinanceFuturesMock(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Binance Futures Order Simulator")
        self.setMinimumSize(400, 350)
        self.setStyleSheet(
            "QWidget { background-color: #232629; color: #e0e0e0; } "
            "QLabel { color: #e0e0e0; font-size: 14px; } "
            "QLineEdit, QComboBox, QSpinBox { background-color: #232629; color: #e0e0e0; border: 1px solid #444; border-radius: 6px; font-size: 14px; } "
            "QPushButton { background-color: #333; color: #e0e0e0; border-radius: 8px; font-size: 16px; padding: 8px; } "
            "QPushButton#buy { background-color: #1ecb81; color: #fff; } "
            "QPushButton#sell { background-color: #e74c3c; color: #fff; }"
        )
        main_layout = QVBoxLayout()
        form_group = QGroupBox("Futures Order Panel")
        form_layout = QFormLayout()
        self.symbol_box = QComboBox()
        self.symbol_box.addItems(["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"])
        form_layout.addRow(QLabel("Symbol:"), self.symbol_box)
        self.price_edit = QLineEdit()
        self.price_edit.setPlaceholderText("Order Price")
        form_layout.addRow(QLabel("Price:"), self.price_edit)
        self.qty_edit = QLineEdit()
        self.qty_edit.setPlaceholderText("Quantity")
        form_layout.addRow(QLabel("Quantity:"), self.qty_edit)
        self.leverage_spin = QSpinBox()
        self.leverage_spin.setRange(1, 125)
        self.leverage_spin.setValue(20)
        form_layout.addRow(QLabel("Leverage:"), self.leverage_spin)
        self.margin_mode_box = QComboBox()
        self.margin_mode_box.addItems(["Isolated", "Cross"])
        form_layout.addRow(QLabel("Margin Mode:"), self.margin_mode_box)
        self.order_type_box = QComboBox()
        self.order_type_box.addItems(["Limit", "Market", "Stop"])
        form_layout.addRow(QLabel("Order Type:"), self.order_type_box)
        self.stop_loss_edit = QLineEdit()
        self.stop_loss_edit.setPlaceholderText("Stop Loss Price")
        form_layout.addRow(QLabel("Stop Loss:"), self.stop_loss_edit)
        self.take_profit_edit = QLineEdit()
        self.take_profit_edit.setPlaceholderText("Take Profit Price")
        form_layout.addRow(QLabel("Take Profit:"), self.take_profit_edit)
        form_group.setLayout(form_layout)
        main_layout.addWidget(form_group)
        btn_layout = QHBoxLayout()
        self.buy_btn = QPushButton("Buy")
        self.buy_btn.setObjectName("buy")
        self.sell_btn = QPushButton("Sell")
        self.sell_btn.setObjectName("sell")
        btn_layout.addWidget(self.buy_btn)
        btn_layout.addWidget(self.sell_btn)
        main_layout.addLayout(btn_layout)
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignTop)
        self.status_label.setWordWrap(True)
        self.status_label.setFont(QFont("Arial", 10))
        main_layout.addWidget(self.status_label)
        self.pnl_preview_label = QLabel("")
        self.pnl_preview_label.setAlignment(Qt.AlignTop)
        self.pnl_preview_label.setWordWrap(True)
        self.pnl_preview_label.setFont(QFont("Arial", 9))
        main_layout.addWidget(self.pnl_preview_label)
        # --- Candlestick Chart Panel ---
        chart_group = QGroupBox("BTCUSDT Candlestick Chart")
        chart_layout = QVBoxLayout()
        self.interval_box = QComboBox()
        self.interval_box.addItems(["1m", "5m", "15m", "1h", "4h"])
        chart_layout.addWidget(QLabel("Interval:"))
        chart_layout.addWidget(self.interval_box)
        self.canvas = FigureCanvas(Figure(figsize=(5, 3)))
        chart_layout.addWidget(self.canvas)
        chart_group.setLayout(chart_layout)
        main_layout.addWidget(chart_group)
        self.setLayout(main_layout)
        self.buy_btn.clicked.connect(self.place_order)
        self.sell_btn.clicked.connect(self.place_order)
        # Live preview connections
        self.price_edit.textChanged.connect(self.update_pnl_preview)
        self.stop_loss_edit.textChanged.connect(self.update_pnl_preview)
        self.take_profit_edit.textChanged.connect(self.update_pnl_preview)
        self.leverage_spin.valueChanged.connect(self.update_pnl_preview)
        self.order_type_box.currentIndexChanged.connect(self.update_pnl_preview)
        self.buy_btn.clicked.connect(self.update_pnl_preview)
        self.sell_btn.clicked.connect(self.update_pnl_preview)
        # Chart interval connection
        self.interval_box.currentIndexChanged.connect(self.update_chart)
        self.update_chart()

        # Auto-refresh chart every second
        from PyQt5.QtCore import QTimer
        self.chart_timer = QTimer(self)
        self.chart_timer.timeout.connect(self.update_chart)
        self.chart_timer.start(1000)

    def update_chart(self):
        interval = self.interval_box.currentText()
        url = f"https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval={interval}&limit=30"
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
                # Only redraw if data changed
                if not hasattr(self, '_last_chart_close') or df['Close'].iloc[-1] != getattr(self, '_last_chart_close', None):
                    self._last_chart_close = df['Close'].iloc[-1]
                    ax = self.canvas.figure.gca()
                    ax.clear()
                    mpf.plot(df, type='candle', ax=ax, style='charles', ylabel='Price')
                    self.canvas.draw()
            else:
                ax = self.canvas.figure.gca()
                ax.clear()
                ax.text(0.5, 0.5, "Data fetch error.", ha='center', va='center', fontsize=12)
                self.canvas.draw()
        except Exception as e:
            ax = self.canvas.figure.gca()
            ax.clear()
            ax.text(0.5, 0.5, f"Error: {e}", ha='center', va='center', fontsize=12)
            self.canvas.draw()
    def update_chart(self):
        interval = self.interval_box.currentText()
        url = f"https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval={interval}&limit=50"
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
                self.canvas.figure.clear()
                ax = self.canvas.figure.add_subplot(111)
                mpf.plot(df, type='candle', ax=ax, style='charles', ylabel='Price')
                self.canvas.draw()
            else:
                self.canvas.figure.clear()
                ax = self.canvas.figure.add_subplot(111)
                ax.text(0.5, 0.5, "Data fetch error.", ha='center', va='center', fontsize=12)
                self.canvas.draw()
        except Exception as e:
            self.canvas.figure.clear()
            ax = self.canvas.figure.add_subplot(111)
            ax.text(0.5, 0.5, f"Error: {e}", ha='center', va='center', fontsize=12)
            self.canvas.draw()
    def update_pnl_preview(self):
        action = "Buy" if self.buy_btn.hasFocus() else "Sell"
        price = self.price_edit.text()
        stop_loss = self.stop_loss_edit.text()
        take_profit = self.take_profit_edit.text()
        leverage = self.leverage_spin.value()
        order_type = self.order_type_box.currentText()
        preview = []
        try:
            entry = float(price) if price else None
            sl = float(stop_loss) if stop_loss else None
            tp = float(take_profit) if take_profit else None
            if entry:
                if action == "Buy":
                    if sl:
                        pnl_sl = ((sl-entry)/entry)*100*leverage
                        preview.append(f"SL: {stop_loss} ({pnl_sl:.2f}% PNL)")
                    if tp:
                        pnl_tp = ((tp-entry)/entry)*100*leverage
                        preview.append(f"TP: {take_profit} ({pnl_tp:.2f}% PNL)")
                    if sl and tp:
                        rr = abs((tp-entry)/(entry-sl)) if (entry-sl)!=0 else 0
                        preview.append(f"Risk/Reward: {rr:.2f}")
                else:
                    if sl:
                        pnl_sl = ((entry-sl)/entry)*100*leverage
                        preview.append(f"SL: {stop_loss} ({pnl_sl:.2f}% PNL)")
                    if tp:
                        pnl_tp = ((entry-tp)/entry)*100*leverage
                        preview.append(f"TP: {take_profit} ({pnl_tp:.2f}% PNL)")
                    if sl and tp:
                        rr = abs((entry-tp)/(sl-entry)) if (sl-entry)!=0 else 0
                        preview.append(f"Risk/Reward: {rr:.2f}")
        except Exception:
            pass
        self.pnl_preview_label.setText(" | ".join(preview) if preview else "")

    def place_order(self):
        sender = self.sender()
        action = "Buy" if sender.objectName() == "buy" else "Sell"
        symbol = self.symbol_box.currentText()
        price = self.price_edit.text()
        qty = self.qty_edit.text()
        leverage = self.leverage_spin.value()
        margin_mode = self.margin_mode_box.currentText()
        order_type = self.order_type_box.currentText()
        stop_loss = self.stop_loss_edit.text()
        take_profit = self.take_profit_edit.text()
        if not price and order_type == "Limit":
            self.status_label.setText("Please enter a price for Limit order.")
            return
        if not qty:
            self.status_label.setText("Please enter quantity.")
            return
        if order_type == "Stop" and not stop_loss:
            self.status_label.setText("Please enter Stop Loss price for Stop order.")
            return
        details = [
            f"{action} {qty} {symbol}",
            f"@ {price if price else 'Market'}",
            f"x{leverage}",
            f"[{order_type}]",
            f"Margin: {margin_mode}"
        ]
        pnl_text = ""
        try:
            entry = float(price) if price else None
            sl = float(stop_loss) if stop_loss else None
            tp = float(take_profit) if take_profit else None
            if entry:
                if action == "Buy":
                    if sl:
                        pnl_sl = ((sl-entry)/entry)*100*leverage
                        details.append(f"SL: {stop_loss} ({pnl_sl:.2f}% PNL)")
                    if tp:
                        pnl_tp = ((tp-entry)/entry)*100*leverage
                        details.append(f"TP: {take_profit} ({pnl_tp:.2f}% PNL)")
                    if sl and tp:
                        rr = abs((tp-entry)/(entry-sl)) if (entry-sl)!=0 else 0
                        details.append(f"Risk/Reward: {rr:.2f}")
                else: # Sell
                    if sl:
                        pnl_sl = ((entry-sl)/entry)*100*leverage
                        details.append(f"SL: {stop_loss} ({pnl_sl:.2f}% PNL)")
                    if tp:
                        pnl_tp = ((entry-tp)/entry)*100*leverage
                        details.append(f"TP: {take_profit} ({pnl_tp:.2f}% PNL)")
                    if sl and tp:
                        rr = abs((entry-tp)/(sl-entry)) if (sl-entry)!=0 else 0
                        details.append(f"Risk/Reward: {rr:.2f}")
        except Exception:
            if stop_loss:
                details.append(f"SL: {stop_loss}")
            if take_profit:
                details.append(f"TP: {take_profit}")
        self.status_label.setText("  ｣  ".join(details) + " (Simulated)")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = BinanceFuturesMock()
    win.show()
    sys.exit(app.exec_())
