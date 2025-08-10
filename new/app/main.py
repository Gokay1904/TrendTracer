"""
Main entry point for the application.
"""
import sys
import logging
import asyncio
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication, QThread, QEventLoop
from app.ui.main_window import MainWindow
from app.ui.theme import get_application_stylesheet, get_dark_palette


# Fix for asyncio-qt integration on Windows
def windows_event_loop_fix():
    """Apply a fix for asyncio event loop on Windows."""
    if sys.platform == 'win32':
        # Required for asyncio and Qt integration on Windows
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Create a new event loop for the main thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            
class AsyncioEventLoopThread(QThread):
    """Thread for running the asyncio event loop."""
    
    def run(self):
        """Run the asyncio event loop in the thread."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
        
    def stop(self):
        """Stop the asyncio event loop."""
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.wait()


def main():
    """Main application entry point."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    # Set application information
    QCoreApplication.setApplicationName("CryptoPortfolioManager")
    QCoreApplication.setOrganizationName("CryptoPortfolioManager")
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use Fusion style for better dark theme support
    
    # Apply dark theme
    app.setStyleSheet(get_application_stylesheet())
    app.setPalette(get_dark_palette())
    
    # Fix for asyncio event loop on Windows
    windows_event_loop_fix()
    
    # Create a thread for the asyncio event loop
    asyncio_thread = AsyncioEventLoopThread()
    asyncio_thread.start()
    
    # Create main window
    window = MainWindow()
    window.show()
    
    # Run Qt event loop
    exit_code = app.exec_()
    
    # Clean up asyncio event loop thread
    asyncio_thread.stop()
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
