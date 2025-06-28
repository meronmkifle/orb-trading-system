import logging
from datetime import datetime, time
from typing import Dict, Tuple, Optional, List
import traceback

class TradingStrategyConfig:
    """Configuration parameters for trading strategies"""
    def __init__(self):
        # Time windows (in minutes)
        self.MARKET_OPEN_WINDOW = 5  # Minutes after open to allow entry
        self.MARKET_CLOSE_WINDOW = 10  # Minutes before close to start exiting
        
        # Risk parameters
        self.STRATEGY_RISK_MULTIPLIERS = {
            'strategy1': 2.0,
            'strategy2': 2.0,
            'strategy3': 4.0
        }
        
        # Position limits
        self.MAX_POSITIONS_PER_STRATEGY = 1
        self.MAX_TOTAL_POSITIONS = 3
        self.MAX_CAPITAL_PER_STRATEGY = 0.3  # 30% of total capital per strategy
        
        # Timing parameters
        self.STRATEGY1_ENTRY_START = time(9, 35)  # 5 min after open
        self.STRATEGY1_ENTRY_END = time(9, 40)    # 10 min window
        
        # Data validation
        self.MIN_MA_PERIODS = {
            'strategy1': 350,
            'strategy2': 300,
            'strategy3': 400
        }
        
        # Retry parameters
        self.MAX_ORDER_RETRIES = 3
        self.RETRY_DELAY_SECONDS = 2

