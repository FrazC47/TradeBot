#!/usr/bin/env python3
"""
ETHUSDT Dedicated Agent
Specialized trading agent for Ethereum/USDT pair only
"""

import json
import csv
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import sys

# ETHUSDT Agent Configuration
AGENT_CONFIG = {
    'symbol': 'ETHUSDT',
    'name': 'ETHUSDT_Specialist_Agent',
    'version': '1.0.0',
    
    # Data Configuration
    'data_dir': '/root/.openclaw/workspace/data/binance/ETHUSDT',
    'state_file': '/root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/state/agent_state.json',
    'log_file': '/root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/logs/agent.log',
    
    # Trading Parameters (ETH-specific)
    # Uses ALL timeframes as per original MTF framework agreement
    'timeframes': ['1M', '1w', '1d', '4h', '1h', '15m', '5m'],
    'primary_timeframe': '1h',  # Main entry/exit decisions
    'execution_timeframe': '5m',  # Precision entries
    'strategy': 'selective_momentum_v2',
    
    # Entry Parameters
    'entry': {
        'ema_fast': 9,
        'ema_slow': 21,
        'rsi_period': 14,
        'rsi_min': 40,
        'rsi_max': 75,
        'volume_threshold': 1.0,
        'consecutive_bullish': 2,
        'require_confirmation': True,
        'max_range_location': 70,  # Don't chase
    },
    
    # Risk Management
    'risk': {
        'risk_per_trade': 0.03,  # 3%
        'leverage': 5,
        'atr_multiplier_stop': 1.5,
        'atr_multiplier_target': 3.0,
        'min_rr': 2.0,
        'position_scale': True,
        'initial_scale': 0.5,
        'add_scale': 0.5,
    },
    
    # Filters
    'filters': {
        'max_volatility': 4.0,  # ATR%
        'trading_hours': '24/7',  # Crypto never sleeps
        'max_trades_per_day': 3,
        'cooldown_minutes': 60,
    }
}

