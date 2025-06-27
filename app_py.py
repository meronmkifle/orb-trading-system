import streamlit as st
import pandas as pd
import time
import json
from datetime import datetime
import random

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
    
    .info-box {
        background: #e3f2fd;
        border: 1px solid #2196f3;
        border-radius: 8px;
        padding: 15px;
        margin: 15px 0;
        color: #1565c0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'system_running' not in st.session_state:
    st.session_state.system_running = False
if 'trading_enabled' not in st.session_state:
    st.session_state.trading_enabled = False
if 'current_price' not in st.session_state:
    st.session_state.current_price = 16234.50
if 'positions' not in st.session_state:
    st.session_state.positions = {
        'strategy1': {'side': 'LONG', 'quantity': 2, 'entry_price': 16230.25, 'pnl': 17.00},
        'strategy2': None,
        'strategy3': {'side': 'SHORT', 'quantity': 1, 'entry_price': 16240.00, 'pnl': 11.00}
    }
if 'risk_settings' not in st.session_state:
    st.session_state.risk_settings = {
        'risk_range': '$100 - $150 (Moderate)',
        'stop_loss': '1.0% (Standard)',
        'daily_limit': '$900 (Standard Account)',
        'total_limit': '$4,200 (Standard Account)'
    }
if 'last_update' not in st.session_state:
    st.session_state.last_update = time.time()
if 'api_connected' not in st.session_state:
    st.session_state.api_connected = False

# Header Section
st.markdown("""
<div class="main-header">
    <h1>📈 ORB Trading System</h1>
    <h2>Demo Trading Interface</h2>
</div>
""", unsafe_allow_html=True)

# Info about demo mode
st.markdown("""
<div class="info-box">
    <strong>ℹ️ Demo Mode:</strong> This is the frontend interface. To enable live trading, 
    you'll need to run the Node.js backend locally and integrate with TradoVate API.
    <br><br>
    <strong>📘 Setup Instructions:</strong> 
    <a href="https://github.com/meronmkifle/orb-trading-system" target="_blank">
        View GitHub Repository for Full Setup Guide
    </a>
</div>
""", unsafe_allow_html=True)

# System Status Display
if st.session_state.system_running:
    if st.session_state.trading_enabled:
        status_text = "🟢 SYSTEM RUNNING & TRADING (DEMO)"
        status_class = "status-running"
    else:
        status_text = "🟡 SYSTEM RUNNING (PAUSED) (DEMO)"
        status_class = "status-paused"
else:
    status_text = "🔴 SYSTEM STOPPED (DEMO)"
    status_class = "status-stopped"

st.markdown(f'<div class="{status_class}" style="text-align: center; margin: 20px 0;">{status_text}</div>', unsafe_allow_html=True)

# Sidebar - Control Panel
with st.sidebar:
    st.markdown("### 🎛️ System Controls")
    st.markdown("*Demo Mode - UI Only*")
    
    # Main control buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("▶️ START", use_container_width=True, type="primary"):
            st.session_state.system_running = True
            st.session_state.trading_enabled = True
            st.success("✅ Demo System Started!")
            
        if st.button("⏸️ PAUSE", use_container_width=True):
            if st.session_state.system_running:
                st.session_state.trading_enabled = False
                st.warning("⏸️ Demo Trading Paused")
            else:
                st.error("System must be running to pause")
    
    with col2:
        if st.button("🛑 STOP", use_container_width=True):
            st.session_state.system_running = False
            st.session_state.trading_enabled = False
            st.error("🛑 Demo System Stopped")
            
        if st.button("▶️ RESUME", use_container_width=True):
            if st.session_state.system_running:
                st.session_state.trading_enabled = True
                st.success("▶️ Demo Trading Resumed")
            else:
                st.error("System must be running to resume")
    
    # Emergency controls
    st.markdown("---")
    st.markdown("### 🚨 Emergency Controls")
    
    if st.button("🔴 CLOSE ALL POSITIONS", use_container_width=True, type="secondary"):
        # Clear all positions
        for key in st.session_state.positions:
            st.session_state.positions[key] = None
        st.warning("🔴 All demo positions closed!")
    
    # Quick status
    st.markdown("---")
    st.markdown("### 📊 Quick Status")
    
    market_status = "🟢 OPEN" if datetime.now().hour >= 9 and datetime.now().hour < 16 else "🔴 CLOSED"
    active_positions = sum(1 for pos in st.session_state.positions.values() if pos is not None)
    
    st.markdown(f"""
    **Market:** {market_status}  
    **Positions:** {active_positions} Active  
    **Last Price:** ${st.session_state.current_price:,.2f}
    """)

# Main Content
# Current Price Display
st.markdown("## 📊 Current Price")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown(f"""
    <div class="price-display">
        <h2>MNQ - Micro E-mini Nasdaq-100</h2>
        <div class="price-value">${st.session_state.current_price:,.2f}</div>
        <div style="font-size: 18px; color: #2ecc71;">▲ +$12.25 (+0.08%)</div>
        <div style="margin-top: 10px; color: #7f8c8d;">
            Last Updated: {datetime.now().strftime("%I:%M:%S %p")}
        </div>
        <div style="margin-top: 5px; font-size: 14px; color: #e74c3c;">
            📊 DEMO DATA - Not Live Market Prices
        </div>
    </div>
    """, unsafe_allow_html=True)

# Strategy Status
st.markdown("## 🎯 Strategy Overview")

col1, col2, col3 = st.columns(3)

strategies = [
    {
        'name': 'Strategy 1',
        'title': 'Opening Candle',
        'status': 'ACTIVE' if st.session_state.positions['strategy1'] else 'WAITING',
        'position': f"LONG 2" if st.session_state.positions['strategy1'] else "None"
    },
    {
        'name': 'Strategy 2', 
        'title': 'VWAP Following',
        'status': 'WAITING',
        'position': "None"
    },
    {
        'name': 'Strategy 3',
        'title': 'Bands Breakout', 
        'status': 'ACTIVE' if st.session_state.positions['strategy3'] else 'WAITING',
        'position': f"SHORT 1" if st.session_state.positions['strategy3'] else "None"
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

# Create positions data
positions_data = []
total_pnl = 0

for strategy, position in st.session_state.positions.items():
    if position:
        positions_data.append({
            'Strategy': strategy.replace('strategy', 'Strategy '),
            'Direction': position['side'],
            'Contracts': position['quantity'],
            'Entry Price': f"${position['entry_price']:,.2f}",
            'Current P&L': f"${position['pnl']:,.2f}"
        })
        total_pnl += position['pnl']

if positions_data:
    df_positions = pd.DataFrame(positions_data)
    
    # Display the table
    st.dataframe(df_positions, use_container_width=True, hide_index=True)
    
    # Individual close buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.session_state.positions['strategy1'] and st.button("Close Strategy 1", use_container_width=True):
            st.session_state.positions['strategy1'] = None
            st.success("Strategy 1 demo position closed")
    
    with col2:
        if st.session_state.positions['strategy2'] and st.button("Close Strategy 2", use_container_width=True):
            st.session_state.positions['strategy2'] = None
            st.success("Strategy 2 demo position closed")
    
    with col3:
        if st.session_state.positions['strategy3'] and st.button("Close Strategy 3", use_container_width=True):
            st.session_state.positions['strategy3'] = None
            st.success("Strategy 3 demo position closed")
    
    # Total P&L
    st.markdown(f"""
    <div style="text-align: center; margin-top: 20px;">
        <span style="font-size: 20px; font-weight: bold; color: #2ecc71;">
            Total P&L: +${total_pnl:.2f} (DEMO)
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
        st.success("✅ Risk settings saved! (Demo Mode)")

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
    
    api_key = st.text_input("API Key:", type="password", placeholder="Demo mode - not required", disabled=True)
    api_secret = st.text_input("API Secret:", type="password", placeholder="Demo mode - not required", disabled=True)
    environment = st.selectbox("Environment:", ["demo", "live"], index=0, disabled=True)
    
    st.info("💡 **For Live Trading:** Download the full system from GitHub and run locally with Node.js backend")

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
    
    st.markdown(f"""
    **Connection Status:** 🟡 Demo Mode  
    **Market Status:** 🟢 OPEN (Simulated)  
    **Backend Status:** ❌ Not Connected (Frontend Only)
    """)

# Live Trading Setup Instructions
st.markdown("## 🚀 Enable Live Trading")

st.markdown("""
### To enable actual trading with your ORB strategies:

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/meronmkifle/orb-trading-system.git
   cd orb-trading-system
   ```

2. **Install Dependencies:**
   ```bash
   # Node.js backend
   npm install
   
   # Python frontend
   pip install -r requirements.txt
   ```

3. **Run Both Systems:**
   ```bash
   # Terminal 1: Start backend
   node trading_backend.js
   
   # Terminal 2: Start frontend
   streamlit run app.py
   ```

4. **Configure API:**
   - Enter your TradoVate API credentials
   - Select demo or live environment
   - Configure risk parameters

5. **Start Trading:**
   - Click "START BACKEND" to connect
   - Use the same interface with live data
   - All strategies will trade automatically
""")

# Simulate price updates when system is running
if st.session_state.system_running:
    current_time = time.time()
    if current_time - st.session_state.last_update > 3:  # Update every 3 seconds
        # Simulate small price movements
        price_change = random.uniform(-10, 10)
        st.session_state.current_price += price_change
        st.session_state.current_price = max(15000, min(18000, st.session_state.current_price))
        st.session_state.last_update = current_time
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #7f8c8d; margin-top: 20px;">
    ORB Trading System - Demo Interface<br>
    <small>For live trading, run the full system locally with Node.js backend</small><br>
    <small>Visit: <a href="https://github.com/meronmkifle/orb-trading-system" target="_blank">GitHub Repository</a></small><br>
    <small>For educational purposes only. Trade at your own risk.</small>
</div>
""", unsafe_allow_html=True)