class ImprovedTradingStrategy:
    def __init__(self, config: TradingStrategyConfig = None):
        self.config = config or TradingStrategyConfig()
        self.setup_logging()
        self.position_tracker = PositionTracker()
        
    def setup_logging(self):
        """Set up comprehensive logging system"""
        self.logger = logging.getLogger('TradingStrategy')
        self.logger.setLevel(logging.INFO)
        
        # File handler for all logs
        fh = logging.FileHandler(f'trading_{datetime.now().strftime("%Y%m%d")}.log')
        fh.setLevel(logging.DEBUG)
        
        # Console handler for important logs
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        
        # Separate trade logger
        self.trade_logger = logging.getLogger('TradeExecution')
        trade_fh = logging.FileHandler(f'trades_{datetime.now().strftime("%Y%m%d")}.log')
        trade_fh.setFormatter(formatter)
        self.trade_logger.addHandler(trade_fh)

    def check_strategies(self):
        """Check all trading strategies with robust error handling"""
        try:
            self.logger.info("Starting strategy check cycle")
            
            # Update positions with error handling
            if not self.safe_sync_positions():
                self.logger.error("Failed to sync positions, skipping cycle")
                return
            
            # Update candle data with validation
            if not self.safe_update_candle_data():
                self.logger.error("Failed to update candle data, skipping cycle")
                return
            
            # Validate market hours
            if not self.is_market_hours():
                self.logger.debug("Outside market hours, skipping strategies")
                return
            
            # Execute strategies with error isolation
            strategies = [
                ('strategy1', self.execute_strategy1_improved),
                ('strategy2', self.execute_strategy2_improved),
                ('strategy3', self.execute_strategy3_improved)
            ]
            
            for strategy_name, strategy_func in strategies:
                try:
                    strategy_func()
                except Exception as e:
                    self.logger.error(f"Error in {strategy_name}: {str(e)}")
                    self.logger.debug(traceback.format_exc())
                    
        except Exception as e:
            self.logger.critical(f"Critical error in check_strategies: {str(e)}")
            self.logger.debug(traceback.format_exc())

    def safe_sync_positions(self) -> bool:
        """Safely sync positions with error handling"""
        try:
            self.sync_positions()
            return True
        except Exception as e:
            self.logger.error(f"Position sync failed: {str(e)}")
            return False

    def safe_update_candle_data(self) -> bool:
        """Update candle data with validation"""
        try:
            self.update_candle_data()
            
            # Validate data integrity
            if not self.validate_candle_data():
                self.logger.error("Candle data validation failed")
                return False
                
            return True
        except Exception as e:
            self.logger.error(f"Candle data update failed: {str(e)}")
            return False

    def validate_candle_data(self) -> bool:
        """Validate candle data integrity"""
        validations = []
        
        # Check 5m candles
        if hasattr(self, 'candles_5m'):
            if len(self.candles_5m) > 0:
                latest = self.candles_5m[-1]
                validations.append(
                    latest['high'] >= latest['low'] and
                    latest['close'] > 0 and
                    latest['volume'] >= 0
                )
        
        # Check moving averages
        for ma_name, min_periods in [
            ('ma350', 350), ('ma300', 300), ('ma400', 400)
        ]:
            if hasattr(self, ma_name):
                ma_data = getattr(self, ma_name)
                validations.append(
                    len(ma_data) >= min_periods and
                    all(v > 0 for v in ma_data[-10:])  # Check last 10 values
                )
        
        # Check VWAP
        if hasattr(self, 'vwap'):
            validations.append(self.vwap > 0)
        
        return all(validations) if validations else False

    def is_market_hours(self) -> bool:
        """Check if current time is within market hours"""
        now = datetime.now()
        market_open = time(9, 30)
        market_close = time(16, 0)
        current_time = now.time()
        
        return market_open <= current_time <= market_close

    def is_near_market_close(self) -> bool:
        """Check if we're within the market close window"""
        now = datetime.now()
        minutes_to_close = (16 * 60) - (now.hour * 60 + now.minute)
        return 0 <= minutes_to_close <= self.config.MARKET_CLOSE_WINDOW

    def execute_strategy1_improved(self):
        """Strategy 1: Opening Candle Direction with improvements"""
        strategy_id = 'strategy1'
        
        try:
            # Pre-execution checks
            if not self.pre_execution_checks(strategy_id):
                return
            
            # Check if we need to exit positions near market close
            if self.is_near_market_close():
                if self.strategy_positions.get(strategy_id):
                    self.logger.info(f"{strategy_id}: Closing position near market close")
                    self.safe_close_position(strategy_id)
                return
            
            # Validate data requirements
            if not self.validate_strategy_data(strategy_id):
                return
            
            # Check if we're within the entry window
            now = datetime.now()
            if not self.is_in_time_window(
                now.time(),
                self.config.STRATEGY1_ENTRY_START,
                self.config.STRATEGY1_ENTRY_END
            ):
                # Check for fallback entry if we missed the primary window
                if not self.check_fallback_entry(strategy_id):
                    return
            
            # Get validated candle data
            opening_candle = self.candles_5m[-1]
            ma350_value = self.calculate_ma_safely(self.ma350)
            
            if ma350_value is None:
                self.logger.error(f"{strategy_id}: Failed to calculate MA350")
                return
            
            # Entry logic with position tracking
            current_position = self.strategy_positions.get(strategy_id)
            
            if not current_position:
                # Check for bullish setup
                if (self.is_bullish_candle(opening_candle) and 
                    opening_candle['close'] > ma350_value):
                    
                    self.logger.info(f"{strategy_id}: Bullish setup detected")
                    self.execute_entry(strategy_id, 'Buy', opening_candle)
                    
                # Check for bearish setup
                elif (self.is_bearish_candle(opening_candle) and 
                      opening_candle['close'] < ma350_value):
                    
                    self.logger.info(f"{strategy_id}: Bearish setup detected")
                    self.execute_entry(strategy_id, 'Sell', opening_candle)
                    
        except Exception as e:
            self.logger.error(f"{strategy_id} execution error: {str(e)}")
            self.logger.debug(traceback.format_exc())

    def execute_strategy2_improved(self):
        """Strategy 2: VWAP Trend Following with improvements"""
        strategy_id = 'strategy2'
        
        try:
            # Pre-execution checks
            if not self.pre_execution_checks(strategy_id):
                return
            
            # Market close exit
            if self.is_near_market_close():
                if self.strategy_positions.get(strategy_id):
                    self.logger.info(f"{strategy_id}: Closing position near market close")
                    self.safe_close_position(strategy_id)
                return
            
            # Validate data
            if not self.validate_strategy_data(strategy_id):
                return
            
            current_candle = self.candles_15m[-1]
            ma300_value = self.calculate_ma_safely(self.ma300)
            
            if ma300_value is None or not hasattr(self, 'vwap') or self.vwap <= 0:
                self.logger.error(f"{strategy_id}: Invalid MA300 or VWAP data")
                return
            
            # Check existing position for trailing stop
            current_position = self.strategy_positions.get(strategy_id)
            if current_position:
                if self.check_vwap_trailing_stop(strategy_id, current_position, current_candle):
                    return
            
            # Entry logic
            if not current_position:
                # Long condition
                if (current_candle['close'] > self.vwap and 
                    current_candle['close'] > ma300_value):
                    
                    self.logger.info(f"{strategy_id}: Long setup detected")
                    self.execute_entry(strategy_id, 'Buy', current_candle)
                    
                # Short condition
                elif (current_candle['close'] < self.vwap and 
                      current_candle['close'] < ma300_value):
                    
                    self.logger.info(f"{strategy_id}: Short setup detected")
                    self.execute_entry(strategy_id, 'Sell', current_candle)
                    
        except Exception as e:
            self.logger.error(f"{strategy_id} execution error: {str(e)}")
            self.logger.debug(traceback.format_exc())

    def execute_strategy3_improved(self):
        """Strategy 3: Concretum Bands Breakout with improvements"""
        strategy_id = 'strategy3'
        
        try:
            # Pre-execution checks
            if not self.pre_execution_checks(strategy_id):
                return
            
            # Market close exit
            if self.is_near_market_close():
                if self.strategy_positions.get(strategy_id):
                    self.logger.info(f"{strategy_id}: Closing position near market close")
                    self.safe_close_position(strategy_id)
                return
            
            # Validate data
            if not self.validate_strategy_data(strategy_id):
                return
            
            if len(self.candles_1m) < 2:
                return
            
            current_candle = self.candles_1m[-1]
            previous_candle = self.candles_1m[-2]
            ma400_value = self.calculate_ma_safely(self.ma400)
            
            if ma400_value is None:
                self.logger.error(f"{strategy_id}: Invalid MA400 data")
                return
            
            # Calculate bands with error handling
            bands = self.calculate_concretum_bands_safely()
            if not bands:
                return
            
            upper_band, lower_band = bands
            
            # Check existing position
            current_position = self.strategy_positions.get(strategy_id)
            if current_position:
                if self.check_vwap_trailing_stop(strategy_id, current_position, current_candle):
                    return
            
            # Entry logic
            if not current_position:
                # Long breakout
                if (previous_candle['open'] < upper_band and 
                    current_candle['close'] > upper_band and
                    current_candle['close'] > ma400_value):
                    
                    self.logger.info(f"{strategy_id}: Long breakout detected")
                    self.execute_entry(strategy_id, 'Buy', current_candle)
                    
                # Short breakout
                elif (previous_candle['open'] > lower_band and 
                      current_candle['close'] < lower_band and
                      current_candle['close'] < ma400_value):
                    
                    self.logger.info(f"{strategy_id}: Short breakout detected")
                    self.execute_entry(strategy_id, 'Sell', current_candle)
                    
        except Exception as e:
            self.logger.error(f"{strategy_id} execution error: {str(e)}")
            self.logger.debug(traceback.format_exc())

    def pre_execution_checks(self, strategy_id: str) -> bool:
        """Perform pre-execution checks for a strategy"""
        # Check if strategy can trade
        if not self.can_trade(strategy_id):
            return False
        
        # Check daily risk limits
        risk_ok, risk_msg = self.check_daily_risk_limits()
        if not risk_ok:
            self.logger.warning(f"{strategy_id}: {risk_msg}")
            return False
        
        # Check position limits
        if not self.position_tracker.can_open_position(strategy_id):
            self.logger.debug(f"{strategy_id}: Position limit reached")
            return False
        
        return True

    def validate_strategy_data(self, strategy_id: str) -> bool:
        """Validate required data for a strategy"""
        min_periods = self.config.MIN_MA_PERIODS.get(strategy_id, 0)
        
        if strategy_id == 'strategy1':
            return (hasattr(self, 'ma350') and 
                   len(self.ma350) >= min_periods and
                   hasattr(self, 'candles_5m') and 
                   len(self.candles_5m) >= 2)
        
        elif strategy_id == 'strategy2':
            return (hasattr(self, 'ma300') and 
                   len(self.ma300) >= min_periods and
                   hasattr(self, 'candles_15m') and 
                   len(self.candles_15m) >= 1)
        
        elif strategy_id == 'strategy3':
            return (hasattr(self, 'ma400') and 
                   len(self.ma400) >= min_periods and
                   hasattr(self, 'candles_1m') and 
                   len(self.candles_1m) >= 2)
        
        return False

    def execute_entry(self, strategy_id: str, action: str, candle: dict):
        """Execute entry with proper position tracking and error handling"""
        try:
            # Calculate position size
            risk_multiplier = self.config.STRATEGY_RISK_MULTIPLIERS.get(strategy_id, 2.0)
            position_size = self.calculate_position_size_safe(risk_multiplier)
            
            if position_size <= 0:
                self.logger.error(f"{strategy_id}: Invalid position size calculated")
                return
            
            # Check capital allocation
            if not self.position_tracker.check_capital_allocation(strategy_id, position_size):
                self.logger.warning(f"{strategy_id}: Capital allocation limit reached")
                return
            
            # Place order with retries
            success = self.place_order_with_retry(strategy_id, action, position_size)
            
            if success:
                self.trade_logger.info(
                    f"ENTRY|{strategy_id}|{action}|{position_size}|"
                    f"Price:{candle['close']}|Time:{datetime.now()}"
                )
                self.position_tracker.record_entry(strategy_id, action, position_size, candle['close'])
            
        except Exception as e:
            self.logger.error(f"Entry execution error for {strategy_id}: {str(e)}")

    def place_order_with_retry(self, strategy_id: str, action: str, size: float) -> bool:
        """Place order with retry logic"""
        for attempt in range(self.config.MAX_ORDER_RETRIES):
            try:
                self.place_strategy_order(strategy_id, action, size)
                return True
            except Exception as e:
                self.logger.warning(
                    f"Order attempt {attempt + 1} failed for {strategy_id}: {str(e)}"
                )
                if attempt < self.config.MAX_ORDER_RETRIES - 1:
                    import time
                    time.sleep(self.config.RETRY_DELAY_SECONDS)
        
        self.logger.error(f"Failed to place order for {strategy_id} after {self.config.MAX_ORDER_RETRIES} attempts")
        return False

    def safe_close_position(self, strategy_id: str) -> bool:
        """Safely close position with error handling"""
        try:
            self.close_strategy_position(strategy_id)
            self.trade_logger.info(
                f"EXIT|{strategy_id}|Time:{datetime.now()}"
            )
            self.position_tracker.record_exit(strategy_id)
            return True
        except Exception as e:
            self.logger.error(f"Failed to close position for {strategy_id}: {str(e)}")
            return False

    def check_vwap_trailing_stop(self, strategy_id: str, position: dict, candle: dict) -> bool:
        """Check VWAP trailing stop condition"""
        if ((position['action'] == 'Buy' and candle['close'] < self.vwap) or
            (position['action'] == 'Sell' and candle['close'] > self.vwap)):
            
            self.logger.info(f"{strategy_id}: VWAP trailing stop triggered")
            self.safe_close_position(strategy_id)
            return True
        return False

    def calculate_ma_safely(self, ma_data: List[float]) -> Optional[float]:
        """Safely calculate moving average"""
        try:
            if ma_data and len(ma_data) > 0:
                return sum(ma_data) / len(ma_data)
        except Exception as e:
            self.logger.error(f"MA calculation error: {str(e)}")
        return None

    def calculate_concretum_bands_safely(self) -> Optional[Tuple[float, float]]:
        """Safely calculate Concretum bands"""
        try:
            session_open = self.get_session_open_price()
            volatility = self.calculate_volatility_factor()
            
            if session_open > 0 and volatility > 0:
                upper = session_open * (1 + volatility)
                lower = session_open * (1 - volatility)
                return (upper, lower)
                
        except Exception as e:
            self.logger.error(f"Band calculation error: {str(e)}")
        return None

    def calculate_position_size_safe(self, risk_multiplier: float) -> float:
        """Safely calculate position size"""
        try:
            base_size = self.calculate_position_size_exact(risk_multiplier)
            # Ensure minimum and maximum bounds
            min_size = 1  # Minimum 1 share
            max_size = self.position_tracker.get_max_position_size()
            
            return max(min_size, min(base_size, max_size))
        except Exception as e:
            self.logger.error(f"Position size calculation error: {str(e)}")
            return 0

    def is_in_time_window(self, current: time, start: time, end: time) -> bool:
        """Check if current time is within a window"""
        return start <= current <= end

    def check_fallback_entry(self, strategy_id: str) -> bool:
        """Check if fallback entry conditions are met"""
        # Implement strategy-specific fallback logic
        # For example, allow entry up to 30 minutes after primary window
        # if certain conditions are still valid
        return False

    def is_bullish_candle(self, candle: dict) -> bool:
        """Check if candle is bullish with validation"""
        return candle['close'] > candle['open'] and candle['close'] > 0

    def is_bearish_candle(self, candle: dict) -> bool:
        """Check if candle is bearish with validation"""
        return candle['close'] < candle['open'] and candle['close'] > 0


