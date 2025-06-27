# ORB Trading System

## 📈 Multi-Strategy Opening Range Breakout Trading Interface

A simple, clean interface for controlling and monitoring Opening Range Breakout trading strategies on futures markets.

### ✨ Features

- **🎛️ System Controls** - Start, Stop, Pause, Resume trading
- **🚨 Emergency Controls** - Instant position closure
- **📊 Live Price Display** - Real-time market data
- **🎯 Strategy Monitoring** - Track 3 ORB strategies
- **📋 Position Management** - View and close individual positions
- **⚠️ Risk Management** - Configurable risk parameters
- **🔗 API Integration** - TradoVate connection setup

### 🚀 Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/orb-trading-system.git
   cd orb-trading-system
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   streamlit run app.py
   ```

4. **Open in browser:** http://localhost:8501

### 🔧 Configuration

#### Risk Parameters
- **Conservative:** $90-$100 per trade
- **Moderate:** $100-$150 per trade  
- **Aggressive:** $150-$200 per trade

#### Account Limits
- Small Account: $500 daily / $2,500 total
- Standard Account: $900 daily / $4,200 total
- Large Account: $1,500 daily / $7,500 total
- Professional: $2,500 daily / $12,500 total

### 🎯 Strategies

1. **Opening Candle Direction** - Trades based on first 5-minute candle direction
2. **VWAP Trend Following** - Continuous entries/exits using VWAP crossovers
3. **Concretum Bands Breakout** - Volatility-based noise range breakouts

### ⚠️ Disclaimer

This application is for educational purposes only. Trading futures involves substantial risk of loss and is not suitable for all investors. Past performance is not indicative of future results.

### 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

### 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### 📞 Support

For questions or issues, please open an issue on GitHub.

---

**Made with ❤️ and Streamlit**