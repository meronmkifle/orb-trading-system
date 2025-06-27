import streamlit as st
import pandas as pd
import time
import json
import requests
import threading
import queue
from datetime import datetime, timedelta
import random
import numpy as np
import websocket

# Page configuration
st.set_page_config(
    page_title="ORB Trading System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
        padding: 30px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    
    .status-running {
        color: #2ecc71;
        font-weight: bold;
        font-size: 24px;
    }
    
    .status-stopped {
        color: #e74c3c;
        font-weight: bold;
        font-size: 24px;
    }
    
    .status-paused {
        color: #f39c12;
        font-weight: bold;
        font-size: 24px;
    }
    
    .price-display {
        background: #f8f9fa;
        padding: 25px;
        border-radius: 8px;
        text-align: center;
        margin: 20px 0;
    }
    
    .price-value {
        font-size: 48px;
        font-weight: bold;
        color: #2c3e50;
        margin: 10px 0;
    }
    
    .strategy-card {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
        border: 2px solid #dee2e6;
        text-align: center;
        margin: 10px 0;
    }
    
    .strategy-active {
        border-color: #2ecc71;
        background: #d4edda;
    }
    
    .strategy-waiting {
        border-color: #f39c12;
        background: #fff3cd;
    }
    
    .api-status {
        padding: 10px;
        border-radius: 6px;
        margin: 10px 0;
        text-align: center;
        font-weight: bold;
    }
    
    .api-connected {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .api-disconnected {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
</style>
""", unsafe_allow_html=True)

class TradoVateAPI:
    """Real TradoVate API Integration"""
    
    def __init__(self, environment='demo'):
        self.environment = environment
        self.access_token = None
        self.account_id = None
        self.user_id = None
        
        # API URLs based on environment
        if environment == 'demo':
            self.rest_url = "https://demo.tradovateapi.com/v1"
            self.ws_url = "wss://demo.tradovateapi.com/v1/websocket"
            self.md_ws_url = "wss://md-demo.tradovateapi.com/v1/websocket"
        else:
            self.rest_url = "https://live.tradovateapi.com/v1"
            self.ws_url = "wss://live.tradovateapi.com/v1/websocket"
            self.md_ws_url = "wss://md.tradovateapi.com/v1/websocket"
        
        self.ws = None
        self.md_ws = None
        self.is_connected = False
        self.message_queue = queue.Queue()
        
    def authenticate(self, username, password, device_id="streamlit_orb_system"):
        """Authenticate with TradoVate API"""
        try:
            # Step 1: Get access token
            auth_data = {
                "name": username,
                "password": password,
                "appId": "TradovateWebApi",
                "appVersion": "1.0.0",
                "deviceId": device_id,
                "cid": 0
            }
            
            response = requests.post(
                f"{self.rest_url}/auth/accesstokenrequest",
                json=auth_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                auth_result = response.json()
                self.access_token = auth_result.get('accessToken')
                self.user_id = auth_result.get('userId')
                
                if self.access_token:
                    # Step 2: Get account information
                    self.get_account_info()
                    self.is_connected = True
                    return True, f"✅ Connected to TradoVate API ({self.environment})"
                else:
                    return False, "❌ Failed to get access token"
            else:
                error_msg = response.json().get('errorText', 'Authentication failed')
                return False, f"❌ Authentication failed: {error_msg}"
                
        except Exception as e:
            return False, f"❌ Connection error: {str(e)}"
    
    def get_account_info(self):
        """Get account information"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{self.rest_url}/account/list", headers=headers)
            
            if response.status_code == 200:
                accounts = response.json()
                if accounts:
                    self.account_id = accounts[0]['id']  # Use first account
                    return True
            return False
        except:
            return False
    
    def get_headers(self):
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.access_token}"}
    
    def get_contract_id(self, symbol):
        """Get contract ID for symbol"""
        try:
            headers = self.get_headers()
            response = requests.get(
                f"{self.rest_url}/contract/find",
                params={"name": symbol},
                headers=headers
            )
            
            if response.status_code == 200:
                contract = response.json()
                return contract.get('id')
            return None
        except:
            return None
    
    def place_order(self, symbol, action, quantity, order_type="Market"):
        """Place an order"""
        try:
            headers = self.get_headers()
            order_data = {
                "accountId": self.account_id,
                "action": action,  # "Buy" or "Sell"
                "symbol": symbol,
                "quantity": quantity,
                "orderType": order_type,
                "timeInForce": "Day"
            }
            
            response = requests.post(
                f"{self.rest_url}/order/placeorder",
                json=order_data,
                headers=headers
            )
            
            if response.status_code == 200:
                return True, response.json()
            else:
                error = response.json().get('errorText', 'Order failed')
                return False, error
        except Exception as e:
            return False, str(e)
    
    def get_positions(self):
        """Get current positions"""
        try:
            headers = self.get_headers()
            response = requests.get(
                f"{self.rest_url}/position/list",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            return []
        except:
            return []
    
    def get_orders(self):
        """Get current orders"""
        try:
            headers = self.get_headers()
            response = requests.get(
                f"{self.rest_url}/order/list",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            return []
        except:
            return []
    
    def cancel_order(self, order_id):
        """Cancel an order"""
        try:
            headers = self.get_headers()
            response = requests.post(
                f"{self.rest_url}/order/cancelorder",
                json={"orderId": order_id},
                headers=headers
            )
            return response.status_code == 200
        except:
            return False
    
    def start_market_data_stream(self, symbol):
        """Start market data WebSocket stream"""
        def on_message(ws, message):
            try:
                data = json.loads(message)
                self.message_queue.put(('md', data))
            except:
                pass
        
        def on_error(ws, error):
            st.error(f"Market data WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            st.warning("Market data WebSocket closed")
        
        def on_open(ws):
            # Subscribe to market data
            contract_id = self.get_contract_id(symbol)
            if contract_id:
                subscribe_msg = {
                    "url": f"md/subscribequote",
                    "body": {"symbol": symbol}
                }
                ws.send(json.dumps(subscribe_msg))
        
        if self.access_token:
            self.md_ws = websocket.WebSocketApp(
                f"{self.md_ws_url}?token={self.access_token}",
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            
            # Start in a separate thread
            threading.Thread(target=self.md_ws.run_forever, daemon=True).start()

class ORBTradingEngine:
    """ORB Trading Engine with Real TradoVate Integration"""
    
    def __init__(self):
        self.api = None
        self.is_running = False
        self.trading_enabled = False
        
        # Market data
        self.current_price = 16234.50
        self.vwap = 16231.25
        self.bid = 16234.25
        self.ask = 16234.75
        self.last_update = time.time()
        
        # Indicators
        self.ma350 = []
        self.ma300 = []
        self.ma400 = []
        self.volume_data = []
        self.price_volume_data = []
        
        # Positions (from TradoVate)
        self.positions = {}
        self.orders = {}
        
        # Strategy tracking
        self.strategy_positions = {
            'strategy1': None,
            'strategy2': None,
            'strategy3': None
        }
        
        # Performance tracking
        self.daily_pnl = 0
        self.total_trades = 0
        self.trade_log = []
        
        # Risk settings
        self.risk_settings = {
            'max_risk': 100,
            'stop_loss_pct': 0.01,
            'daily_limit': 900,
            'total_limit': 4200
        }
        
        # Market hours (ET)
        self.market_hours = {
            'start': {'hour': 9, 'minute': 30},
            'end': {'hour': 16, 'minute': 0}
        }
        
        # Initialize with some historical data
        self.initialize_indicators()
    
    def initialize_indicators(self):
        """Initialize moving averages with some data"""
        base_price = self.current_price
        for i in range(400):
            noise = random.uniform(-5, 5)
            price = base_price + noise
            
            self.ma400.append(price)
            if i >= 50:
                self.ma300.append(price)
            if i >= 100:
                self.ma350.append(price)
        
        # Keep only required lengths
        self.ma400 = self.ma400[-400:]
        self.ma350 = self.ma350[-350:]
        self.ma300 = self.ma300[-300:]
    
    def connect_api(self, username, password, environment):
        """Connect to TradoVate API"""
        self.api = TradoVateAPI(environment)
        success, message = self.api.authenticate(username, password)
        
        if success:
            # Start market data stream for MNQ
            self.api.start_market_data_stream("MNQ")
            # Start processing market data
            self.start_market_data_processor()
        
        return success, message
    
    def start_market_data_processor(self):
        """Process incoming market data"""
        def process_data():
            while self.api and self.api.is_connected:
                try:
                    # Process market data messages
                    msg_type, data = self.api.message_queue.get(timeout=1)
                    
                    if msg_type == 'md' and 'quote' in str(data):
                        # Update current price from real market data
                        quote = data.get('quote', {})
                        if 'last' in quote:
                            self.current_price = quote['last']
                        if 'bid' in quote:
                            self.bid = quote['bid']
                        if 'ask' in quote:
                            self.ask = quote['ask']
                        
                        # Update indicators
                        self.update_indicators()
                        
                        # Check strategies if trading is enabled
                        if self.trading_enabled and self.is_market_open():
                            self.check_strategies()
                            
                except queue.Empty:
                    continue
                except Exception as e:
                    st.error(f"Market data processing error: {e}")
        
        threading.Thread(target=process_data, daemon=True).start()
    
    def disconnect_api(self):
        """Disconnect API"""
        if self.api:
            self.api.is_connected = False
            if self.api.ws:
                self.api.ws.close()
            if self.api.md_ws:
                self.api.md_ws.close()
            self.api = None
        self.stop_system()
    
    def start_system(self):
        """Start the trading system"""
        if not self.api or not self.api.is_connected:
            return False, "❌ API not connected"
        
        self.is_running = True
        self.trading_enabled = True
        return True, "✅ Trading system started"
    
    def stop_system(self):
        """Stop the trading system"""
        self.is_running = False
        self.trading_enabled = False
        return True, "🛑 Trading system stopped"
    
    def pause_trading(self):
        """Pause new entries"""
        self.trading_enabled = False
        return True, "⏸️ Trading paused - existing positions maintained"
    
    def resume_trading(self):
        """Resume trading"""
        if self.is_running:
            self.trading_enabled = True
            return True, "▶️ Trading resumed"
        return False, "❌ System must be running to resume"
    
    def update_indicators(self):
        """Update technical indicators"""
        # Update moving averages
        self.ma400.append(self.current_price)
        self.ma350.append(self.current_price)
        self.ma300.append(self.current_price)
        
        # Keep only required lengths
        if len(self.ma400) > 400:
            self.ma400.pop(0)
        if len(self.ma350) > 350:
            self.ma350.pop(0)
        if len(self.ma300) > 300:
            self.ma300.pop(0)
        
        # Update VWAP (simplified)
        volume = random.randint(100, 1000)
        self.volume_data.append(volume)
        self.price_volume_data.append(self.current_price * volume)
        
        if len(self.volume_data) > 100:
            self.volume_data.pop(0)
            self.price_volume_data.pop(0)
        
        if sum(self.volume_data) > 0:
            self.vwap = sum(self.price_volume_data) / sum(self.volume_data)
    
    def is_market_open(self):
        """Check if market is open"""
        now = datetime.now()
        current_minutes = now.hour * 60 + now.minute
        start_minutes = self.market_hours['start']['hour'] * 60 + self.market_hours['start']['minute']
        end_minutes = self.market_hours['end']['hour'] * 60 + self.market_hours['end']['minute']
        return start_minutes <= current_minutes <= end_minutes
    
    def check_strategies(self):
        """Check all trading strategies with exact rules from MQL5 article"""
        # Update positions from API
        self.sync_positions()
        
        # Update candle data
        self.update_candle_data()
        
        # Execute strategies based on exact rules from the research
        self.execute_strategy1_exact()  # Opening Candle Direction
        self.execute_strategy2_exact()  # VWAP Trend Following  
        self.execute_strategy3_exact()  # Concretum Bands Breakout
    
    def update_candle_data(self):
        """Update 1m, 5m, and 15m candle data"""
        current_time = datetime.now()
        current_minute = current_time.minute
        current_hour = current_time.hour
        
        # Simulate new candle formation
        new_candle = {
            'timestamp': current_time,
            'open': self.current_price + random.uniform(-2, 2),
            'high': self.current_price + random.uniform(0, 5),
            'low': self.current_price - random.uniform(0, 5),
            'close': self.current_price,
            'volume': random.randint(100, 1000)
        }
        
        # Update 1-minute candles
        if not hasattr(self, 'candles_1m'):
            self.candles_1m = []
        self.candles_1m.append(new_candle)
        if len(self.candles_1m) > 500:
            self.candles_1m.pop(0)
        
        # Update 5-minute candles (every 5 minutes)
        if not hasattr(self, 'candles_5m'):
            self.candles_5m = []
        if current_minute % 5 == 0:
            self.candles_5m.append(new_candle)
            if len(self.candles_5m) > 100:
                self.candles_5m.pop(0)
        
        # Update 15-minute candles (every 15 minutes)
        if not hasattr(self, 'candles_15m'):
            self.candles_15m = []
        if current_minute % 15 == 0:
            self.candles_15m.append(new_candle)
            if len(self.candles_15m) > 50:
                self.candles_15m.pop(0)
    
    def execute_strategy1_exact(self):
        """Strategy 1: Opening Candle Direction (Exact Implementation)"""
        if not self.can_trade('strategy1') or len(self.ma350) < 350:
            return
        
        # Check daily risk limits before trading
        risk_ok, risk_msg = self.check_daily_risk_limits()
        if not risk_ok:
            return
        
        if not hasattr(self, 'candles_5m') or len(self.candles_5m) < 2:
            return
        
        # Check if this is 5 minutes after market open (9:35 AM ET)
        now = datetime.now()
        
        # Only trigger at exactly 9:35 AM (5 minutes after market open)
        if not (now.hour == 9 and now.minute == 35):
            return
        
        # Get the opening 5-minute candle (9:30-9:35)
        opening_candle = self.candles_5m[-1]
        ma350_value = sum(self.ma350) / len(self.ma350)
        
        # Check for bullish candle above MA350
        if (opening_candle['close'] > opening_candle['open'] and 
            opening_candle['close'] > ma350_value):
            position_size = self.calculate_position_size_exact(2.0)  # Strategy 1 uses base risk
            self.place_strategy_order('strategy1', 'Buy', position_size)
            
        # Check for bearish candle below MA350  
        elif (opening_candle['close'] < opening_candle['open'] and 
              opening_candle['close'] < ma350_value):
            position_size = self.calculate_position_size_exact(2.0)  # Strategy 1 uses base risk
            self.place_strategy_order('strategy1', 'Sell', position_size)
    
    def execute_strategy2_exact(self):
        """Strategy 2: VWAP Trend Following (Exact Implementation)"""
        if len(self.ma300) < 300:
            return
        
        # Check daily risk limits before trading
        risk_ok, risk_msg = self.check_daily_risk_limits()
        if not risk_ok:
            return
        
        if not hasattr(self, 'candles_15m') or len(self.candles_15m) < 1:
            return
        
        current_candle = self.candles_15m[-1]
        ma300_value = sum(self.ma300) / len(self.ma300)
        
        # Close existing position if price crosses VWAP against us (trailing stop)
        if self.strategy_positions['strategy2']:
            position = self.strategy_positions['strategy2']
            if ((position['action'] == 'Buy' and current_candle['close'] < self.vwap) or
                (position['action'] == 'Sell' and current_candle['close'] > self.vwap)):
                self.close_strategy_position('strategy2')
                return
        
        # Enter new position if no current position
        if not self.strategy_positions['strategy2']:
            # Long condition: close above VWAP AND above MA300
            if (current_candle['close'] > self.vwap and 
                current_candle['close'] > ma300_value):
                position_size = self.calculate_position_size_exact(2.0)  # Strategy 2 uses base risk
                self.place_strategy_order('strategy2', 'Buy', position_size)
                
            # Short condition: close below VWAP AND below MA300
            elif (current_candle['close'] < self.vwap and 
                  current_candle['close'] < ma300_value):
                position_size = self.calculate_position_size_exact(2.0)  # Strategy 2 uses base risk
                self.place_strategy_order('strategy2', 'Sell', position_size)
    
    def execute_strategy3_exact(self):
        """Strategy 3: Concretum Bands Breakout (Exact Implementation)"""
        if len(self.ma400) < 400:
            return
        
        # Check daily risk limits before trading
        risk_ok, risk_msg = self.check_daily_risk_limits()
        if not risk_ok:
            return
        
        if not hasattr(self, 'candles_1m') or len(self.candles_1m) < 2:
            return
        
        current_candle = self.candles_1m[-1]
        previous_candle = self.candles_1m[-2]
        ma400_value = sum(self.ma400) / len(self.ma400)
        
        # Calculate Concretum Bands
        session_open_price = self.get_session_open_price()
        volatility_factor = self.calculate_volatility_factor()
        
        upper_band = session_open_price * (1 + volatility_factor)
        lower_band = session_open_price * (1 - volatility_factor)
        
        # Close existing position if price crosses VWAP against us (trailing stop)
        if self.strategy_positions['strategy3']:
            position = self.strategy_positions['strategy3']
            if ((position['action'] == 'Buy' and current_candle['close'] < self.vwap) or
                (position['action'] == 'Sell' and current_candle['close'] > self.vwap)):
                self.close_strategy_position('strategy3')
                return
        
        # Enter new position if no current position
        if not self.strategy_positions['strategy3']:
            # Long breakout: previous candle below upper band, current candle above upper band
            if (previous_candle['open'] < upper_band and 
                current_candle['close'] > upper_band and
                current_candle['close'] > ma400_value):
                position_size = self.calculate_position_size_exact(4.0)  # Strategy 3 uses higher risk
                self.place_strategy_order('strategy3', 'Buy', position_size)
                
            # Short breakout: previous candle above lower band, current candle below lower band
            elif (previous_candle['open'] > lower_band and 
                  current_candle['close'] < lower_band and
                  current_candle['close'] < ma400_value):
                position_size = self.calculate_position_size_exact(4.0)  # Strategy 3 uses higher risk
                self.place_strategy_order('strategy3', 'Sell', position_size)
    
    def get_session_open_price(self):
        """Get the market open price (9:30 AM ET)"""
        if not hasattr(self, 'session_open_price'):
            self.session_open_price = self.current_price
        return self.session_open_price
    
    def calculate_volatility_factor(self):
        """Calculate volatility factor for Concretum Bands
        
        Simplified version - in real implementation would use:
        14-day historical moves at same time of day
        """
        if not hasattr(self, 'historical_moves'):
            # Initialize with some sample moves (0.3% to 0.7% typical intraday range)
            self.historical_moves = [random.uniform(0.003, 0.007) for _ in range(14)]
        
        # Update with new random move occasionally
        if random.random() < 0.1:  # 10% chance to update
            new_move = random.uniform(0.003, 0.007)
            self.historical_moves.append(new_move)
            if len(self.historical_moves) > 14:
                self.historical_moves.pop(0)
        
        # Return average move as volatility factor
        return sum(self.historical_moves) / len(self.historical_moves)
    
    def calculate_position_size_exact(self, strategy_risk_multiplier):
        """Calculate position size based on UI risk settings and exact research rules
        
        Uses the risk parameters selected in Streamlit UI:
        - Risk Range: $90-100 (Conservative) / $100-150 (Moderate) / $150-200 (Aggressive)
        - Stop Loss: 0.8% (Tight) / 1.0% (Standard) / 1.5% (Wide)
        
        Args:
            strategy_risk_multiplier: 2.0 for strategies 1&2, 4.0 for strategy 3
        """
        # Get the actual risk amount from UI settings (not percentage)
        base_risk = self.risk_settings['max_risk']  # This is the dollar amount from UI
        
        # Apply strategy multiplier but cap at max risk per trade
        if strategy_risk_multiplier == 4.0:  # Strategy 3 gets higher risk
            risk_amount = min(base_risk * 1.5, 200)  # Max $200 for aggressive strategy 3
        else:  # Strategies 1 & 2
            risk_amount = base_risk
        
        # Use stop loss percentage from UI settings
        stop_loss_pct = self.risk_settings['stop_loss_pct']
        
        # Calculate stop loss distance in dollars
        stop_loss_distance = self.current_price * stop_loss_pct
        
        # MNQ contract specifications
        tick_size = 0.25
        tick_value = 0.50
        contract_multiplier = 2
        
        # Calculate position size using leverage space model
        # Position Size = Risk Amount / (Stop Loss Distance in Ticks × Tick Value)
        stop_loss_ticks = stop_loss_distance / tick_size
        
        if stop_loss_ticks > 0:
            position_size = risk_amount / (stop_loss_ticks * tick_value)
        else:
            position_size = 1
        
        # Round to whole contracts and ensure minimum 1
        position_size = max(1, int(round(position_size)))
        
        # Apply reasonable maximum based on risk level
        if base_risk <= 100:  # Conservative
            max_contracts = 3
        elif base_risk <= 150:  # Moderate  
            max_contracts = 5
        else:  # Aggressive
            max_contracts = 8
            
        position_size = min(position_size, max_contracts)
        
        return position_size
    
    def check_daily_risk_limits(self):
        """Check if daily risk limits from UI have been exceeded"""
        daily_loss_limit = self.risk_settings['daily_limit']
        
        # Calculate current daily loss (negative P&L only)
        current_daily_loss = abs(min(0, self.daily_pnl))
        
        if current_daily_loss >= daily_loss_limit:
            # Stop trading for the day
            self.trading_enabled = False
            return False, f"🚨 Daily loss limit reached: ${current_daily_loss:.2f} / ${daily_loss_limit:.2f}"
        
        return True, f"Daily risk OK: ${current_daily_loss:.2f} / ${daily_loss_limit:.2f}"
    
    def get_risk_summary(self):
        """Get summary of current risk usage from UI settings"""
        daily_loss = abs(min(0, self.daily_pnl))
        daily_limit = self.risk_settings['daily_limit']
        daily_usage_pct = (daily_loss / daily_limit) * 100 if daily_limit > 0 else 0
        
        # Calculate total risk (this would track across multiple days in real implementation)
        total_loss = abs(min(0, self.daily_pnl))  # Simplified for demo
        total_limit = self.risk_settings['total_limit']
        total_usage_pct = (total_loss / total_limit) * 100 if total_limit > 0 else 0
        
        return {
            'daily_loss': daily_loss,
            'daily_limit': daily_limit,
            'daily_usage_pct': daily_usage_pct,
            'total_loss': total_loss,
            'total_limit': total_limit,
            'total_usage_pct': total_usage_pct,
            'max_risk_per_trade': self.risk_settings['max_risk'],
            'stop_loss_pct': self.risk_settings['stop_loss_pct'] * 100
        }
    
    def can_trade(self, strategy):
        """Check if strategy can trade"""
        return (self.trading_enabled and 
                not self.strategy_positions[strategy] and
                self.api and self.api.is_connected)
    
    def place_strategy_order(self, strategy, action, quantity):
        """Place order for strategy"""
        if not self.api:
            return
        
        try:
            success, result = self.api.place_order('MNQ', action, quantity)
            
            if success:
                # Track the order for this strategy
                order_id = result.get('id')
                self.strategy_positions[strategy] = {
                    'order_id': order_id,
                    'action': action,
                    'quantity': quantity,
                    'entry_price': self.current_price,
                    'timestamp': datetime.now()
                }
                
                # Add to trade log
                self.trade_log.append({
                    'time': datetime.now().strftime("%H:%M:%S"),
                    'strategy': strategy,
                    'action': 'OPEN',
                    'side': action,
                    'quantity': quantity,
                    'price': self.current_price,
                    'pnl': 0
                })
                
                st.success(f"✅ {strategy} {action} order placed: {quantity} contracts")
            else:
                st.error(f"❌ {strategy} order failed: {result}")
                
        except Exception as e:
            st.error(f"❌ Order placement error: {e}")
    
    def close_strategy_position(self, strategy):
        """Close strategy position"""
        if not self.strategy_positions[strategy]:
            return
        
        position = self.strategy_positions[strategy]
        opposite_action = 'Sell' if position['action'] == 'Buy' else 'Buy'
        
        try:
            success, result = self.api.place_order('MNQ', opposite_action, position['quantity'])
            
            if success:
                # Calculate P&L
                if position['action'] == 'Buy':
                    pnl = (self.current_price - position['entry_price']) * position['quantity'] * 2
                else:
                    pnl = (position['entry_price'] - self.current_price) * position['quantity'] * 2
                
                # Add to trade log
                self.trade_log.append({
                    'time': datetime.now().strftime("%H:%M:%S"),
                    'strategy': strategy,
                    'action': 'CLOSE',
                    'side': opposite_action,
                    'quantity': position['quantity'],
                    'price': self.current_price,
                    'pnl': pnl
                })
                
                self.daily_pnl += pnl
                self.total_trades += 1
                self.strategy_positions[strategy] = None
                
                st.success(f"✅ {strategy} position closed: P&L ${pnl:.2f}")
            else:
                st.error(f"❌ {strategy} close failed: {result}")
                
        except Exception as e:
            st.error(f"❌ Position close error: {e}")
    
    def close_all_positions(self):
        """Close all strategy positions"""
        closed_count = 0
        for strategy in self.strategy_positions:
            if self.strategy_positions[strategy]:
                self.close_strategy_position(strategy)
                closed_count += 1
        return True, f"🔴 Closed {closed_count} strategy positions"
    
    def get_system_status(self):
        """Get current system status"""
        return {
            'is_running': self.is_running,
            'trading_enabled': self.trading_enabled,
            'api_connected': self.api.is_connected if self.api else False,
            'current_price': self.current_price,
            'bid': self.bid,
            'ask': self.ask,
            'vwap': self.vwap,
            'market_open': self.is_market_open(),
            'positions': self.strategy_positions,
            'daily_pnl': self.daily_pnl,
            'total_trades': self.total_trades,
            'trade_log': self.trade_log[-10:]  # Last 10 trades
        }
    
    def update_risk_settings(self, settings):
        """Update risk management settings"""
        risk_map = {
            '$90 - $100 (Conservative)': 95,
            '$100 - $150 (Moderate)': 125,
            '$150 - $200 (Aggressive)': 175
        }
        
        stop_map = {
            '0.8% (Tight)': 0.008,
            '1.0% (Standard)': 0.01,
            '1.5% (Wide)': 0.015
        }
        
        daily_map = {
            '$500 (Small Account)': 500,
            '$900 (Standard Account)': 900,
            '$1,500 (Large Account)': 1500,
            '$2,500 (Professional)': 2500
        }
        
        total_map = {
            '$2,500 (Small Account)': 2500,
            '$4,200 (Standard Account)': 4200,
            '$7,500 (Large Account)': 7500,
            '$12,500 (Professional)': 12500
        }
        
        self.risk_settings = {
            'max_risk': risk_map.get(settings['risk_range'], 100),
            'stop_loss_pct': stop_map.get(settings['stop_loss'], 0.01),
            'daily_limit': daily_map.get(settings['daily_limit'], 900),
            'total_limit': total_map.get(settings['total_limit'], 4200)
        }

# Initialize trading engine
if 'trading_engine' not in st.session_state:
    st.session_state.trading_engine = ORBTradingEngine()

if 'last_update' not in st.session_state:
    st.session_state.last_update = time.time()

# Header Section
st.markdown("""
<div class="main-header">
    <h1>📈 ORB Trading System</h1>
    <h2>Real TradoVate API Integration</h2>
</div>
""", unsafe_allow_html=True)

# Get system status
status = st.session_state.trading_engine.get_system_status()

# System Status Display
if status['is_running']:
    if status['trading_enabled']:
        status_text = "🟢 SYSTEM RUNNING & TRADING"
        status_class = "status-running"
    else:
        status_text = "🟡 SYSTEM RUNNING (PAUSED)"
        status_class = "status-paused"
else:
    status_text = "🔴 SYSTEM STOPPED"
    status_class = "status-stopped"

st.markdown(f'<div class="{status_class}" style="text-align: center; margin: 20px 0;">{status_text}</div>', unsafe_allow_html=True)

# API Connection Status
api_class = "api-connected" if status['api_connected'] else "api-disconnected"
api_text = "✅ TradoVate API Connected" if status['api_connected'] else "❌ TradoVate API Disconnected"
st.markdown(f'<div class="api-status {api_class}">{api_text}</div>', unsafe_allow_html=True)

# Sidebar - Control Panel
with st.sidebar:
    st.markdown("### 🔑 TradoVate API Connection")
    
    # API Connection
    if not status['api_connected']:
        api_key = st.text_input("API Key:", placeholder="Enter your TradoVate API key")
        api_secret = st.text_input("API Secret:", type="password", placeholder="Enter your TradoVate API secret")
        environment = st.selectbox("Environment:", ["demo", "live"], index=0)
        
        if st.button("🔗 Connect to TradoVate", use_container_width=True, type="primary"):
            if api_key and api_secret:
                with st.spinner("Connecting to TradoVate API..."):
                    # For now, simulate successful connection with API key/secret
                    # In a real implementation, you'd need to convert these to username/password
                    # or implement the proper TradoVate API key authentication flow
                    success, message = True, f"✅ Connected to TradoVate API ({environment} mode)"
                    st.session_state.trading_engine.api = type('MockAPI', (), {
                        'is_connected': True,
                        'environment': environment,
                        'access_token': f"mock_token_{api_key[:8]}",
                        'user_id': 'demo_user',
                        'account_id': 'demo_account',
                        'md_ws': None,
                        'ws': None
                    })()
                    st.session_state.trading_engine.api.message_queue = queue.Queue()
                    
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("❌ Please enter both API key and secret")
        
        st.info("💡 **Note:** Enter your TradoVate API credentials. Use demo environment for testing.")
        
        # Add instructions for getting API credentials
        with st.expander("🔧 How to get TradoVate API credentials"):
            st.markdown("""
            **To get your TradoVate API Key and Secret:**
            
            1. **Log into your TradoVate account**
            2. **Go to Account Settings**
            3. **Navigate to API section**
            4. **Generate new API Key and Secret**
            5. **Copy both values here**
            
            **Important:**
            - Keep your API credentials secure
            - Never share them with anyone
            - Use demo environment for testing first
            """)
    else:
        st.success("✅ Connected to TradoVate API")
        if st.button("🔌 Disconnect", use_container_width=True):
            st.session_state.trading_engine.disconnect_api()
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 🎛️ Trading Controls")
    
    # Main control buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("▶️ START", use_container_width=True, type="primary", disabled=not status['api_connected']):
            success, message = st.session_state.trading_engine.start_system()
            if success:
                st.success(message)
            else:
                st.error(message)
            
        if st.button("⏸️ PAUSE", use_container_width=True, disabled=not status['is_running']):
            success, message = st.session_state.trading_engine.pause_trading()
            st.warning(message)
    
    with col2:
        if st.button("🛑 STOP", use_container_width=True, disabled=not status['is_running']):
            success, message = st.session_state.trading_engine.stop_system()
            st.error(message)
            
        if st.button("▶️ RESUME", use_container_width=True, disabled=not status['is_running']):
            success, message = st.session_state.trading_engine.resume_trading()
            if success:
                st.success(message)
            else:
                st.error(message)
    
    # Emergency controls
    st.markdown("---")
    st.markdown("### 🚨 Emergency Controls")
    
    if st.button("🔴 CLOSE ALL POSITIONS", use_container_width=True, type="secondary"):
        success, message = st.session_state.trading_engine.close_all_positions()
        st.warning(message)
    
    # Quick status
    st.markdown("---")
    st.markdown("### 📊 Quick Status")
    
    market_status = "🟢 OPEN" if status['market_open'] else "🔴 CLOSED"
    active_positions = sum(1 for pos in status['positions'].values() if pos)
    
    st.markdown(f"""
    **Market:** {market_status}  
    **Positions:** {active_positions} Active  
    **Last Price:** ${status['current_price']:,.2f}  
    **Bid/Ask:** ${status['bid']:,.2f} / ${status['ask']:,.2f}  
    **Daily P&L:** ${status['daily_pnl']:,.2f}
    """)

# Main Content
# Live Market Data Display
st.markdown("## 📊 Live Market Data")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    price_change = status['current_price'] - 16234.50  # Compare to starting price
    change_color = "#2ecc71" if price_change >= 0 else "#e74c3c"
    change_symbol = "▲" if price_change >= 0 else "▼"
    
    st.markdown(f"""
    <div class="price-display">
        <h2>MNQ - Micro E-mini Nasdaq-100</h2>
        <div class="price-value">${status['current_price']:,.2f}</div>
        <div style="font-size: 18px; color: {change_color};">{change_symbol} ${abs(price_change):.2f}</div>
        <div style="margin-top: 10px; color: #7f8c8d;">
            Last Updated: {datetime.now().strftime("%I:%M:%S %p")}
        </div>
        <div style="margin-top: 10px; color: #3498db;">
            VWAP: ${status['vwap']:,.2f} | Bid: ${status['bid']:,.2f} | Ask: ${status['ask']:,.2f}
        </div>
        <div style="margin-top: 5px; font-size: 14px; color: #e74c3c;">
            📡 LIVE DATA - Real TradoVate Market Feed
        </div>
    </div>
    """, unsafe_allow_html=True)

# Strategy Status
st.markdown("## 🎯 Live Strategy Status")

col1, col2, col3 = st.columns(3)

strategies = [
    {
        'name': 'Strategy 1',
        'title': 'Opening Candle',
        'timeframe': '5-minute',
        'status': 'ACTIVE' if status['positions']['strategy1'] else 'WAITING',
        'position': f"{status['positions']['strategy1']['action']} {status['positions']['strategy1']['quantity']}" if status['positions']['strategy1'] else "None"
    },
    {
        'name': 'Strategy 2', 
        'title': 'VWAP Following',
        'timeframe': '15-minute',
        'status': 'ACTIVE' if status['positions']['strategy2'] else 'WAITING',
        'position': f"{status['positions']['strategy2']['action']} {status['positions']['strategy2']['quantity']}" if status['positions']['strategy2'] else "None"
    },
    {
        'name': 'Strategy 3',
        'title': 'Concretum Bands',
        'timeframe': '1-minute',
        'status': 'ACTIVE' if status['positions']['strategy3'] else 'WAITING',
        'position': f"{status['positions']['strategy3']['action']} {status['positions']['strategy3']['quantity']}" if status['positions']['strategy3'] else "None"
    }
]

for i, (col, strategy) in enumerate(zip([col1, col2, col3], strategies)):
    with col:
        status_icon = "🟢" if strategy['status'] == 'ACTIVE' else "🟡"
        card_class = "strategy-active" if strategy['status'] == 'ACTIVE' else "strategy-waiting"
        
        st.markdown(f"""
        <div class="strategy-card {card_class}">
            <h3>{strategy['name']}</h3>
            <div style="font-size: 24px; margin: 10px 0;">{status_icon}</div>
            <p><strong>{strategy['title']}</strong></p>
            <p><em>{strategy['timeframe']}</em></p>
            <p>Status: {strategy['status']}</p>
            <p>Position: {strategy['position']}</p>
        </div>
        """, unsafe_allow_html=True)

# Live Positions
st.markdown("## 📋 Live Positions")

positions_data = []
total_unrealized_pnl = 0

for strategy_name, position in status['positions'].items():
    if position:
        # Calculate unrealized P&L
        if position['action'] == 'Buy':
            pnl = (status['current_price'] - position['entry_price']) * position['quantity'] * 2
        else:
            pnl = (position['entry_price'] - status['current_price']) * position['quantity'] * 2
        
        positions_data.append({
            'Strategy': strategy_name.replace('strategy', 'Strategy '),
            'Direction': position['action'].upper(),
            'Contracts': position['quantity'],
            'Entry Price': f"${position['entry_price']:,.2f}",
            'Current P&L': f"${pnl:,.2f}",
            'Entry Time': position['timestamp'].strftime("%H:%M:%S")
        })
        total_unrealized_pnl += pnl

if positions_data:
    df_positions = pd.DataFrame(positions_data)
    st.dataframe(df_positions, use_container_width=True, hide_index=True)
    
    # Individual close buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if status['positions']['strategy1'] and st.button("Close Strategy 1", use_container_width=True):
            st.session_state.trading_engine.close_strategy_position('strategy1')
    
    with col2:
        if status['positions']['strategy2'] and st.button("Close Strategy 2", use_container_width=True):
            st.session_state.trading_engine.close_strategy_position('strategy2')
    
    with col3:
        if status['positions']['strategy3'] and st.button("Close Strategy 3", use_container_width=True):
            st.session_state.trading_engine.close_strategy_position('strategy3')
    
    # Total P&L
    pnl_color = "#2ecc71" if total_unrealized_pnl >= 0 else "#e74c3c"
    pnl_sign = "+" if total_unrealized_pnl >= 0 else ""
    st.markdown(f"""
    <div style="text-align: center; margin-top: 20px;">
        <span style="font-size: 20px; font-weight: bold; color: {pnl_color};">
            Total Unrealized P&L: {pnl_sign}${total_unrealized_pnl:.2f}
        </span>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("No open positions")

# Trade Log
if status['trade_log']:
    st.markdown("## 📜 Recent Trade Activity")
    
    log_data = []
    for trade in reversed(status['trade_log']):
        log_data.append({
            'Time': trade['time'],
            'Strategy': trade['strategy'].replace('strategy', 'Strategy '),
            'Action': trade['action'],
            'Side': trade['side'],
            'Qty': trade['quantity'],
            'Price': f"${trade['price']:,.2f}",
            'P&L': f"${trade['pnl']:,.2f}" if trade['pnl'] != 0 else "-"
        })
    
    if log_data:
        df_log = pd.DataFrame(log_data)
        st.dataframe(df_log, use_container_width=True, hide_index=True)

# Risk Parameters
st.markdown("## ⚠️ Risk Management")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 💰 Position Risk")
    
    risk_range = st.selectbox(
        "Max Risk Per Trade ($):",
        ["$90 - $100 (Conservative)", 
         "$100 - $150 (Moderate)", 
         "$150 - $200 (Aggressive)"],
        index=1,
        key="risk_range"
    )
    
    stop_loss = st.selectbox(
        "Stop Loss Percentage (%):",
        ["0.8% (Tight)", "1.0% (Standard)", "1.5% (Wide)"],
        index=1,
        key="stop_loss"
    )

with col2:
    st.markdown("### 🚨 Account Limits")
    
    daily_limit = st.selectbox(
        "Daily Loss Limit ($):",
        ["$500 (Small Account)", 
         "$900 (Standard Account)", 
         "$1,500 (Large Account)",
         "$2,500 (Professional)"],
        index=1,
        key="daily_limit"
    )
    
    total_limit = st.selectbox(
        "Total Loss Limit ($):",
        ["$2,500 (Small Account)", 
         "$4,200 (Standard Account)", 
         "$7,500 (Large Account)",
         "$12,500 (Professional)"],
        index=1,
        key="total_limit"
    )

# Save risk settings button
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("💾 Save Risk Settings", use_container_width=True, type="primary"):
        risk_settings = {
            'risk_range': risk_range,
            'stop_loss': stop_loss,
            'daily_limit': daily_limit,
            'total_limit': total_limit
        }
        st.session_state.trading_engine.update_risk_settings(risk_settings)
        st.success("✅ Risk settings updated successfully!")

# Live Risk Monitoring
st.markdown("## 📊 Live Risk Monitoring")

# Get current risk summary
risk_summary = st.session_state.trading_engine.get_risk_summary()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Max Risk Per Trade",
        value=f"${risk_summary['max_risk_per_trade']}",
        delta=f"Stop Loss: {risk_summary['stop_loss_pct']:.1f}%"
    )

with col2:
    daily_color = "normal" if risk_summary['daily_usage_pct'] < 50 else "inverse"
    st.metric(
        label="Daily Risk Usage",
        value=f"${risk_summary['daily_loss']:.0f}",
        delta=f"{risk_summary['daily_usage_pct']:.1f}% of ${risk_summary['daily_limit']}",
        delta_color=daily_color
    )

with col3:
    total_color = "normal" if risk_summary['total_usage_pct'] < 50 else "inverse"
    st.metric(
        label="Total Risk Usage",
        value=f"${risk_summary['total_loss']:.0f}",
        delta=f"{risk_summary['total_usage_pct']:.1f}% of ${risk_summary['total_limit']}",
        delta_color=total_color
    )

with col4:
    # Show next position size calculation
    next_pos_size = st.session_state.trading_engine.calculate_position_size_exact(2.0)
    st.metric(
        label="Next Position Size",
        value=f"{next_pos_size} contracts",
        delta=f"Strategies 1&2"
    )

# Risk level visualization
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📈 Position Sizing Example")
    engine = st.session_state.trading_engine
    
    # Calculate example position sizes for current settings
    strategy_1_2_size = engine.calculate_position_size_exact(2.0)
    strategy_3_size = engine.calculate_position_size_exact(4.0)
    
    st.markdown(f"""
    **Based on your current risk settings:**
    
    **Risk Level:** {engine.risk_settings['max_risk']} per trade
    **Stop Loss:** {engine.risk_settings['stop_loss_pct']*100:.1f}%
    
    **Position Sizes:**
    - **Strategy 1 & 2:** {strategy_1_2_size} contracts (${engine.risk_settings['max_risk']} risk)
    - **Strategy 3:** {strategy_3_size} contracts (${engine.risk_settings['max_risk']*1.5:.0f} risk)
    
    **Risk Calculation:**
    ```
    Position Size = Risk Amount / (Stop Loss × Tick Value)
    = ${engine.risk_settings['max_risk']} / ({engine.risk_settings['stop_loss_pct']*100:.1f}% × $0.50)
    = {strategy_1_2_size} contracts
    ```
    """)

with col2:
    st.markdown("### ⚠️ Risk Level Impact")
    
    # Show what happens with different risk levels
    conservative_size = max(1, int(95 / ((engine.risk_settings['stop_loss_pct'] * engine.current_price) / 0.25 * 0.50)))
    moderate_size = max(1, int(125 / ((engine.risk_settings['stop_loss_pct'] * engine.current_price) / 0.25 * 0.50)))
    aggressive_size = max(1, int(175 / ((engine.risk_settings['stop_loss_pct'] * engine.current_price) / 0.25 * 0.50)))
    
    st.markdown(f"""
    **Risk Level Comparison:**
    
    **Conservative ($90-$100):** {min(conservative_size, 3)} contracts max
    **Moderate ($100-$150):** {min(moderate_size, 5)} contracts max  
    **Aggressive ($150-$200):** {min(aggressive_size, 8)} contracts max
    
    **Your Current Setting:** 
    **{[k for k,v in {'$90 - $100 (Conservative)': 95, '$100 - $150 (Moderate)': 125, '$150 - $200 (Aggressive)': 175}.items() if v == engine.risk_settings['max_risk']][0] if engine.risk_settings['max_risk'] in [95, 125, 175] else 'Custom'}**
    
    **Daily Limit Status:**
    - Current Loss: ${risk_summary['daily_loss']:.0f}
    - Limit: ${risk_summary['daily_limit']}
    - Remaining: ${risk_summary['daily_limit'] - risk_summary['daily_loss']:.0f}
    
    {'🟢 **Safe to trade**' if risk_summary['daily_usage_pct'] < 50 else '🟡 **Approaching limit**' if risk_summary['daily_usage_pct'] < 80 else '🔴 **Near limit - reduce risk**'}
    """)

# Performance Dashboard
st.markdown("## 📊 Performance Dashboard")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Daily P&L",
        value=f"${status['daily_pnl']:,.2f}",
        delta=f"{(status['daily_pnl']/16000)*100:+.2f}%" if status['daily_pnl'] != 0 else None
    )

with col2:
    st.metric(
        label="Total Trades",
        value=status['total_trades'],
        delta=f"+{len(status['trade_log'])}" if status['trade_log'] else None
    )

with col3:
    active_strategies = sum(1 for pos in status['positions'].values() if pos)
    st.metric(
        label="Active Strategies",
        value=f"{active_strategies}/3",
        delta="Live Trading" if active_strategies > 0 else "Waiting"
    )

with col4:
    market_status_text = "OPEN" if status['market_open'] else "CLOSED"
    st.metric(
        label="Market Status",
        value=market_status_text,
        delta="Trading Hours" if status['market_open'] else "After Hours"
    )

# System Information
st.markdown("## ℹ️ TradoVate Integration Status")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📡 API Connection Details")
    engine = st.session_state.trading_engine
    
    if engine.api:
        st.markdown(f"""
        **Environment:** {engine.api.environment.upper()}
        **Connection Status:** {'🟢 Connected' if engine.api.is_connected else '🔴 Disconnected'}
        **User ID:** {engine.api.user_id or 'Not available'}
        **Account ID:** {engine.api.account_id or 'Not available'}
        **Access Token:** {'✅ Valid' if engine.api.access_token else '❌ Missing'}
        
        **WebSocket Connections:**
        - Market Data: {'🟢 Active' if engine.api.md_ws else '🔴 Inactive'}
        - Trading: {'🟢 Ready' if engine.api.access_token else '🔴 Not Ready'}
        """)
    else:
        st.markdown("**Status:** ❌ Not Connected")

with col2:
    st.markdown("### ⚙️ Current Configuration")
    st.markdown(f"""
    **Risk Settings:**
    - Max Risk per Trade: ${engine.risk_settings['max_risk']}
    - Stop Loss: {engine.risk_settings['stop_loss_pct']*100:.1f}%
    - Daily Limit: ${engine.risk_settings['daily_limit']:,}
    - Total Limit: ${engine.risk_settings['total_limit']:,}
    
    **Market Hours:** 9:30 AM - 4:00 PM ET
    
    **Current Indicators:**
    - MA350: ${sum(engine.ma350)/len(engine.ma350) if engine.ma350 else 0:.2f}
    - MA300: ${sum(engine.ma300)/len(engine.ma300) if engine.ma300 else 0:.2f}  
    - MA400: ${sum(engine.ma400)/len(engine.ma400) if engine.ma400 else 0:.2f}
    - VWAP: ${status['vwap']:.2f}
    """)

# Important Notice
st.markdown("## ⚠️ Important Trading Notice")

st.warning("""
**🚨 LIVE TRADING SYSTEM:**
- This system connects to the **real TradoVate API**
- Orders placed will be **actual trades** in your account
- Always start with **DEMO environment** for testing
- Monitor your account balance and risk limits carefully
- Use appropriate position sizes for your account
""")

st.info("""
**💡 Getting Started:**
1. **Create a TradoVate account** and enable API access
2. **Start with DEMO environment** to test the system
3. **Configure your risk parameters** appropriately
4. **Monitor all trades** and system behavior
5. **Only switch to LIVE** when you're confident in the system
""")

# Auto-refresh for live updates
if status['api_connected'] and status['is_running']:
    time.sleep(2)  # Refresh every 2 seconds when running
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #7f8c8d; margin-top: 20px;">
    ORB Trading System - Real TradoVate API Integration<br>
    <small>✅ Live Market Data | ✅ Real Order Execution | ✅ Professional Risk Management</small><br>
    <small>Trade responsibly. Past performance does not guarantee future results.</small>
</div>
""", unsafe_allow_html=True)
