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

def execute_strategy1_exact(self):
    """Strategy 1: Opening Candle Direction (Exact Implementation)"""
    if not self.can_trade('strategy1') or len(self.ma350) < 350:
        return
    
    # Check daily risk limits before trading
    risk_ok, risk_msg = self.check_daily_risk_limits()
    if not risk_ok:
        return
    
    # **MARKET CLOSE EXIT - 5 minutes before close**
    now = datetime.now()
    if now.hour == 15 and now.minute == 55:  # 3:55 PM ET (5 min before 4:00 PM close)
        if self.strategy_positions['strategy1']:
            self.close_strategy_position('strategy1')
            return
    
    if not hasattr(self, 'candles_5m') or len(self.candles_5m) < 2:
        return
    
    # Check if this is 5 minutes after market open (9:35 AM ET)
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
    
    # **MARKET CLOSE EXIT - 5 minutes before close**
    now = datetime.now()
    if now.hour == 15 and now.minute == 55:  # 3:55 PM ET (5 min before 4:00 PM close)
        if self.strategy_positions['strategy2']:
            self.close_strategy_position('strategy2')
            return
    
    if not hasattr(self, 'candles_15m') or len(self.candles_15m) < 1:
        return
    
    current_candle = self.candles_15m[-1]
    ma300_value = sum(self.ma300) / len(self.ma300)
    
    # **VWAP TRAILING STOP - Close existing position if price crosses VWAP against us**
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
    
    # **MARKET CLOSE EXIT - 5 minutes before close**
    now = datetime.now()
    if now.hour == 15 and now.minute == 55:  # 3:55 PM ET (5 min before 4:00 PM close)
        if self.strategy_positions['strategy3']:
            self.close_strategy_position('strategy3')
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
    
    # **VWAP TRAILING STOP - Close existing position if price crosses VWAP against us**
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
