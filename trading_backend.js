// trading_backend.js - Bridge between Streamlit and ORB Trading System
const express = require('express');
const cors = require('cors');
const fs = require('fs');

// Import your existing ORB trading system
// (We'll need to modify the class slightly to work as a module)
class ORBTradingSystem {
    constructor(config) {
        this.config = {
            accountSize: 150000,
            maxDailyLoss: 900,
            maxOverallLoss: 4200,
            maxRiskPerTrade: 100,
            symbol: 'MNQ',
            tickSize: 0.25,
            tickValue: 0.50,
            contractMultiplier: 2,
            ...config
        };
        
        this.api = null;
        this.ws = null;
        this.currentPrice = 16234.50; // Start with a default price
        this.isRunning = false;
        this.tradingEnabled = false;
        
        this.sessionData = {
            openPrice: 0,
            vwap: 16231.25,
            volume: 0,
            priceVolume: 0,
            upperBand: 0,
            lowerBand: 0,
            ma350: [],
            ma300: [],
            ma400: [],
            dailyPnL: 0,
            totalTrades: 0
        };
        
        this.positions = {
            strategy1: null,
            strategy2: null,
            strategy3: null
        };
        
        this.marketHours = {
            start: { hour: 9, minute: 30 },
            end: { hour: 16, minute: 0 }
        };
        
        this.candleData = {
            m1: [],
            m5: [],
            m15: []
        };
        
        this.historicalMoves = [];
        
        // Start price simulation
        this.startPriceSimulation();
    }

    // Simplified initialization for demo/testing
    async initialize(apiKey, apiSecret, environment) {
        try {
            console.log(`Initializing ORB System in ${environment} mode...`);
            
            // For demo purposes, we'll simulate the connection
            if (environment === 'demo') {
                this.api = { connected: true }; // Mock API
                console.log('✅ Connected to TradoVate API (Demo Mode)');
                return true;
            } else {
                // Real API connection would go here
                // this.api = new TradoVateAPI({ apiKey, apiSecret, environment: 'live' });
                // await this.api.connect();
                console.log('🔄 Live trading not implemented yet - using demo mode');
                this.api = { connected: true };
                return true;
            }
        } catch (error) {
            console.error('❌ Initialization error:', error);
            return false;
        }
    }

    // Simulate price movements for demo
    startPriceSimulation() {
        setInterval(() => {
            if (this.isRunning) {
                // Simulate realistic price movements
                const change = (Math.random() - 0.5) * 10; // -5 to +5 points
                this.currentPrice += change;
                this.currentPrice = Math.max(15000, Math.min(18000, this.currentPrice)); // Keep in realistic range
                
                // Update VWAP slightly
                this.sessionData.vwap += (Math.random() - 0.5) * 2;
                
                // Simulate occasional position changes
                if (Math.random() < 0.01) { // 1% chance per tick
                    this.simulateRandomTrade();
                }
            }
        }, 1000); // Update every second
    }

    simulateRandomTrade() {
        const strategies = ['strategy1', 'strategy2', 'strategy3'];
        const randomStrategy = strategies[Math.floor(Math.random() * strategies.length)];
        
        if (!this.positions[randomStrategy] && Math.random() < 0.5) {
            // Enter a position
            this.positions[randomStrategy] = {
                side: Math.random() < 0.5 ? 'long' : 'short',
                quantity: Math.floor(Math.random() * 3) + 1, // 1-3 contracts
                entryPrice: this.currentPrice,
                timestamp: new Date(),
                stopLoss: this.currentPrice * (Math.random() < 0.5 ? 0.99 : 1.01)
            };
            console.log(`📊 Simulated ${randomStrategy} position: ${this.positions[randomStrategy].side} ${this.positions[randomStrategy].quantity}`);
        } else if (this.positions[randomStrategy] && Math.random() < 0.3) {
            // Close a position
            console.log(`🔄 Simulated close ${randomStrategy}`);
            this.positions[randomStrategy] = null;
        }
    }

    // System control methods
    startSystem() {
        this.isRunning = true;
        this.tradingEnabled = true;
        console.log('✅ Trading system STARTED');
        return { success: true, message: 'System started' };
    }

    stopSystem() {
        this.isRunning = false;
        this.tradingEnabled = false;
        console.log('🛑 Trading system STOPPED');
        return { success: true, message: 'System stopped' };
    }

    pauseTrading() {
        this.tradingEnabled = false;
        console.log('⏸️ Trading PAUSED');
        return { success: true, message: 'Trading paused' };
    }

    resumeTrading() {
        if (this.isRunning) {
            this.tradingEnabled = true;
            console.log('▶️ Trading RESUMED');
            return { success: true, message: 'Trading resumed' };
        } else {
            return { success: false, message: 'System must be running to resume' };
        }
    }

