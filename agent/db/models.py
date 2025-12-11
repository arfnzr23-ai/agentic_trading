"""
Database Models

SQLModel schemas for trades, signals, exit plans, and agent logs.
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
import json


class Trade(SQLModel, table=True):
    """Record of executed trades."""
    __tablename__ = "trades"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    opened_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None
    
    # Trade details
    coin: str = Field(index=True)
    direction: str  # "LONG" or "SHORT"
    entry_price: float
    exit_price: Optional[float] = None
    size_usd: float
    size_tokens: float
    leverage: int
    
    # Results
    pnl_usd: Optional[float] = None
    pnl_pct: Optional[float] = None
    close_reason: Optional[str] = None  # "TP", "SL", "INVALIDATION", "MANUAL", "DRAWDOWN"
    
    # Context
    reasoning: str
    signal_id: Optional[int] = Field(default=None, foreign_key="signals.id")
    
    # Relationships
    exit_plan: Optional["ExitPlan"] = Relationship(back_populates="trade")
    approvals: list["Approval"] = Relationship(back_populates="trade")


class Signal(SQLModel, table=True):
    """Generated trade signals from analyst."""
    __tablename__ = "signals"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    coin: str = Field(index=True)
    signal_type: str  # "LONG", "SHORT", "CLOSE", "HOLD"
    confidence: float  # 0.0 - 1.0
    
    entry_price: Optional[float] = None
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    
    analysis: str  # Full analysis text
    executed: bool = Field(default=False)
    rejected_reason: Optional[str] = None


class ExitPlan(SQLModel, table=True):
    """Exit plan with invalidation conditions for active trades."""
    __tablename__ = "exit_plans"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    trade_id: int = Field(foreign_key="trades.id", unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Exit targets
    take_profit_price: float
    take_profit_pct: float
    stop_loss_price: float
    stop_loss_pct: float
    
    # Invalidation conditions (stored as JSON array)
    invalidation_conditions_json: str = Field(default="[]")
    
    # Status
    status: str = Field(default="ACTIVE")  # "ACTIVE", "TP_HIT", "SL_HIT", "INVALIDATED", "CLOSED"
    triggered_at: Optional[datetime] = None
    triggered_reason: Optional[str] = None
    
    # Relationship
    trade: Optional[Trade] = Relationship(back_populates="exit_plan")
    
    @property
    def invalidation_conditions(self) -> list[str]:
        """Get invalidation conditions as list."""
        return json.loads(self.invalidation_conditions_json)
    
    @invalidation_conditions.setter
    def invalidation_conditions(self, conditions: list[str]):
        """Set invalidation conditions from list."""
        self.invalidation_conditions_json = json.dumps(conditions)


class Approval(SQLModel, table=True):
    """Telegram approval requests and responses."""
    __tablename__ = "approvals"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    trade_id: Optional[int] = Field(default=None, foreign_key="trades.id")
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    responded_at: Optional[datetime] = None
    
    # Request details
    coin: str
    direction: str
    size_usd: float
    message_id: Optional[str] = None  # Telegram message ID
    
    # Response
    status: str = Field(default="PENDING")  # "PENDING", "APPROVED", "REJECTED", "TIMEOUT"
    responder: Optional[str] = None  # Telegram username
    
    # Relationship
    trade: Optional[Trade] = Relationship(back_populates="approvals")


class AgentLog(SQLModel, table=True):
    """Log of all agent actions for debugging and analysis."""
    __tablename__ = "agent_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    # Action details
    action_type: str = Field(index=True)  # "TOOL_CALL", "LLM_RESPONSE", "APPROVAL", "ERROR", "INFERENCE"
    node_name: Optional[str] = None  # "analyst", "risk", "merge"
    tool_name: Optional[str] = None
    
    # Content
    input_args: Optional[str] = None
    output: str
    
    # Full reasoning (not truncated) 
    reasoning: Optional[str] = None
    
    # Metrics
    tokens_used: Optional[int] = None
    latency_ms: Optional[int] = None
    
    # Error tracking
    error: Optional[str] = None


class InferenceLog(SQLModel, table=True):
    """Archive of each inference cycle with full reasoning from all agents."""
    __tablename__ = "inference_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    cycle_number: Optional[int] = None
    
    # Models used
    analyst_model: Optional[str] = None
    risk_model: Optional[str] = None
    
    # Analyst output
    analyst_signal: Optional[str] = None  # JSON
    analyst_reasoning: Optional[str] = None  # Full text
    analyst_tool_calls: Optional[str] = None  # JSON list of tool calls
    
    # Risk Manager output
    risk_decision: Optional[str] = None  # JSON
    risk_reasoning: Optional[str] = None  # Full text
    risk_tool_calls: Optional[str] = None  # JSON list of tool calls
    
    # Final decision
    final_action: Optional[str] = None  # "NO_TRADE", "EXECUTE", "REQUEST_APPROVAL", etc.
    final_reasoning: Optional[str] = None
    
    # Context at time of inference
    account_equity: Optional[float] = None
    account_margin_pct: Optional[float] = None
    active_positions: Optional[int] = None
    
    # Execution details (if trade was made)
    trade_id: Optional[int] = Field(default=None, foreign_key="trades.id")


class MarketMemory(SQLModel, table=True):
    """Daily market context cache to reduce token usage."""
    __tablename__ = "market_memories"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    date: str = Field(index=True)  # "YYYY-MM-DD"
    coin: str = Field(index=True)
    
    # Content
    analysis: str  # The 1D chart summary
    volatility_score: float  # 0-100
    market_bias: str  # "BULLISH", "BEARISH", "NEUTRAL"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TradePattern(SQLModel, table=True):
    """
    Learned trade patterns for continuous improvement.
    Tracks win rates by pattern type, market conditions, and context.
    """
    __tablename__ = "trade_patterns"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Pattern identification
    name: str = Field(index=True)  # "Bull Flag", "HTF Reversal", "Funding Fade"
    category: str  # "MOMENTUM", "REVERSAL", "BREAKOUT", "FADE"
    description: str  # Human-readable pattern description
    
    # Conditions (stored as JSON)
    conditions_json: str = Field(default="{}")  # {"funding": "extreme_positive", "htf_trend": "bearish"}
    
    # Performance metrics
    total_trades: int = Field(default=0)
    wins: int = Field(default=0)
    losses: int = Field(default=0)
    total_pnl: float = Field(default=0.0)
    avg_win_pct: float = Field(default=0.0)
    avg_loss_pct: float = Field(default=0.0)
    
    # Derived
    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return (self.wins / self.total_trades) * 100
    
    @property
    def expectancy(self) -> float:
        """Expected return per trade."""
        if self.total_trades == 0:
            return 0.0
        return self.total_pnl / self.total_trades


# Models for creating tables
ALL_MODELS = [Trade, Signal, ExitPlan, Approval, AgentLog, InferenceLog, MarketMemory, TradePattern]
