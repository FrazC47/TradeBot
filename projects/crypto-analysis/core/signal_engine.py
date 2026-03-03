#!/usr/bin/env python3
"""
Signal Engine - State Machine for Trade Signals
Handles PENDING → ACTIVE → COOLDOWN → EXPIRED lifecycle
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from enum import Enum

class SignalStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COOLDOWN = "cooldown"
    EXPIRED = "expired"

@dataclass
class TradeSignal:
    """Trade signal with all metadata"""
    signal_id: str
    symbol: str
    direction: str
    status: SignalStatus
    entry_zone_low: float
    entry_zone_high: float
    stop_loss: float
    target_1: float
    target_2: float
    created_at: int
    expires_at: int
    activated_at: Optional[int] = None
    invalidated_at: Optional[int] = None
    invalidated_reason: Optional[str] = None
    mtf_snapshot: Dict = None
    
    def to_dict(self):
        data = asdict(self)
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data):
        data['status'] = SignalStatus(data['status'])
        return cls(**data)

class SignalEngine:
    """Manages signal lifecycle and state transitions"""
    
    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.signals: Dict[str, List[TradeSignal]] = {}
        self.load_state()
    
    def load_state(self):
        """Load signal state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.signals = {
                        symbol: [TradeSignal.from_dict(s) for s in signals]
                        for symbol, signals in data.items()
                    }
            except Exception as e:
                print(f"Error loading state: {e}")
                self.signals = {}
    
    def save_state(self):
        """Save signal state atomically"""
        try:
            tmp_file = self.state_file.with_suffix('.tmp')
            with open(tmp_file, 'w') as f:
                json.dump(
                    {symbol: [s.to_dict() for s in signals] 
                     for symbol, signals in self.signals.items()},
                    f, indent=2, default=str
                )
            tmp_file.rename(self.state_file)
        except Exception as e:
            print(f"Error saving state: {e}")
    
    def generate_signal_id(self, symbol: str, direction: str, 
                          entry_low: float, entry_high: float,
                          stop: float, macro_regime: str) -> str:
        """Generate stable signal ID"""
        tick_size = 0.01 if 'BTC' not in symbol else 0.1
        entry_mid = (entry_low + entry_high) / 2
        rounded_entry = round(entry_mid / tick_size) * tick_size
        
        unique_str = f"{symbol}_{direction}_{rounded_entry:.0f}_{stop:.0f}_{macro_regime}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:12]
    
    def create_signal(self, symbol: str, direction: str,
                     entry_zone: tuple, stop: float, targets: tuple,
                     mtf_snapshot: Dict, macro_regime: str) -> Optional[TradeSignal]:
        """Create new signal if no duplicate exists"""
        entry_low, entry_high = entry_zone
        target_1, target_2 = targets
        
        signal_id = self.generate_signal_id(symbol, direction, 
                                           entry_low, entry_high, 
                                           stop, macro_regime)
        
        # Check for existing
        existing = self.check_duplicate(signal_id, symbol)
        if existing:
            print(f"Signal blocked: {existing.status.value} signal exists")
            return None
        
        now = int(datetime.now().timestamp() * 1000)
        expires = now + (30 * 60 * 1000)  # 30 minutes
        
        signal = TradeSignal(
            signal_id=signal_id,
            symbol=symbol,
            direction=direction,
            status=SignalStatus.PENDING,
            entry_zone_low=entry_low,
            entry_zone_high=entry_high,
            stop_loss=stop,
            target_1=target_1,
            target_2=target_2,
            created_at=now,
            expires_at=expires,
            mtf_snapshot=mtf_snapshot
        )
        
        if symbol not in self.signals:
            self.signals[symbol] = []
        
        self.signals[symbol].append(signal)
        self.save_state()
        
        return signal
    
    def check_duplicate(self, signal_id: str, symbol: str) -> Optional[TradeSignal]:
        """Check if similar signal already exists"""
        if symbol not in self.signals:
            return None
        
        for signal in self.signals[symbol]:
            if signal.signal_id == signal_id:
                if signal.status in [SignalStatus.PENDING, SignalStatus.ACTIVE]:
                    return signal
                
                if signal.status == SignalStatus.COOLDOWN:
                    if signal.invalidated_at:
                        age_minutes = (datetime.now().timestamp() * 1000 - signal.invalidated_at) / (1000 * 60)
                        if age_minutes < 120:
                            return signal
        
        return None
    
    def confirm_signal(self, signal_id: str, symbol: str) -> bool:
        """Confirm PENDING signal → ACTIVE"""
        if symbol not in self.signals:
            return False
        
        for signal in self.signals[symbol]:
            if signal.signal_id == signal_id:
                if signal.status != SignalStatus.PENDING:
                    return False
                
                now = int(datetime.now().timestamp() * 1000)
                if now > signal.expires_at:
                    signal.status = SignalStatus.EXPIRED
                    self.save_state()
                    return False
                
                signal.status = SignalStatus.ACTIVE
                signal.activated_at = now
                self.save_state()
                
                print(f"✅ Signal {signal_id} ACTIVATED")
                return True
        
        return False
    
    def invalidate_signal(self, signal_id: str, symbol: str, 
                         reason: str) -> bool:
        """Invalidate ACTIVE/PENDING signal → COOLDOWN"""
        if symbol not in self.signals:
            return False
        
        for signal in self.signals[symbol]:
            if signal.signal_id == signal_id:
                if signal.status not in [SignalStatus.PENDING, SignalStatus.ACTIVE]:
                    return False
                
                signal.status = SignalStatus.COOLDOWN
                signal.invalidated_at = int(datetime.now().timestamp() * 1000)
                signal.invalidated_reason = reason
                self.save_state()
                
                print(f"❌ Signal {signal_id} INVALIDATED: {reason}")
                return True
        
        return False

if __name__ == '__main__':
    engine = SignalEngine(Path('/root/.openclaw/workspace/data/state/signals_state.json'))
    
    # Test
    signal = engine.create_signal(
        'BTCUSDT', 'LONG',
        (66200, 66300), 65900, (66800, 67200),
        {'overall_score': 0.55}, 'trend_bull'
    )
    
    if signal:
        print(f"Created signal: {signal.signal_id}")
        engine.confirm_signal(signal.signal_id, 'BTCUSDT')
