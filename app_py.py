import streamlit as st
import pandas as pd
import time
from datetime import datetime

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
    /* Main styling */
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
    
    .emergency-section {
        background: #ffe6e6;
        border: 2px solid #ff6b6b;
        border-radius: 8px;
        padding: 15px;
        margin: 20px 0;
    }
    
    .quick-status {
        background: white;
        padding: 15px;
        border-radius: 8px;
        margin-top: 20px;
        color: #2c3e50;
    }
    
    /* Sidebar styling */
    .sidebar .element-container {
        margin-bottom: 10px;
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
if 'api_connected' not in st.session_state:
    st.session_state.api_connected = True

# Header Section
st.markdown("""
<div class="main-header">
    <h1>📈 ORB Trading System</h1>
    <h2>Simple Control Interface</h2>
</div>
""", unsafe_allow_html=True)

# System Status Display
if st.session_state.system_running:
    if st.session_state.trading_enabled:
        status_text = "🟢 SYSTEM RUNNING & TRADING"
        status_class = "status-running"
    else:
        status_text = "🟡 SYSTEM RUNNING (PAUSED)"
        status_class = "status-paused"
else:
    status_text = "🔴 SYSTEM STOPPED"
    status_class = "status-stopped"

st.markdown(f'<div class="{status_class}" style="text-align: center; margin: 20px 0;">{status_text}</div>', unsafe_allow_html=True)

# Sidebar - Control Panel
with st.sidebar:
    st.markdown("### 🎛️ System Controls")
    
    # Main control buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("▶️ START", use_container_width=True, type="primary"):
            st.session_state.system_running = True
            st.session_state.trading_enabled = True
            st.success("✅ System Started!")
            
        if st.button("⏸️ PAUSE", use_container_width=True):
            if st.session_state.system_running:
                st.session_state.trading_enabled = False
                st.warning("⏸️ Trading Paused")
            else:
                st.error("System must be running to pause")
    
    with col2:
        if st.button("🛑 STOP", use_container_width=True):
            st.session_state.system_running = False
            st.session_state.trading_enabled = False
            st.error("🛑 System Stopped")
            
        if st.button("▶️ RESUME", use_container_width=True):
            if st.session_state.system_running:
                st.session_state.trading_enabled = True
                st.success("▶️ Trading Resumed")
            else:
                st.error("System must be running to resume")
    
    # Emergency controls
    st.markdown("---")
    st.markdown("### 🚨 Emergency Controls")
    
    if st.button("🔴 CLOSE ALL POSITIONS", use_container_width=True, type="secondary"):
        # Clear all positions
        for key in st.session_state.positions:
            st.session_state.positions[key] = None
        st.warning("🔴 All positions closed!")
    
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
    
    # Style the dataframe
    def style_pnl(val):
        if '+' in val:
            return 'color: #2ecc71; font-weight: bold'
        elif '-' in val:
            return 'color: #e74c3c; font-weight: bold'
        return ''
    
    def style_direction(val):
        if val == 'LONG':
            return 'color: #2ecc71; font-weight: bold'
        elif val == 'SHORT':
            return 'color: #e74c3c; font-weight: bold'
        return ''
    
    styled_df = df_positions.style.applymap(style_pnl, subset=['Current P&L'])
    styled_df = styled_df.applymap(style_direction, subset=['Direction'])
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    # Individual close buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.session_state.positions['strategy1'] and st.button("Close Strategy 1", use_container_width=True):
            st.session_state.positions['strategy1'] = None
            st.success("Strategy 1 position closed")
    
    with col2:
        if st.session_state.positions['strategy2'] and st.button("Close Strategy 2", use_container_width=True):
            st.session_state.positions['strategy2'] = None
            st.success("Strategy 2 position closed")
    
    with col3:
        if st.session_state.positions['strategy3'] and st.button("Close Strategy 3", use_container_width=True):
            st.session_state.positions['strategy3'] = None
            st.success("Strategy 3 position closed")
    
    # Total P&L
    st.markdown(f"""
    <div style="text-align: center; margin-top: 20px;">
        <span style="font-size: 20px; font-weight: bold; color: #2ecc71;">
            Total P&L: +${total_pnl:.2f}
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
        st.success("✅ Risk settings saved!")

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
    
    api_key = st.text_input("API Key:", type="password", placeholder="Enter your API key")
    api_secret = st.text_input("API Secret:", type="password", placeholder="Enter your secret")
    environment = st.selectbox("Environment:", ["Demo", "Live"], index=0)
    
    if st.button("🔗 Connect", use_container_width=True, type="primary"):
        if api_key and api_secret:
            st.session_state.api_connected = True
            st.success("✅ Connected to TradoVate")
        else:
            st.error("❌ Please enter API credentials")

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
    
    connection_status = "✅ Connected" if st.session_state.api_connected else "❌ Disconnected"
    market_status = "🟢 OPEN" if datetime.now().hour >= 9 and datetime.now().hour < 16 else "🔴 CLOSED"
    
    st.markdown(f"""
    **Connection Status:** {connection_status}  
    **Market Status:** {market_status}
    """)

# Auto-refresh for live updates
if st.session_state.system_running:
    # Simulate price updates
    if 'last_update' not in st.session_state:
        st.session_state.last_update = time.time()
    
    current_time = time.time()
    if current_time - st.session_state.last_update > 2:  # Update every 2 seconds
        # Simulate small price movements
        import random
        price_change = random.uniform(-5, 5)
        st.session_state.current_price += price_change
        st.session_state.last_update = current_time
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #7f8c8d; margin-top: 20px;">
    ORB Trading System - Simple Control Interface<br>
    <small>For educational purposes only. Trade at your own risk.</small>
</div>
""", unsafe_allow_html=True)