    closeAllPositions() {
        let closedCount = 0;
        for (const strategy in this.positions) {
            if (this.positions[strategy]) {
                this.positions[strategy] = null;
                closedCount++;
            }
        }
        console.log(`🔴 Closed ${closedCount} positions`);
        return { success: true, message: `Closed ${closedCount} positions` };
    }

    closePosition(strategy) {
        if (this.positions[strategy]) {
            this.positions[strategy] = null;
            console.log(`🔄 Closed ${strategy} position`);
            return { success: true, message: `${strategy} position closed` };
        } else {
            return { success: false, message: `No ${strategy} position to close` };
        }
    }

    isMarketOpen() {
        const now = new Date();
        const hour = now.getHours();
        const minute = now.getMinutes();
        const currentMinutes = hour * 60 + minute;
        
        const startMinutes = this.marketHours.start.hour * 60 + this.marketHours.start.minute;
        const endMinutes = this.marketHours.end.hour * 60 + this.marketHours.end.minute;
        
        return currentMinutes >= startMinutes && currentMinutes <= endMinutes;
    }

    getSystemStatus() {
        return {
            system_running: this.isRunning,
            trading_enabled: this.tradingEnabled,
            current_price: this.currentPrice,
            positions: this.positions,
            market_open: this.isMarketOpen(),
            vwap: this.sessionData.vwap,
            daily_pnl: this.sessionData.dailyPnL,
            total_trades: this.sessionData.totalTrades,
            timestamp: new Date().toISOString()
        };
    }

    updateRiskSettings(settings) {
        console.log('📊 Risk settings updated:', settings);
        // In a real implementation, this would update the trading parameters
        return { success: true, message: 'Risk settings updated' };
    }
}

// Express server setup
const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

// Initialize trading system
let tradingSystem = null;

// Initialize trading system with config
app.post('/initialize', async (req, res) => {
    try {
        const { apiKey, apiSecret, environment, riskSettings } = req.body;
        
        tradingSystem = new ORBTradingSystem();
        const success = await tradingSystem.initialize(apiKey, apiSecret, environment);
        
        if (success) {
            res.json({ success: true, message: 'Trading system initialized' });
        } else {
            res.status(500).json({ success: false, message: 'Failed to initialize' });
        }
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

// Get system status
app.get('/status', (req, res) => {
    if (tradingSystem) {
        res.json(tradingSystem.getSystemStatus());
    } else {
        res.json({
            system_running: false,
            trading_enabled: false,
            current_price: 16234.50,
            positions: {},
            market_open: false,
            vwap: 16231.25,
            daily_pnl: 0,
            total_trades: 0
        });
    }
});

// Handle commands from frontend
app.post('/command', (req, res) => {
    if (!tradingSystem) {
        return res.status(400).json({ error: 'Trading system not initialized' });
    }

    const { command, strategy } = req.body;
    let result;

    try {
        switch (command) {
            case 'start':
                result = tradingSystem.startSystem();
                break;
            case 'stop':
                result = tradingSystem.stopSystem();
                break;
            case 'pause':
                result = tradingSystem.pauseTrading();
                break;
            case 'resume':
                result = tradingSystem.resumeTrading();
                break;
            case 'close_all':
                result = tradingSystem.closeAllPositions();
                break;
            case 'close_position':
                result = tradingSystem.closePosition(strategy);
                break;
            case 'update_risk':
                result = tradingSystem.updateRiskSettings(req.body);
                break;
            default:
                result = { success: false, message: `Unknown command: ${command}` };
        }

        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// Start server
app.listen(PORT, () => {
    console.log(`🚀 ORB Trading Backend running on port ${PORT}`);
    console.log(`📊 Health check: http://localhost:${PORT}/health`);
    console.log(`📈 Status endpoint: http://localhost:${PORT}/status`);
    
    // Auto-initialize with demo settings if config file exists
    if (process.env.CONFIG_FILE && require('fs').existsSync(process.env.CONFIG_FILE)) {
        const config = JSON.parse(require('fs').readFileSync(process.env.CONFIG_FILE, 'utf8'));
        tradingSystem = new ORBTradingSystem();
        tradingSystem.initialize(config.apiKey, config.apiSecret, config.environment)
            .then(() => {
                console.log('✅ Auto-initialized with config file');
            })
            .catch(err => {
                console.error('❌ Auto-initialization failed:', err);
            });
    }
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\n👋 Shutting down ORB Trading Backend...');
    if (tradingSystem) {
        tradingSystem.closeAllPositions();
    }
    process.exit(0);
});

module.exports = { ORBTradingSystem, app };