import streamlit as st
import pandas as pd
import time
import json
import subprocess
import os
import signal
import threading
import queue
from datetime import datetime
import requests
import websocket

# Page configuration
st.set_page_config(
    page_title="ORB Trading System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to match wireframe design
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
    
    .connection-status {
        padding: 10px;
        border-radius: 6px;
        margin: 10px 0;
        text-align: center;
        font-weight: bold;
    }
    
    .connected {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .disconnected {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
</style>
""", unsafe_allow_html=True)

class ORBTradingBridge:
    """Bridge between Streamlit frontend and Node.js backend"""
    
    def __init__(self):
        self.backend_process = None
        self.backend_port = 3001
        self.backend_url = f"http://localhost:{self.backend_port}"
        self.is_connected = False
        
    def start_backend(self, api_key, api_secret, environment, risk_settings):
        """Start the Node.js backend trading system"""
        try:
            # Create config for backend
            config = {
                'apiKey': api_key,
                'apiSecret': api_secret,
                'environment': environment,
                'riskSettings': risk_settings
            }
            
            # Save config to file for backend to read
            with open('backend_config.json', 'w') as f:
                json.dump(config, f)
            
            # Start Node.js backend process
            cmd = ['node', 'trading_backend.js']
            self.backend_process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                env={**os.environ, 'CONFIG_FILE': 'backend_config.json'}
            )
            
            # Wait a moment for backend to start
            time.sleep(3)
            
            # Test connection
            self.is_connected = self.test_connection()
            return self.is_connected
            
        except Exception as e:
            st.error(f"Failed to start backend: {str(e)}")
            return False
    
    def stop_backend(self):
        """Stop the Node.js backend"""
        if self.backend_process:
            self.backend_process.terminate()
            self.backend_process = None
        self.is_connected = False
    
    def test_connection(self):
        """Test if backend is responding"""
        try:
            response = requests.get(f"{self.backend_url}/status", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def send_command(self, command, data=None):
        """Send command to backend"""
        try:
            if not self.is_connected:
                return {"error": "Backend not connected"}
                
            payload = {"command": command}
            if data:
                payload.update(data)
                
            response = requests.post(
                f"{self.backend_url}/command", 
                json=payload, 
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_system_status(self):
        """Get current system status from backend"""
        try:
            response = requests.get(f"{self.backend_url}/status", timeout=5)
            return response.json()
        except:
            return {
                "system_running": False,
                "trading_enabled": False,
                "current_price": 0,
                "positions": {},
                "market_open": False
            }

# Initialize session state
if 'bridge' not in st.session_state:
    st.session_state.bridge = ORBTradingBridge()

if 'backend_running' not in st.session_state:
    st.session_state.backend_running = False

if 'system_data' not in st.session_state:
    st.session_state.system_data = {
        "system_running": False,
        "trading_enabled": False,
        "current_price": 16234.50,
        "positions": {},
        "market_open": False,
        "vwap": 16231.25,
        "daily_pnl": 0,
        "total_trades": 0
    }

if 'risk_settings' not in st.session_state:
    st.session_state.risk_settings = {
        'risk_range': '$100 - $150 (Moderate)',
        'stop_loss': '1.0% (Standard)',
        'daily_limit': '$900 (Standard Account)',
        'total_limit': '$4,200 (Standard Account)'
    }

# Header Section
st.markdown("""
<div class="main-header">
    <h1>📈 ORB Trading System</h1>
    <h2>Live Trading Interface</h2>
</div>
""", unsafe_allow_html=True)

# Get system status from backend
system_status = st.session_state.bridge.get_system_status()
st.session_state.system_data.update(system_status)

# System Status Display
if st.session_state.system_data["system_running"]:
    if st.session_state.system_data["trading_enabled"]:
        status_text = "🟢 SYSTEM RUNNING & TRADING"
        status_class = "status-running"
    else:
        status_text = "🟡 SYSTEM RUNNING (PAUSED)"
        status_class = "status-paused"
else:
    status_text = "🔴 SYSTEM STOPPED"
    status_class = "status-stopped"

st.markdown(f'<div class="{status_class}" style="text-align: center; margin: 20px 0;">{status_text}</div>', unsafe_allow_html=True)

# Backend Connection Status
connection_class = "connected" if st.session_state.bridge.is_connected else "disconnected"
connection_text = "✅ Backend Connected" if st.session_state.bridge.is_connected else "❌ Backend Disconnected"
st.markdown(f'<div class="connection-status {connection_class}">{connection_text}</div>', unsafe_allow_html=True)

# Sidebar - Control Panel
with st.sidebar:
    st.markdown("### 🎛️ System Controls")
    
    # Backend control
    if not st.session_state.backend_running:
        if st.button("🚀 START BACKEND", use_container_width=True, type="primary"):
            # Get API settings first
            api_key = st.session_state.get('api_key', '')
            api_secret = st.session_state.get('api_secret', '')
            environment = st.session_state.get('environment', 'demo')
            
            if api_key and api_secret:
                if st.session_state.bridge.start_backend(api_key, api_secret, environment, st.session_state.risk_settings):
                    st.session_state.backend_running = True
                    st.success("✅ Backend Started!")
                    st.rerun()
                else:
                    st.error("❌ Failed to start backend")
            else:
                st.error("❌ Please enter API credentials first")
    else:
        if st.button("🛑 STOP BACKEND", use_container_width=True):
            st.session_state.bridge.stop_backend()
            st.session_state.backend_running = False
            st.success("✅ Backend Stopped")
            st.rerun()
    
    st.markdown("---")
    
    # Trading control buttons (only work if backend is connected)
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("▶️ START", use_container_width=True, type="primary", disabled=not st.session_state.bridge.is_connected):
            result = st.session_state.bridge.send_command("start")
            if "error" not in result:
                st.success("✅ Trading Started!")
            else:
                st.error(f"❌ {result['error']}")
            
        if st.button("⏸️ PAUSE", use_container_width=True, disabled=not st.session_state.bridge.is_connected):
            result = st.session_state.bridge.send_command("pause")
            if "error" not in result:
                st.warning("⏸️ Trading Paused")
            else:
                st.error(f"❌ {result['error']}")
    
    with col2:
        if st.button("🛑 STOP", use_container_width=True, disabled=not st.session_state.bridge.is_connected):
            result = st.session_state.bridge.send_command("stop")
            if "error" not in result:
                st.error("🛑 Trading Stopped")
            else:
                st.error(f"❌ {result['error']}")
            
        if st.button("▶️ RESUME", use_container_width=True, disabled=not st.session_state.bridge.is_connected):
            result = st.session_state.bridge.send_command("resume")
            if "error" not in result:
                st.success("▶️ Trading Resumed")
            else:
                st.error(f"❌ {result['error']}")
    
    # Emergency controls
    st.markdown("---")
    st.markdown("### 🚨 Emergency Controls")
    
    if st.button("🔴 CLOSE ALL POSITIONS", use_container_width=True, type="secondary", disabled=not st.session_state.bridge.is_connected):
        result = st.session_state.bridge.send_command("close_all")
        if "error" not in result:
            st.warning("🔴 All positions closed!")
        else:
            st.error(f"❌ {result['error']}")
    
    # Quick status
    st.markdown("---")
    st.markdown("### 📊 Quick Status")
    
    market_status = "🟢 OPEN" if st.session_state.system_data["market_open"] else "🔴 CLOSED"
    active_positions = len([p for p in st.session_state.system_data["positions"].values() if p])
    
    st.markdown(f"""
    **Market:** {market_status}  
    **Positions:** {active_positions} Active  
    **Last Price:** ${st.session_state.system_data["current_price"]:,.2f}  
    **Daily P&L:** ${st.session_state.system_data.get("daily_pnl", 0):,.2f}
    """)

# Main Content
# Current Price Display
st.markdown("## 📊 Current Price")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    price_change = "+$12.25 (+0.08%)"  # This would be calculated from real data
    st.markdown(f"""
    <div class="price-display">
        <h2>MNQ - Micro E-mini Nasdaq-100</h2>
        <div class="price-value">${st.session_state.system_data["current_price"]:,.2f}</div>
        <div style="font-size: 18px; color: #2ecc71;">▲ {price_change}</div>
        <div style="margin-top: 10px; color: #7f8c8d;">
            Last Updated: {datetime.now().strftime("%I:%M:%S %p")}
        </div>
        <div style="margin-top: 10px; color: #3498db;">
            VWAP: ${st.session_state.system_data.get("vwap", 0):,.2f}
        </div>
    </div>
    """, unsafe_allow_html=True)

# Strategy Status
st.markdown("## 🎯 Strategy Overview")

col1, col2, col3 = st.columns(3)

positions = st.session_state.system_data["positions"]
strategies = [
    {
        'name': 'Strategy 1',
        'title': 'Opening Candle',
        'status': 'ACTIVE' if positions.get('strategy1') else 'WAITING',
        'position': f"{positions['strategy1']['side'].upper()} {positions['strategy1']['quantity']}" if positions.get('strategy1') else "None"
    },
    {
        'name': 'Strategy 2', 
        'title': 'VWAP Following',
        'status': 'ACTIVE' if positions.get('strategy2') else 'WAITING',
        'position': f"{positions['strategy2']['side'].upper()} {positions['strategy2']['quantity']}" if positions.get('strategy2') else "None"
    },
    {
        'name': 'Strategy 3',
        'title': 'Bands Breakout', 
        'status': 'ACTIVE' if positions.get('strategy3') else 'WAITING',
        'position': f"{positions['strategy3']['side'].upper()} {positions['strategy3']['quantity']}" if positions.get('strategy3') else "None"
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
            <p>Status: {strategy['status']}</p>
            <p>Position: {strategy['position']}</p>
        </div>
        """, unsafe_allow_html=True)

# Open Positions
st.markdown("## 📋 Open Positions")

# Create positions data from backend
positions_data = []
total_pnl = 0

for strategy_name, position in positions.items():
    if position:
        # Calculate unrealized P&L (this would come from backend in real implementation)
        entry_price = position.get('entryPrice', 0)
        current_price = st.session_state.system_data["current_price"]
        quantity = position.get('quantity', 0)
        side = position.get('side', 'long')
        
        if side == 'long':
            pnl = (current_price - entry_price) * quantity * 2  # MNQ multiplier
        else:
            pnl = (entry_price - current_price) * quantity * 2
        
        positions_data.append({
            'Strategy': strategy_name.replace('strategy', 'Strategy '),
            'Direction': side.upper(),
            'Contracts': quantity,
            'Entry Price': f"${entry_price:,.2f}",
            'Current P&L': f"${pnl:,.2f}"
        })
        total_pnl += pnl

if positions_data:
    df_positions = pd.DataFrame(positions_data)
    
    # Display the table
    st.dataframe(df_positions, use_container_width=True, hide_index=True)
    
    # Individual close buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if positions.get('strategy1') and st.button("Close Strategy 1", use_container_width=True):
            result = st.session_state.bridge.send_command("close_position", {"strategy": "strategy1"})
            if "error" not in result:
                st.success("Strategy 1 position closed")
            else:
                st.error(f"Error: {result['error']}")
    
    with col2:
        if positions.get('strategy2') and st.button("Close Strategy 2", use_container_width=True):
            result = st.session_state.bridge.send_command("close_position", {"strategy": "strategy2"})
            if "error" not in result:
                st.success("Strategy 2 position closed")
            else:
                st.error(f"Error: {result['error']}")
    
    with col3:
        if positions.get('strategy3') and st.button("Close Strategy 3", use_container_width=True):
            result = st.session_state.bridge.send_command("close_position", {"strategy": "strategy3"})
            if "error" not in result:
                st.success("Strategy 3 position closed")
            else:
                st.error(f"Error: {result['error']}")
    
    # Total P&L
    pnl_color = "#2ecc71" if total_pnl >= 0 else "#e74c3c"
    pnl_sign = "+" if total_pnl >= 0 else ""
    st.markdown(f"""
    <div style="text-align: center; margin-top: 20px;">
        <span style="font-size: 20px; font-weight: bold; color: {pnl_color};">
            Total P&L: {pnl_sign}${total_pnl:.2f}
        </span>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("No open positions")

# Risk Parameters
st.markdown("## ⚠️ Risk Settings")

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
        st.session_state.risk_settings = {
            'risk_range': risk_range,
            'stop_loss': stop_loss,
            'daily_limit': daily_limit,
            'total_limit': total_limit
        }
        
        # Send to backend if connected
        if st.session_state.bridge.is_connected:
            result = st.session_state.bridge.send_command("update_risk", st.session_state.risk_settings)
            if "error" not in result:
                st.success("✅ Risk settings saved and updated in trading system!")
            else:
                st.error(f"❌ Failed to update backend: {result['error']}")
        else:
            st.success("✅ Risk settings saved locally!")

# Risk level guide
st.info("""
**⚠️ Risk Level Guide:**  
• **Conservative ($90-$100):** Safe for beginners and small accounts  
• **Moderate ($100-$150):** Balanced risk for most traders  
• **Aggressive ($150-$200):** Higher risk for experienced traders  

**Note:** System will randomly select risk amount within your chosen range for each trade.
""")

# API Connection Settings
st.markdown("## ⚙️ Connection Settings")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🔑 TradoVate API")
    
    api_key = st.text_input("API Key:", type="password", placeholder="Enter your API key", key="api_key")
    api_secret = st.text_input("API Secret:", type="password", placeholder="Enter your secret", key="api_secret")
    environment = st.selectbox("Environment:", ["demo", "live"], index=0, key="environment")
    
    # Store in session state
    st.session_state.api_key = api_key
    st.session_state.api_secret = api_secret
    st.session_state.environment = environment

with col2:
    st.markdown("### 📊 Trading Symbol")
    
    trading_symbol = st.selectbox(
        "Futures Contract:",
        ["MNQ (Micro E-mini Nasdaq-100)",
         "MES (Micro E-mini S&P 500)",
         "M2K (Micro E-mini Russell 2000)"],
        index=0
    )
    
    st.markdown("---")
    
    backend_status = "✅ Connected" if st.session_state.bridge.is_connected else "❌ Disconnected"
    market_status = "🟢 OPEN" if st.session_state.system_data["market_open"] else "🔴 CLOSED"
    
    st.markdown(f"""
    **Backend Status:** {backend_status}  
    **Market Status:** {market_status}  
    **Total Trades Today:** {st.session_state.system_data.get("total_trades", 0)}
    """)

# Auto-refresh for live updates when backend is connected
if st.session_state.bridge.is_connected:
    time.sleep(1)  # Refresh every second
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #7f8c8d; margin-top: 20px;">
    ORB Trading System - Live Trading Interface<br>
    <small>Backend: Node.js + TradoVate API | Frontend: Streamlit</small><br>
    <small>For educational purposes only. Trade at your own risk.</small>
</div>
""", unsafe_allow_html=True)