class ETHUSDTAgent:
    """Dedicated agent for ETHUSDT trading"""
    
    def __init__(self):
        self.config = AGENT_CONFIG
        self.symbol = self.config['symbol']
        self.state = self.load_state()
        self.setup_logging()
        
    def setup_logging(self):
        """Setup dedicated logging for this agent"""
        log_file = Path(self.config['log_file'])
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - ETHUSDT_AGENT - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('ETHUSDT_AGENT')
        
    def load_state(self) -> Dict:
        """Load agent state from file"""
        state_file = Path(self.config['state_file'])
        if state_file.exists():
            with open(state_file, 'r') as f:
                return json.load(f)
        return {
            'last_run': None,
            'trades_today': 0,
            'last_trade_time': None,
            'active_setup': None,
            'total_trades': 0,
            'winning_trades': 0,
            'total_pnl': 0,
        }
    
    def save_state(self):
        """Save agent state to file"""
        state_file = Path(self.config['state_file'])
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def load_ohlcv(self, timeframe: str) -> List[Dict]:
        """Load OHLCV data for ETHUSDT only"""
        filepath = Path(self.config['data_dir']) / f"{timeframe}.csv"
        if not filepath.exists():
            self.logger.warning(f"Data file not found: {filepath}")
            return []
        
        data = []
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append({
                    'timestamp': int(row['open_time']),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row['volume'])
                })
        return data
    
    def calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate EMA"""
        if len(prices) < period:
            return sum(prices) / len(prices)
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        return ema
    
    def calculate_atr(self, data: List[Dict], period: int = 14) -> float:
        """Calculate ATR"""
        if len(data) < period + 1:
            return 0
        tr_list = []
        for i in range(1, len(data)):
            high = data[i]['high']
            low = data[i]['low']
            prev_close = data[i-1]['close']
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            tr_list.append(tr)
        return sum(tr_list[-period:]) / period
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        gains = []
        losses = []
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def check_trading_allowed(self) -> bool:
        """Check if trading is allowed based on daily limits"""
        now = datetime.now()
        
        # Reset daily counter
        if self.state['last_run']:
            last_run = datetime.fromisoformat(self.state['last_run'])
            if last_run.date() != now.date():
                self.state['trades_today'] = 0
                self.logger.info("Daily trade counter reset")
        
        # Check max trades per day
        if self.state['trades_today'] >= self.config['filters']['max_trades_per_day']:
            self.logger.info(f"Max trades ({self.config['filters']['max_trades_per_day']}) reached for today")
            return False
        
        # Check cooldown
        if self.state['last_trade_time']:
            last_trade = datetime.fromisoformat(self.state['last_trade_time'])
            cooldown = timedelta(minutes=self.config['filters']['cooldown_minutes'])
            if now - last_trade < cooldown:
                remaining = cooldown - (now - last_trade)
                self.logger.info(f"In cooldown period. {remaining.seconds // 60} minutes remaining")
                return False
        
        return True
    
    def analyze_eth_setup(self) -> Optional[Dict]:
        """
        ETH-specific setup analysis using full MTF framework
        Analyzes all timeframes: 1M -> 1w -> 1d -> 4h -> 1h -> 15m -> 5m
        """
        self.logger.info("Analyzing ETHUSDT using full MTF framework...")
        
        # Load ALL timeframe data as per original agreement
        data_1M = self.load_ohlcv('1M')
        data_1w = self.load_ohlcv('1w')
        data_1d = self.load_ohlcv('1d')
        data_4h = self.load_ohlcv('4h')
        data_1h = self.load_ohlcv('1h')
        data_15m = self.load_ohlcv('15m')
        data_5m = self.load_ohlcv('5m')
        
        # Primary analysis on 1h (as per strategy)
        if not data_1h or len(data_1h) < 50:
            self.logger.warning("Insufficient 1h data")
            return None
        
        # Get recent data from primary timeframe
        recent = data_1h[-50:]
        prices = [c['close'] for c in recent]
        highs = [c['high'] for c in recent]
        lows = [c['low'] for c in recent]
        volumes = [c['volume'] for c in recent]
        
        current_price = prices[-1]
        
        # Calculate indicators on 1h
        ema9 = self.calculate_ema(prices[-20:], self.config['entry']['ema_fast'])
        ema21 = self.calculate_ema(prices[-30:], self.config['entry']['ema_slow'])
        atr = self.calculate_atr(recent)
        atr_pct = (atr / current_price) * 100
        rsi = self.calculate_rsi(prices)
        
        # Volume analysis on 1h
        avg_volume = sum(volumes[-20:]) / 20
        volume_ratio = recent[-1]['volume'] / avg_volume
        
        # Range location on 1h
        recent_high = max(highs[-30:])
        recent_low = min(lows[-30:])
        range_pct = (current_price - recent_low) / (recent_high - recent_low) * 100
        
        # Check higher timeframe trend (4h and 1d)
        trend_aligned = True
        if data_4h and len(data_4h) > 30:
            prices_4h = [c['close'] for c in data_4h[-30:]]
            ema9_4h = self.calculate_ema(prices_4h[-20:], 9)
            ema21_4h = self.calculate_ema(prices_4h[-30:], 21)
            trend_4h = prices_4h[-1] > ema9_4h > ema21_4h
            if not trend_4h:
                trend_aligned = False
                self.logger.info("  4h trend not aligned")
        
        # Check consecutive bullish candles on 1h
        bullish_count = 0
        for i in range(-1, -6, -1):
            if prices[i] > prices[i-1]:
                bullish_count += 1
            else:
                break
        
        # Check breakout on 1h
        recent_resistance = max(highs[-10:-1])
        broke_resistance = current_price > recent_resistance
        
        # Log full MTF analysis
        self.logger.info(f"ETH MTF Analysis @ ${current_price:.2f}")
        self.logger.info(f"  Timeframes: 1M,1w,1d,4h,1h,15m,5m (all loaded)")
        self.logger.info(f"  Primary (1h) EMA9: ${ema9:.2f}, EMA21: ${ema21:.2f}")
        self.logger.info(f"  Primary (1h) RSI: {rsi:.1f}, ATR%: {atr_pct:.2f}%")
        self.logger.info(f"  Volume (1h): {volume_ratio:.2f}x, Range: {range_pct:.1f}%")
        self.logger.info(f"  HTF Trend Aligned: {trend_aligned}")
        self.logger.info(f"  Bullish candles (1h): {bullish_count}, Breakout: {broke_resistance}")
        
        # Apply ETH-specific filters
        setup = {
            'symbol': self.symbol,
            'timestamp': datetime.now().isoformat(),
            'price': current_price,
            'timeframes_analyzed': ['1M', '1w', '1d', '4h', '1h', '15m', '5m'],
            'primary_timeframe': '1h',
            'indicators': {
                'ema9': ema9,
                'ema21': ema21,
                'rsi': rsi,
                'atr': atr,
                'atr_pct': atr_pct,
                'volume_ratio': volume_ratio,
                'range_pct': range_pct,
            },
            'signals': {
                'htf_trend_aligned': trend_aligned,  # Higher timeframe trend
                'ema_aligned': current_price > ema9 > ema21,
                'rsi_ok': self.config['entry']['rsi_min'] < rsi < self.config['entry']['rsi_max'],
                'volume_ok': volume_ratio >= self.config['entry']['volume_threshold'],
                'momentum_ok': bullish_count >= self.config['entry']['consecutive_bullish'],
                'breakout': broke_resistance,
                'range_ok': range_pct <= self.config['entry']['max_range_location'],
                'volatility_ok': atr_pct <= self.config['filters']['max_volatility'],
            }
        }
        
        # Count passed filters
        passed = sum(1 for v in setup['signals'].values() if v)
        total = len(setup['signals'])
        self.logger.info(f"  Filters passed: {passed}/{total}")
        
        # Check if all filters pass
        if all(setup['signals'].values()):
            # Calculate trade levels
            stop = current_price - (atr * self.config['risk']['atr_multiplier_stop'])
            target = current_price + (atr * self.config['risk']['atr_multiplier_target'])
            
            risk = current_price - stop
            reward = target - current_price
            rr = reward / risk if risk > 0 else 0
            
            if rr >= self.config['risk']['min_rr']:
                setup['trade'] = {
                    'direction': 'LONG',
                    'entry': current_price,
                    'stop': stop,
                    'target': target,
                    'rr': rr,
                    'position_scale': self.config['risk']['position_scale'],
                }
                self.logger.info(f"✅ VALID SETUP FOUND: Long @ ${current_price:.2f}, R:R = 1:{rr:.1f}")
                return setup
            else:
                self.logger.info(f"❌ R:R too low: 1:{rr:.1f} (need {self.config['risk']['min_rr']}:1)")
        else:
            failed = [k for k, v in setup['signals'].items() if not v]
            self.logger.info(f"❌ Filters failed: {', '.join(failed)}")
        
        return setup
    
    def run(self):
        """Main agent execution"""
        self.logger.info("="*60)
        self.logger.info("ETHUSDT AGENT STARTING")
        self.logger.info("="*60)
        
        # Update state
        self.state['last_run'] = datetime.now().isoformat()
        
        # Check if trading allowed
        if not self.check_trading_allowed():
            self.logger.info("Trading not allowed at this time")
            self.save_state()
            return
        
        # Analyze for setup
        setup = self.analyze_eth_setup()
        
        if setup and 'trade' in setup:
            self.logger.info("🎯 TRADE OPPORTUNITY IDENTIFIED")
            self.logger.info(json.dumps(setup['trade'], indent=2))
            
            # ACTIVATE GRANULAR MODE for precision entry/exit
            self.logger.info("⚡ ACTIVATING GRANULAR MODE (1m data) for precision entry")
            self.state['granular_mode_active'] = True
            self.state['granular_mode_activated_at'] = datetime.now().isoformat()
            self.state['granular_mode_reason'] = 'SETUP_IDENTIFIED'
            
            # Here you would:
            # 1. Send alert to user
            # 2. Log the setup
            # 3. Wait for confirmation or auto-trade
            
            # Update state
            self.state['active_setup'] = setup
            
        else:
            # No setup - check if we should deactivate granular mode
            if self.state.get('granular_mode_active'):
                activated_at = datetime.fromisoformat(self.state.get('granular_mode_activated_at', datetime.now().isoformat()))
                age_minutes = (datetime.now() - activated_at).total_seconds() / 60
                
                if age_minutes > 30:  # 30 minute timeout
                    self.logger.info("⏱️ DEACTIVATING GRANULAR MODE (timeout)")
                    self.state['granular_mode_active'] = False
                    self.state['granular_mode_deactivated_at'] = datetime.now().isoformat()
        else:
            self.logger.info("No valid setup found this cycle")
        
        self.save_state()
        self.logger.info("="*60)
        self.logger.info("ETHUSDT AGENT COMPLETE")
        self.logger.info("="*60)

if __name__ == '__main__':
    agent = ETHUSDTAgent()
    agent.run()
