"""
Dark theme implementation for the application.
Provides stylesheets and color definitions for a consistent UI appearance.
"""
from PyQt5.QtGui import QColor, QPalette, QBrush
from PyQt5.QtCore import Qt


# Color palette for dark theme
class DarkThemeColors:
    """Color definitions for dark theme."""
    
    # Main colors
    BACKGROUND = "#1E1E2E"
    CARD_BACKGROUND = "#2A2A3C"
    PRIMARY = "#6272A4"
    SECONDARY = "#44475A"
    ACCENT = "#BD93F9"
    
    # Text colors
    TEXT_PRIMARY = "#F8F8F2"
    TEXT_SECONDARY = "#CCCCCC"
    TEXT_DISABLED = "#6272A4"
    
    # Status colors
    SUCCESS = "#50FA7B"
    WARNING = "#FFB86C"
    ERROR = "#FF5555"
    INFO = "#8BE9FD"
    
    # Trading specific colors
    PROFIT = "#50FA7B"  # Green
    LOSS = "#FF5555"    # Red
    NEUTRAL = "#F8F8F2" # White
    
    # Chart colors
    CHART_LINE = "#BD93F9"
    CHART_GRID = "#44475A"
    CHART_BACKGROUND = "#282A36"
    
    # Table colors
    TABLE_HEADER = "#44475A"
    TABLE_ALTERNATE_ROW = "#2D2D42"
    TABLE_SELECTED_ROW = "#6272A4"
    
    # Border colors
    BORDER = "#44475A"


def get_application_stylesheet():
    """Get the application-wide stylesheet."""
    return f"""
    /* Global Styles */
    QWidget {{
        background-color: {DarkThemeColors.BACKGROUND};
        color: {DarkThemeColors.TEXT_PRIMARY};
        font-family: "Segoe UI", Arial, sans-serif;
    }}
    
    /* Main Window */
    QMainWindow {{
        background-color: {DarkThemeColors.BACKGROUND};
    }}
    
    /* Menu Bar */
    QMenuBar {{
        background-color: {DarkThemeColors.CARD_BACKGROUND};
        color: {DarkThemeColors.TEXT_PRIMARY};
        border-bottom: 1px solid {DarkThemeColors.BORDER};
    }}
    
    QMenuBar::item {{
        background-color: transparent;
        padding: 6px 10px;
    }}
    
    QMenuBar::item:selected {{
        background-color: {DarkThemeColors.PRIMARY};
        color: {DarkThemeColors.TEXT_PRIMARY};
    }}
    
    QMenu {{
        background-color: {DarkThemeColors.CARD_BACKGROUND};
        border: 1px solid {DarkThemeColors.BORDER};
        padding: 5px;
    }}
    
    QMenu::item {{
        padding: 5px 25px 5px 20px;
        border-radius: 4px;
    }}
    
    QMenu::item:selected {{
        background-color: {DarkThemeColors.PRIMARY};
    }}
    
    /* Status Bar */
    QStatusBar {{
        background-color: {DarkThemeColors.CARD_BACKGROUND};
        color: {DarkThemeColors.TEXT_SECONDARY};
        border-top: 1px solid {DarkThemeColors.BORDER};
    }}
    
    /* Tab Widget */
    QTabWidget::pane {{
        border: 1px solid {DarkThemeColors.BORDER};
        background-color: {DarkThemeColors.BACKGROUND};
    }}
    
    QTabBar::tab {{
        background-color: {DarkThemeColors.SECONDARY};
        color: {DarkThemeColors.TEXT_SECONDARY};
        padding: 8px 16px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        margin-right: 2px;
    }}
    
    QTabBar::tab:selected {{
        background-color: {DarkThemeColors.ACCENT};
        color: {DarkThemeColors.TEXT_PRIMARY};
    }}
    
    /* Table Widget */
    QTableWidget {{
        background-color: {DarkThemeColors.CARD_BACKGROUND};
        alternate-background-color: {DarkThemeColors.TABLE_ALTERNATE_ROW};
        gridline-color: {DarkThemeColors.BORDER};
        border: 1px solid {DarkThemeColors.BORDER};
        border-radius: 4px;
    }}
    
    QTableWidget::item {{
        padding: 5px;
    }}
    
    QTableWidget::item:selected {{
        background-color: {DarkThemeColors.TABLE_SELECTED_ROW};
    }}
    
    QHeaderView::section {{
        background-color: {DarkThemeColors.TABLE_HEADER};
        color: {DarkThemeColors.TEXT_PRIMARY};
        padding: 5px;
        border: none;
        border-right: 1px solid {DarkThemeColors.BORDER};
        border-bottom: 1px solid {DarkThemeColors.BORDER};
    }}
    
    /* Buttons */
    QPushButton {{
        background-color: {DarkThemeColors.PRIMARY};
        color: {DarkThemeColors.TEXT_PRIMARY};
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: bold;
    }}
    
    QPushButton:hover {{
        background-color: {DarkThemeColors.ACCENT};
    }}
    
    QPushButton:pressed {{
        background-color: {DarkThemeColors.SECONDARY};
    }}
    
    QPushButton:disabled {{
        background-color: {DarkThemeColors.SECONDARY};
        color: {DarkThemeColors.TEXT_DISABLED};
    }}
    
    /* Input Fields */
    QLineEdit, QTextEdit, QComboBox {{
        background-color: {DarkThemeColors.SECONDARY};
        color: {DarkThemeColors.TEXT_PRIMARY};
        border: 1px solid {DarkThemeColors.BORDER};
        border-radius: 4px;
        padding: 6px;
    }}
    
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
        border: 1px solid {DarkThemeColors.ACCENT};
    }}
    
    /* Combo Box */
    QComboBox {{
        background-color: {DarkThemeColors.SECONDARY};
        selection-background-color: {DarkThemeColors.ACCENT};
        padding-right: 15px;
    }}
    
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 15px;
        border-left-width: 1px;
        border-left-color: {DarkThemeColors.BORDER};
        border-left-style: solid;
    }}
    
    QComboBox QAbstractItemView {{
        background-color: {DarkThemeColors.CARD_BACKGROUND};
        border: 1px solid {DarkThemeColors.BORDER};
        selection-background-color: {DarkThemeColors.ACCENT};
    }}
    
    /* Scroll Bars */
    QScrollBar:vertical {{
        border: none;
        background-color: {DarkThemeColors.SECONDARY};
        width: 10px;
        margin: 15px 0 15px 0;
        border-radius: 5px;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {DarkThemeColors.PRIMARY};
        min-height: 30px;
        border-radius: 5px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {DarkThemeColors.ACCENT};
    }}
    
    QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {{
        border: none;
        background: none;
        height: 15px;
    }}
    
    QScrollBar:horizontal {{
        border: none;
        background-color: {DarkThemeColors.SECONDARY};
        height: 10px;
        margin: 0 15px 0 15px;
        border-radius: 5px;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: {DarkThemeColors.PRIMARY};
        min-width: 30px;
        border-radius: 5px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background-color: {DarkThemeColors.ACCENT};
    }}
    
    QScrollBar::sub-line:horizontal, QScrollBar::add-line:horizontal {{
        border: none;
        background: none;
        width: 15px;
    }}
    
    /* Dialogs */
    QDialog {{
        background-color: {DarkThemeColors.BACKGROUND};
        border: 1px solid {DarkThemeColors.BORDER};
    }}
    
    /* Checkboxes */
    QCheckBox {{
        spacing: 5px;
    }}
    
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 3px;
        border: 1px solid {DarkThemeColors.BORDER};
    }}
    
    QCheckBox::indicator:unchecked {{
        background-color: {DarkThemeColors.SECONDARY};
    }}
    
    QCheckBox::indicator:checked {{
        background-color: {DarkThemeColors.ACCENT};
    }}
    
    /* Splitter */
    QSplitter::handle {{
        background-color: {DarkThemeColors.BORDER};
    }}
    
    QSplitter::handle:horizontal {{
        width: 2px;
    }}
    
    QSplitter::handle:vertical {{
        height: 2px;
    }}
    
    /* Labels */
    QLabel {{
        color: {DarkThemeColors.TEXT_PRIMARY};
    }}
    
    /* Group Box */
    QGroupBox {{
        border: 1px solid {DarkThemeColors.BORDER};
        border-radius: 5px;
        margin-top: 10px;
        font-weight: bold;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 10px;
        padding: 0 5px;
    }}
    """


