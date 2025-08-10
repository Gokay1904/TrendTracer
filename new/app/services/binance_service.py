"""
Binance API service for fetching market data and managing account operations.
"""
import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Callable, Any

import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException

# Define a simple mock for the missing AsyncClient and BinanceSocketManager
# This will allow the code to run but websocket functionality will be disabled
class AsyncClient:
    @classmethod
    async def create(cls, api_key=None, api_secret=None):
        return cls()
        
    async def close_connection(self):
        pass
        
class BinanceSocketManager:
    def __init__(self, client):
        self.client = client
        
    def multiplex_socket(self, streams):
        return MockSocketManager()
        
    def kline_socket(self, symbol, interval):
        return MockSocketManager()
        
    def user_socket(self):
        return MockSocketManager()
        
class MockSocketManager:
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
        
    async def recv(self):
        # Return empty data
        await asyncio.sleep(1)
        return {}

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from app.models.asset import Asset, AssetPrice, AssetType
from app.config.settings import Settings


class BinanceService(QObject):
    """Service for interacting with the Binance API."""
    
    # Define signals for real-time updates
    price_updated = pyqtSignal(AssetPrice)
    klines_updated = pyqtSignal(str, object)  # symbol, dataframe
    account_updated = pyqtSignal(dict)
    connection_status_changed = pyqtSignal(bool, str)  # connected, message
    error_occurred = pyqtSignal(str)
    
    # Timeframe constants
    TIMEFRAMES = {
        '1m': '1m',
        '5m': '5m',
        '15m': '15m',
        '30m': '30m',
        '1h': '1h',
        '4h': '4h',
        '1d': '1d',
        '1w': '1w',
    }
    
    def __init__(self, settings: Settings):
        """Initialize the Binance service.
        
        Args:
            settings: Application settings containing API credentials
        """
        super().__init__()
        self.settings = settings
        self.client: Optional[Client] = None
        self.async_client: Optional[AsyncClient] = None
        self.bsm: Optional[BinanceSocketManager] = None
        self.active_streams: Dict[str, Tuple[Any, asyncio.Task]] = {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize client if API keys are available
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize the Binance client with API keys."""
        api_key = self.settings.get('api_key', '')
        api_secret = self.settings.get('api_secret', '')
        
        try:
            if api_key and api_secret:
                self.client = Client(api_key, api_secret)
                self.connection_status_changed.emit(True, "Connected to Binance API")
            else:
                # Initialize in test mode for market data only
                self.client = Client()
                self.connection_status_changed.emit(
                    True, 
                    "Connected to Binance API in public data mode (no API keys)"
                )
        except BinanceAPIException as e:
            self.logger.error(f"Binance API error: {e}")
            self.connection_status_changed.emit(False, f"Connection error: {str(e)}")
            self.error_occurred.emit(f"Binance API error: {str(e)}")
            
    async def _initialize_async_client(self):
        """Initialize the async Binance client for websocket connections."""
        if self.async_client is not None:
            return
            
        api_key = self.settings.get('api_key', '')
        api_secret = self.settings.get('api_secret', '')
        
        try:
            self.async_client = await AsyncClient.create(api_key, api_secret)
            self.bsm = BinanceSocketManager(self.async_client)
        except BinanceAPIException as e:
            self.logger.error(f"Async Binance API error: {e}")
            self.error_occurred.emit(f"Binance API error: {str(e)}")
            raise
    
    def update_credentials(self, api_key: str, api_secret: str):
        """Update the API credentials and reinitialize the client.
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
        """
        self.settings.set('api_key', api_key)
        self.settings.set('api_secret', api_secret)
        
        # Close existing connections if any
        self.close_connections()
        
        # Reinitialize with new credentials
        self._initialize_client()
        
    def close_connections(self):
        """Close all active connections and websockets."""
        # Close all active websocket streams
        for stream_key, (conn, task) in self.active_streams.items():
            if task and not task.done():
                task.cancel()
        
        self.active_streams.clear()
        
        # Close async client if it exists
        if self.async_client:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.async_client.close_connection())
            else:
                loop.run_until_complete(self.async_client.close_connection())
            self.async_client = None
            self.bsm = None
            
    def get_exchange_info(self) -> dict:
        """Get exchange information from Binance.
        
        Returns:
            dict: Exchange information including symbols, filters, etc.
        """
        if not self.client:
            self.error_occurred.emit("Binance client not initialized")
            return {}
            
        try:
            return self.client.get_exchange_info()
        except BinanceAPIException as e:
            self.logger.error(f"Error getting exchange info: {e}")
            self.error_occurred.emit(f"Binance API error: {str(e)}")
            return {}
            
    def get_all_tickers(self) -> List[dict]:
        """Get current price ticker for all symbols.
        
        Returns:
            List[dict]: List of ticker dictionaries with symbol and price
        """
        if not self.client:
            self.error_occurred.emit("Binance client not initialized")
            return []
            
        try:
            return self.client.get_all_tickers()
        except BinanceAPIException as e:
            self.logger.error(f"Error getting tickers: {e}")
            self.error_occurred.emit(f"Binance API error: {str(e)}")
            return []
            
    def get_24h_stats(self, symbol: Optional[str] = None) -> List[dict]:
        """Get 24-hour price statistics for symbols.
        
        Args:
            symbol: Optional specific symbol to get stats for
            
        Returns:
            List[dict]: Statistics including price change, volume, etc.
        """
        if not self.client:
            self.error_occurred.emit("Binance client not initialized")
            return []
            
        try:
            if symbol:
                return [self.client.get_ticker(symbol=symbol)]
            else:
                return self.client.get_ticker()
        except BinanceAPIException as e:
            self.logger.error(f"Error getting 24h stats: {e}")
            self.error_occurred.emit(f"Binance API error: {str(e)}")
            return []
            
    def get_futures_positions(self) -> List[dict]:
        """Get current futures positions from the account.
        
        Returns:
            List[dict]: List of open futures positions with position information
        """
        if not self.client:
            self.error_occurred.emit("Binance client not initialized")
            return []
            
        # Check if API key is available - needed for account data
        if not self.settings.get('api_key') or not self.settings.get('api_secret'):
            self.error_occurred.emit("API key required for futures positions")
            return []
            
        try:
            # Get futures account information
            account_info = self.client.futures_account()
            
            # Extract positions with non-zero amounts
            positions = []
            for position in account_info.get('positions', []):
                # Convert position amount to float and check if it's not zero
                position_amt = float(position.get('positionAmt', 0))
                if abs(position_amt) > 0:
                    # Add current market price
                    symbol = position['symbol']
                    try:
                        ticker = self.client.futures_symbol_ticker(symbol=symbol)
                        position['markPrice'] = ticker['price']
                    except:
                        position['markPrice'] = '0'
                        
                    positions.append(position)
                    
            return positions
        except BinanceAPIException as e:
            self.logger.error(f"Error getting futures positions: {e}")
            self.error_occurred.emit(f"Binance API error: {str(e)}")
            return []
            
    def get_klines(self, 
                  symbol: str, 
                  interval: str, 
                  limit: int = 100) -> Optional[pd.DataFrame]:
        """Get historical klines (candlestick data) for a symbol.
        
        Args:
            symbol: The trading symbol (e.g., 'BTCUSDT')
            interval: Time interval ('1m', '5m', '1h', etc.)
            limit: Number of candles to retrieve
            
        Returns:
            Optional[pd.DataFrame]: DataFrame with OHLCV data or None on error
        """
        if not self.client:
            self.error_occurred.emit("Binance client not initialized")
            return None
            
        if interval not in self.TIMEFRAMES:
            self.error_occurred.emit(f"Invalid interval: {interval}")
            return None
            
        try:
            klines = self.client.get_klines(
                symbol=symbol,
                interval=self.TIMEFRAMES[interval],
                limit=limit
            )
            
            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Convert types
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
                
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
        except BinanceAPIException as e:
            self.logger.error(f"Error getting klines for {symbol}: {e}")
            self.error_occurred.emit(f"Binance API error: {str(e)}")
            return None
            
    def get_account_info(self) -> Optional[dict]:
        """Get account information including balances.
        
        Returns:
            Optional[dict]: Account information or None if not authenticated
        """
        if not self.client:
            self.error_occurred.emit("Binance client not initialized")
            return None
            
        api_key = self.settings.get('api_key', '')
        api_secret = self.settings.get('api_secret', '')
        
        if not api_key or not api_secret:
            self.error_occurred.emit("API credentials required for account info")
            return None
            
        try:
            return self.client.get_account()
        except BinanceAPIException as e:
            self.logger.error(f"Error getting account info: {e}")
            self.error_occurred.emit(f"Binance API error: {str(e)}")
            return None
            
    def create_asset_from_balance(self, balance: dict) -> Optional[Asset]:
        """Create an Asset object from a balance dictionary.
        
        Args:
            balance: Balance dictionary from Binance API
            
        Returns:
            Optional[Asset]: Asset object or None if balance is zero
        """
        asset_name = balance['asset']
        free_balance = float(balance['free'])
        locked_balance = float(balance['locked'])
        total_balance = free_balance + locked_balance
        
        # Skip zero balances
        if total_balance <= 0:
            return None
            
        # Find a USDT pair if possible for price info
        symbol = f"{asset_name}USDT"
        
        # Create the asset
        asset = Asset(symbol, AssetType.SPOT)
        asset.update_balance(total_balance)
        
        # Try to get current price
        try:
            if self.client:
                ticker = self.client.get_symbol_ticker(symbol=symbol)
                price = float(ticker['price'])
                
                price_data = AssetPrice(
                    symbol=symbol,
                    price=price,
                    timestamp=datetime.now()
                )
                asset.update_price(price_data)
        except BinanceAPIException:
            # This is expected for assets without USDT pairs
            pass
            
        return asset
        
    @pyqtSlot()
    def start_ticker_stream(self, symbols: Optional[List[str]] = None):
        """Start a websocket stream for real-time price updates.
        
        Args:
            symbols: Optional list of symbols to stream (all if None)
        """
        async def _start_ticker_stream(self, symbols=None):
            await self._initialize_async_client()
            
            # Use the mini ticker for all symbols or a subset
            if symbols:
                socket_manager = self.bsm.multiplex_socket([
                    f"{symbol.lower()}@miniTicker" for symbol in symbols
                ])
            else:
                socket_manager = self.bsm.multiplex_socket(['!miniTicker@arr'])
                
            async with socket_manager as stream:
                while True:
                    msg = await stream.recv()
                    self._handle_ticker_message(msg)
                    
        async def _handle_ticker_message(self, msg):
            try:
                # Process the ticker data
                if 'data' in msg:
                    data = msg['data']
                    symbol = data['s']  # Symbol
                    price = float(data['c'])  # Close price
                    
                    # Create price object
                    price_data = AssetPrice(
                        symbol=symbol,
                        price=price,
                        timestamp=datetime.now(),
                        volume_24h=float(data['v'])  # 24h volume
                    )
                    
                    # Emit signal
                    self.price_updated.emit(price_data)
            except Exception as e:
                self.logger.error(f"Error processing ticker message: {e}")
                
        # Run in an asyncio task
        loop = asyncio.get_event_loop()
        task = loop.create_task(_start_ticker_stream(self, symbols))
        self.active_streams['ticker'] = (None, task)
        
    @pyqtSlot(str, str)
    def start_kline_stream(self, symbol: str, interval: str):
        """Start a websocket stream for real-time kline updates.
        
        Args:
            symbol: The trading symbol (e.g., 'BTCUSDT')
            interval: Time interval ('1m', '5m', '1h', etc.)
        """
        async def _start_kline_stream(self, symbol, interval):
            await self._initialize_async_client()
            
            if interval not in self.TIMEFRAMES:
                self.error_occurred.emit(f"Invalid interval: {interval}")
                return
                
            socket_manager = self.bsm.kline_socket(
                symbol=symbol,
                interval=self.TIMEFRAMES[interval]
            )
            
            # Store historical data
            historical_df = self.get_klines(symbol, interval)
            
            async with socket_manager as stream:
                while True:
                    msg = await stream.recv()
                    await self._handle_kline_message(msg, historical_df, symbol, interval)
                    
        async def _handle_kline_message(self, msg, historical_df, symbol, interval):
            try:
                if 'k' in msg:
                    k = msg['k']
                    
                    # Only process if the candle is closed or it's the last update
                    is_closed = k['x']
                    
                    # Convert kline to a DataFrame row
                    new_row = pd.DataFrame([{
                        'timestamp': pd.to_datetime(k['t'], unit='ms'),
                        'open': float(k['o']),
                        'high': float(k['h']),
                        'low': float(k['l']),
                        'close': float(k['c']),
                        'volume': float(k['v'])
                    }])
                    new_row.set_index('timestamp', inplace=True)
                    
                    # Update historical data
                    if is_closed:
                        # Remove old candle if exists
                        historical_df = historical_df[historical_df.index != new_row.index[0]]
                        # Append new candle
                        historical_df = pd.concat([historical_df, new_row])
                    else:
                        # Update the current candle (last row)
                        if historical_df.index[-1] == new_row.index[0]:
                            historical_df.iloc[-1] = new_row.iloc[0]
                        else:
                            # Append as a new row
                            historical_df = pd.concat([historical_df, new_row])
                    
                    # Emit signal with updated data
                    self.klines_updated.emit(symbol, historical_df)
            except Exception as e:
                self.logger.error(f"Error processing kline message: {e}")
                
        # Generate a unique key for this stream
        stream_key = f"{symbol}_{interval}_kline"
        
        # Cancel existing stream if any
        if stream_key in self.active_streams:
            _, task = self.active_streams[stream_key]
            if task and not task.done():
                task.cancel()
                
        # Run in an asyncio task
        loop = asyncio.get_event_loop()
        task = loop.create_task(_start_kline_stream(self, symbol, interval))
        self.active_streams[stream_key] = (None, task)
        
    @pyqtSlot()
    def start_user_data_stream(self):
        """Start a user data stream for account updates."""
        async def _start_user_data_stream(self):
            await self._initialize_async_client()
            
            api_key = self.settings.get('api_key', '')
            api_secret = self.settings.get('api_secret', '')
            
            if not api_key or not api_secret:
                self.error_occurred.emit("API credentials required for user data stream")
                return
                
            socket_manager = self.bsm.user_socket()
            
            async with socket_manager as stream:
                while True:
                    msg = await stream.recv()
                    await self._handle_user_data_message(msg)
                    
        async def _handle_user_data_message(self, msg):
            try:
                if 'e' in msg:
                    event_type = msg['e']
                    
                    if event_type == 'outboundAccountPosition':
                        # Account balance update
                        self.account_updated.emit(msg)
                    elif event_type == 'executionReport':
                        # Order update
                        self.order_updated.emit(msg)
            except Exception as e:
                self.logger.error(f"Error processing user data message: {e}")
                
        # Cancel existing stream if any
        if 'user_data' in self.active_streams:
            _, task = self.active_streams['user_data']
            if task and not task.done():
                task.cancel()
                
        # Run in an asyncio task
        loop = asyncio.get_event_loop()
        task = loop.create_task(_start_user_data_stream(self))
        self.active_streams['user_data'] = (None, task)
        
    def get_top_movers(self, base_asset: str = 'USDT', 
                       lookback_hours: int = 24, 
                       limit: int = 10) -> List[Dict[str, Any]]:
        """Get top price movers within a time period.
        
        Args:
            base_asset: Base asset for pairs (e.g., 'USDT', 'BTC')
            lookback_hours: Hours to look back (4 or 24)
            limit: Number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of symbols and their price changes
        """
        if not self.client:
            self.error_occurred.emit("Binance client not initialized")
            return []
            
        try:
            # Get 24h ticker for all symbols
            tickers = self.client.get_ticker()
            
            # Filter for base asset
            filtered_tickers = [
                t for t in tickers 
                if t['symbol'].endswith(base_asset)
            ]
            
            # Sort by price change percentage
            if lookback_hours <= 4:
                # Use 24h data as an approximation for now
                # In a real app, you could calculate 4h changes from klines
                sorted_tickers = sorted(
                    filtered_tickers,
                    key=lambda x: float(x['priceChangePercent']),
                    reverse=True
                )
            else:
                # 24h data
                sorted_tickers = sorted(
                    filtered_tickers,
                    key=lambda x: float(x['priceChangePercent']),
                    reverse=True
                )
                
            # Return top movers
            return sorted_tickers[:limit]
        except BinanceAPIException as e:
            self.logger.error(f"Error getting top movers: {e}")
            self.error_occurred.emit(f"Binance API error: {str(e)}")
            return []