class PositionTracker:
    """Track positions and allocations across strategies"""
    
    def __init__(self):
        self.positions = {}
        self.capital_used = {}
        self.total_positions = 0
        self.logger = logging.getLogger('PositionTracker')
    
    def can_open_position(self, strategy_id: str) -> bool:
        """Check if a new position can be opened"""
        # Check strategy position limit
        strategy_positions = self.positions.get(strategy_id, 0)
        if strategy_positions >= 1:  # Max 1 position per strategy
            return False
        
        # Check total position limit
        if self.total_positions >= 3:  # Max 3 total positions
            return False
        
        return True
    
    def check_capital_allocation(self, strategy_id: str, position_value: float) -> bool:
        """Check if capital allocation allows this position"""
        current_allocation = self.capital_used.get(strategy_id, 0)
        total_capital = self.get_total_capital()  # Implement based on your needs
        
        if (current_allocation + position_value) > (total_capital * 0.3):
            return False
        
        return True
    
    def record_entry(self, strategy_id: str, action: str, size: float, price: float):
        """Record a new position entry"""
        self.positions[strategy_id] = self.positions.get(strategy_id, 0) + 1
        self.capital_used[strategy_id] = self.capital_used.get(strategy_id, 0) + (size * price)
        self.total_positions += 1
        
        self.logger.info(
            f"Position opened: {strategy_id} {action} {size} @ {price}"
        )
    
    def record_exit(self, strategy_id: str):
        """Record a position exit"""
        if strategy_id in self.positions:
            self.positions[strategy_id] = max(0, self.positions[strategy_id] - 1)
            if self.positions[strategy_id] == 0:
                self.capital_used[strategy_id] = 0
            self.total_positions = max(0, self.total_positions - 1)
    
    def get_max_position_size(self) -> float:
        """Get maximum allowed position size"""
        # Implement based on your risk management rules
        return 1000  # Example: max 1000 shares
    
    def get_total_capital(self) -> float:
        """Get total available capital"""
        # Implement based on your account
        return 100000  # Example: $100k account