def get_dark_palette():
    """Create and return a dark color palette for the application."""
    palette = QPalette()
    
    # Base colors
    palette.setColor(QPalette.Window, QColor(DarkThemeColors.BACKGROUND))
    palette.setColor(QPalette.WindowText, QColor(DarkThemeColors.TEXT_PRIMARY))
    palette.setColor(QPalette.Base, QColor(DarkThemeColors.CARD_BACKGROUND))
    palette.setColor(QPalette.AlternateBase, QColor(DarkThemeColors.TABLE_ALTERNATE_ROW))
    palette.setColor(QPalette.ToolTipBase, QColor(DarkThemeColors.CARD_BACKGROUND))
    palette.setColor(QPalette.ToolTipText, QColor(DarkThemeColors.TEXT_PRIMARY))
    
    # Text colors
    palette.setColor(QPalette.Text, QColor(DarkThemeColors.TEXT_PRIMARY))
    palette.setColor(QPalette.Button, QColor(DarkThemeColors.PRIMARY))
    palette.setColor(QPalette.ButtonText, QColor(DarkThemeColors.TEXT_PRIMARY))
    palette.setColor(QPalette.BrightText, QColor(DarkThemeColors.TEXT_PRIMARY))
    
    # Highlight colors
    palette.setColor(QPalette.Highlight, QColor(DarkThemeColors.ACCENT))
    palette.setColor(QPalette.HighlightedText, QColor(DarkThemeColors.TEXT_PRIMARY))
    
    # Disabled colors
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(DarkThemeColors.TEXT_DISABLED))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(DarkThemeColors.TEXT_DISABLED))
    palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(DarkThemeColors.SECONDARY))
    palette.setColor(QPalette.Disabled, QPalette.Base, QColor(DarkThemeColors.SECONDARY))
    palette.setColor(QPalette.Disabled, QPalette.Button, QColor(DarkThemeColors.SECONDARY))
    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(DarkThemeColors.TEXT_DISABLED))
    
    return palette


def apply_dark_theme_to_table(table_widget):
    """Apply dark theme styling to a QTableWidget."""
    # Set alternating row colors
    table_widget.setAlternatingRowColors(True)
    
    # Set selection color
    table_widget.setStyleSheet(f"""
        QTableWidget::item:selected {{
            background-color: {DarkThemeColors.TABLE_SELECTED_ROW};
            color: {DarkThemeColors.TEXT_PRIMARY};
        }}
    """)


def get_color_for_change(change_pct):
    """Get the appropriate color based on price change percentage."""
    if change_pct > 0:
        return QColor(DarkThemeColors.PROFIT)
    elif change_pct < 0:
        return QColor(DarkThemeColors.LOSS)
    else:
        return QColor(DarkThemeColors.NEUTRAL)
