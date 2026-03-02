#!/usr/bin/env python3
"""
Signal State Machine
Manages trade signal lifecycle with cooldown logic
"""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional, Dict

class SignalState(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COOLDOWN = "cooldown"
    EXPIRED = "expired"

class SignalType(Enum):
    LONG = "long"
    SHORT = "short"

@dataclass
class TradeSignal:
    symbol: str
    signal_type: SignalType
    entry_price: float
    stop_loss: float
    take_profit: float
    timeframe: str
    regime: str
    confidence: float
    timestamp: datetime
    state: SignalState = SignalState.PENDING
    state_changed_at: Optional[datetime] = None

class SignalStateMachine:
    def __init__(self, state_file: Path = None, cooldown_minutes: int = 60):
        self.state_file = state_file or Path('/root/.openclaw/workspace/data/signal_states.json')
        self.cooldown_minutes = cooldown_minutes
        self.signals: Dict[str, TradeSignal] = {}
        self.load_state()
    
    def load_state(self):
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.signals = {k: TradeSignal(**v) for k, v in data.items()}
            except:
                self.signals = {}
    
    def save_state(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump({k: v.__dict__ for k, v in self.signals.items()}, f, indent=2, default=str)
    
    def _generate_signal_id(self, symbol: str, signal_type: SignalType, entry: float) -> str:
        rounded_entry = round(entry, -2)
        return f"{symbol}_{signal_type.value}_{rounded_entry}"
    
    def check_duplicate(self, symbol: str, signal_type: SignalType, entry: float) -> Optional[TradeSignal]:
        signal_id = self._generate_signal_id(symbol, signal_type, entry)
        
        if signal_id in self.signals:
            existing = self.signals[signal_id]
            if existing.state in [SignalState.PENDING, SignalState.ACTIVE]:
                return existing
            if existing.state == SignalState.COOLDOWN:
                time_in_cooldown = datetime.now() - existing.state_changed_at
                if time_in_cooldown < timedelta(minutes=self.cooldown_minutes):
                    return existing
        return None
    
    def create_signal(self, symbol: str, signal_type: SignalType, 
                      entry: float, stop: float, target: float,
                      timeframe: str, regime: str, confidence: float) -> Optional[TradeSignal]:
        existing = self.check_duplicate(symbol, signal_type, entry)
        if existing:
            return None
        
        signal_id = self._generate_signal_id(symbol, signal_type, entry)
        signal = TradeSignal(
            symbol=symbol,
            signal_type=signal_type,
            entry_price=entry,
            stop_loss=stop,
            take_profit=target,
            timeframe=timeframe,
            regime=regime,
            confidence=confidence,
            timestamp=datetime.now(),
            state=SignalState.PENDING
        )
        
        self.signals[signal_id] = signal
        self.save_state()
        return signal
    
    def confirm_signal(self, signal_id: str) -> bool:
        if signal_id not in self.signals:
            return False
        signal = self.signals[signal_id]
        if signal.state != SignalState.PENDING:
            return False
        signal.state = SignalState.ACTIVE
        signal.state_changed_at = datetime.now()
        self.save_state()
        return True
    
    def invalidate_signal(self, signal_id: str) -> bool:
        if signal_id not in self.signals:
            return False
        signal = self.signals[signal_id]
        if signal.state not in [SignalState.PENDING, SignalState.ACTIVE]:
            return False
        signal.state = SignalState.COOLDOWN
        signal.state_changed_at = datetime.now()
        self.save_state()
        return True
