"""Database layer package."""

from .models import Trade, Signal, ExitPlan, Approval, AgentLog, InferenceLog, ALL_MODELS
from .engine import create_tables, get_session, get_async_session
from .repository import (
    TradeRepository,
    ExitPlanRepository,
    AgentLogRepository,
    InferenceLogRepository,
    InferenceLogRepository,
    ApprovalRepository,
    MarketMemoryRepository
)
from .dspy_memory import (
    init_dspy_db,
    get_dspy_session,
    ShadowTrade,
    ShadowAccountState,
    ShadowStats,
    OptimizationExample,
    DSPyRepository
)

__all__ = [
    # Models
    "Trade",
    "Signal", 
    "ExitPlan",
    "Approval",
    "AgentLog",
    "InferenceLog",
    "ALL_MODELS",
    # Engine
    "create_tables",
    "get_session",
    "get_async_session",
    # Repositories
    "TradeRepository",
    "ExitPlanRepository",
    "AgentLogRepository",
    "InferenceLogRepository",
    "InferenceLogRepository",
    "ApprovalRepository",
    "MarketMemoryRepository",
    # DSPy Memory
    "init_dspy_db",
    "get_dspy_session",
    "ShadowTrade",
    "ShadowAccountState",
    "ShadowStats",
    "OptimizationExample",
    "DSPyRepository"
]

