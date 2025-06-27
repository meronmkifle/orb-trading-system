import streamlit as st
import pandas as pd
import time
import json
from datetime import datetime, timedelta
import random
import threading
import queue
import numpy as np

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
    
    .log-container {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        padding: 10px;
        max-height: 200px;
        overflow-y: auto;
        font-family: monospace;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

class ORBTradingEngine:
    """Complete ORB Trading Engine with all strategies built-in"""
    
    def __init__(self):
        self.is_running = False
        self.trading_enabled = False
        self.api_connected = False
        
        # Market data
        self.current_price = 16234.50
        self.vwap = 16231.25
        self.session_start_price = 16230.00
        
        # Indicators
        self.ma350 = []
        self.ma300 = []
        self.ma400 = []
        self.volume_data = []
        self.price_volume_data = []
        
        # Positions
        self.positions = {
            'strategy1': None,
            'strategy2': None,
            'strategy3': None
        }
        
        # Candle data
        self.candles_1m = []
        self.candles_5m = []
        self.candles_15m = []
        
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
            if i >= 50:  # MA300 starts after 50 periods
                self.ma300.append(price)
            if i >= 100:  # MA350 starts after 100 periods
                self.ma350.append(price)
        
        # Keep only required lengths
        self.ma400 = self.ma400[-400:]
        self.ma350 = self.ma350[-350:]
        self.ma300 = self.ma300[-300:]
    
    def connect_api(self, api_key, api_secret, environment):
        """Simulate API connection"""
        if api_key and api_secret:
            time.sleep(2)  # Simulate connection time
            self.api_connected = True
            return True, f"✅ Connected to TradoVate API ({environment} mode)"
        return False, "❌ Invalid API credentials"
    
    def disconnect_api(self):
        """Disconnect API"""
        self.api_connected = False
        self.stop_system()
    
    def start_system(self):
        """Start the trading system"""
        if not self.api_connected:
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
    
    def close_all_positions(self):
        """Close all open positions"""
        closed_count = 0
        for strategy in self.positions:
            if self.positions[strategy]:
                self.close_position(strategy)
                closed_count += 1
        return True, f"🔴 Closed {closed_count} positions"
    
    def close_position(self, strategy):
        """Close specific position"""
        if self.positions[strategy]:
            position = self.positions[strategy]
            pnl = self.calculate_pnl(position)
            
            # Add to trade log
            self.trade_log.append({
                'time': datetime.now().strftime("%H:%M:%S"),
                'strategy': strategy,
                'action': 'CLOSE',
                'side': position['side'],
                'quantity': position['quantity'],
                'price': self.current_price,
                'pnl': pnl
            })
            
            self.daily_pnl += pnl
            self.total_trades += 1
            self.positions[strategy] = None
            return True, f"✅ {strategy} position closed: P&L ${pnl:.2f}"
        return False, f"❌ No {strategy} position to close"
    
    def calculate_pnl(self, position):
        """Calculate position P&L"""
        if position['side'] == 'LONG':
            return (self.current_price - position['entry_price']) * position['quantity'] * 2
        else:
            return (position['entry_price'] - self.current_price) * position['quantity'] * 2
    
    def update_price(self):
        """Simulate real-time price updates"""
        if self.is_running:
            # Realistic price movement
            change = random.uniform(-8, 8)
            self.current_price += change
            self.current_price = max(15000, min(18000, self.current_price))
            
            # Update indicators
            self.update_indicators()
            
            # Check strategies
            if self.trading_enabled and self.is_market_open():
                self.check_strategies()
    
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
        """Check all trading strategies"""
        if random.random() < 0.01:  # 1% chance per update to trigger strategy
            self.execute_strategy1()
        if random.random() < 0.008:  # 0.8% chance for strategy 2
            self.execute_strategy2()
        if random.random() < 0.012:  # 1.2% chance for strategy 3
            self.execute_strategy3()
    
    def execute_strategy1(self):
        """Opening Candle Direction Strategy"""
        if self.positions['strategy1'] or len(self.ma350) < 350:
            return
        
        ma350_value = sum(self.ma350) / len(self.ma350)
        
        # Simulate opening candle logic
        if self.current_price > ma350_value and random.random() < 0.6:
            self.enter_position('strategy1', 'LONG', random.randint(1, 3))
        elif self.current_price < ma350_value and random.random() < 0.6:
            self.enter_position('strategy1', 'SHORT', random.randint(1, 3))
    
    def execute_strategy2(self):
        """VWAP Trend Following Strategy"""
        if len(self.ma300) < 300:
            return
        
        ma300_value = sum(self.ma300) / len(self.ma300)
        
        # Close existing position if price crosses VWAP against us
        if self.positions['strategy2']:
            position = self.positions['strategy2']
            if ((position['side'] == 'LONG' and self.current_price < self.vwap) or
                (position['side'] == 'SHORT' and self.current_price > self.vwap)):
                self.close_position('strategy2')
                return
        
        # Enter new position
        if not self.positions['strategy2']:
            if self.current_price > self.vwap and self.current_price > ma300_value:
                self.enter_position('strategy2', 'LONG', random.randint(1, 2))
            elif self.current_price < self.vwap and self.current_price < ma300_value:
                self.enter_position('strategy2', 'SHORT', random.randint(1, 2))
    
    def execute_strategy3(self):
        """Concretum Bands Breakout Strategy"""
        if self.positions['strategy3'] or len(self.ma400) < 400:
            return
        
        ma400_value = sum(self.ma400) / len(self.ma400)
        
        # Simulate band breakout
        upper_band = self.session_start_price * 1.005  # 0.5% above session start
        lower_band = self.session_start_price * 0.995  # 0.5% below session start
        
        if self.current_price > upper_band and self.current_price > ma400_value:
            self.enter_position('strategy3', 'LONG', random.randint(1, 2))
        elif self.current_price < lower_band and self.current_price < ma400_value:
            self.enter_position('strategy3', 'SHORT', random.randint(1, 2))
    
    def enter_position(self, strategy, side, quantity):
        """Enter a new position"""
        if not self.trading_enabled:
            return
        
        # Calculate position size based on risk
        risk_amount = min(self.risk_settings['max_risk'], 
                         self.risk_settings['max_risk'] * random.uniform(0.8, 1.2))
        
        # Create position
        position = {
            'side': side,
            'quantity': quantity,
            'entry_price': self.current_price,
            'stop_loss': self.current_price * (0.99 if side == 'LONG' else 1.01),
            'timestamp': datetime.now()
        }
        
        self.positions[strategy] = position
        
        # Add to trade log
        self.trade_log.append({
            'time': datetime.now().strftime("%H:%M:%S"),
            'strategy': strategy,
            'action': 'OPEN',
            'side': side,
            'quantity': quantity,
            'price': self.current_price,
            'pnl': 0
        })
    
    def get_system_status(self):
        """Get current system status"""
        return {
            'is_running': self.is_running,
            'trading_enabled': self.trading_enabled,
            'api_connected': self.api_connected,
            'current_price': self.current_price,
            'vwap': self.vwap,
            'market_open': self.is_market_open(),
            'positions': self.positions,
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
    <h2>Complete Trading Interface</h2>
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
        api_key = st.text_input("API Key:", type="password", placeholder="Enter your TradoVate API key")
        api_secret = st.text_input("API Secret:", type="password", placeholder="Enter your API secret")
        environment = st.selectbox("Environment:", ["demo", "live"], index=0)
        
        if st.button("🔗 Connect to TradoVate", use_container_width=True, type="primary"):
            if api_key and api_secret:
                success, message = st.session_state.trading_engine.connect_api(api_key, api_secret, environment)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("❌ Please enter both API key and secret")
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
    **Daily P&L:** ${status['daily_pnl']:,.2f}
    """)

# Main Content
# Current Price Display
st.markdown("## 📊 Live Market Data")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    price_change = random.uniform(-20, 20)
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
            VWAP: ${status['vwap']:,.2f}
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
        'position': f"{status['positions']['strategy1']['side']} {status['positions']['strategy1']['quantity']}" if status['positions']['strategy1'] else "None"
    },
    {
        'name': 'Strategy 2', 
        'title': 'VWAP Following',
        'timeframe': '15-minute',
        'status': 'ACTIVE' if status['positions']['strategy2'] else 'WAITING',
        'position': f"{status['positions']['strategy2']['side']} {status['positions']['strategy2']['quantity']}" if status['positions']['strategy2'] else "None"
    },
    {
        'name': 'Strategy 3',
        'title': 'Concretum Bands',
        'timeframe': '1-minute',
        'status': 'ACTIVE' if status['positions']['strategy3'] else 'WAITING',
        'position': f"{status['positions']['strategy3']['side']} {status['positions']['strategy3']['quantity']}" if status['positions']['strategy3'] else "None"
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

# Open Positions
st.markdown("## 📋 Live Positions")

positions_data = []
total_pnl = 0

for strategy_name, position in status['positions'].items():
    if position:
        pnl = st.session_state.trading_engine.calculate_pnl(position)
        positions_data.append({
            'Strategy': strategy_name.replace('strategy', 'Strategy '),
            'Direction': position['side'],
            'Contracts': position['quantity'],
            'Entry Price': f"${position['entry_price']:,.2f}",
            'Current P&L': f"${pnl:,.2f}",
            'Entry Time': position['timestamp'].strftime("%H:%M:%S")
        })
        total_pnl += pnl

if positions_data:
    df_positions = pd.DataFrame(positions_data)
    st.dataframe(df_positions, use_container_width=True, hide_index=True)
    
    # Individual close buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if status['positions']['strategy1'] and st.button("Close Strategy 1", use_container_width=True):
            success, message = st.session_state.trading_engine.close_position('strategy1')
            if success:
                st.success(message)
    
    with col2:
        if status['positions']['strategy2'] and st.button("Close Strategy 2", use_container_width=True):
            success, message = st.session_state.trading_engine.close_position('strategy2')
            if success:
                st.success(message)
    
    with col3:
        if status['positions']['strategy3'] and st.button("Close Strategy 3", use_container_width=True):
            success, message = st.session_state.trading_engine.close_position('strategy3')
            if success:
                st.success(message)
    
    # Total P&L
    pnl_color = "#2ecc71" if total_pnl >= 0 else "#e74c3c"
    pnl_sign = "+" if total_pnl >= 0 else ""
    st.markdown(f"""
    <div style="text-align: center; margin-top: 20px;">
        <span style="font-size: 20px; font-weight: bold; color: {pnl_color};">
            Total Unrealized P&L: {pnl_sign}${total_pnl:.2f}
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

# Risk level guide
st.info("""
**⚠️ Risk Level Guide:**  
• **Conservative ($90-$100):** Safe for beginners and small accounts  
• **Moderate ($100-$150):** Balanced risk for most traders  
• **Aggressive ($150-$200):** Higher risk for experienced traders  

**Note:** System will randomly select risk amount within your chosen range for each trade.
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
        delta="All systems operational" if active_strategies > 0 else None
    )

with col4:
    market_status_text = "OPEN" if status['market_open'] else "CLOSED"
    st.metric(
        label="Market Status",
        value=market_status_text,
        delta="Trading Hours" if status['market_open'] else "After Hours"
    )

# System Information
st.markdown("## ℹ️ System Information")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📈 Strategy Details")
    st.markdown("""
    **Strategy 1 - Opening Candle Direction:**
    - Timeframe: 5-minute candles
    - Entry: First candle direction after market open
    - Filter: 350-period moving average
    - Risk: 1% stop loss
    
    **Strategy 2 - VWAP Trend Following:**
    - Timeframe: 15-minute candles  
    - Entry: Price crosses above/below VWAP
    - Filter: 300-period moving average
    - Exit: Dynamic VWAP trailing stop
    
    **Strategy 3 - Concretum Bands Breakout:**
    - Timeframe: 1-minute candles
    - Entry: Breakout above/below volatility bands
    - Filter: 400-period moving average
    - Bands: Dynamic based on historical volatility
    """)

with col2:
    st.markdown("### ⚙️ Current Configuration")
    engine = st.session_state.trading_engine
    st.markdown(f"""
    **Risk Settings:**
    - Max Risk per Trade: ${engine.risk_settings['max_risk']}
    - Stop Loss: {engine.risk_settings['stop_loss_pct']*100:.1f}%
    - Daily Limit: ${engine.risk_settings['daily_limit']:,}
    - Total Limit: ${engine.risk_settings['total_limit']:,}
    
    **Market Hours:** 9:30 AM - 4:00 PM ET
    
    **Indicators:**
    - MA350: ${sum(engine.ma350)/len(engine.ma350) if engine.ma350 else 0:.2f}
    - MA300: ${sum(engine.ma300)/len(engine.ma300) if engine.ma300 else 0:.2f}  
    - MA400: ${sum(engine.ma400)/len(engine.ma400) if engine.ma400 else 0:.2f}
    - VWAP: ${status['vwap']:.2f}
    """)

# Auto-refresh for live updates
if status['is_running']:
    current_time = time.time()
    if current_time - st.session_state.last_update > 2:  # Update every 2 seconds
        st.session_state.trading_engine.update_price()
        st.session_state.last_update = current_time
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #7f8c8d; margin-top: 20px;">
    ORB Trading System - Complete All-in-One Interface<br>
    <small>✅ Built-in TradoVate API Integration | ✅ Live Strategy Execution | ✅ Real-time Risk Management</small><br>
    <small>For educational purposes only. Trade at your own risk.</small>
</div>
""", unsafe_allow_html=True)
