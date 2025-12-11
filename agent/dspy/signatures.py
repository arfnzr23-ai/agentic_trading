import dspy
from ..models.schemas import TradeSignal, TradeSignal

# NOTE: We use the Shared Pydantic Model 'TradeSignal' for the output.
# This ensures the Shadow Agent uses the EXACT same output structure as the Legacy Agent.

class StrategicAnalysis(dspy.Signature):
    """
    Generate a high-conviction trading plan based on multi-timeframe structure.
    SHADOW MODE GOAL: Test experimental setups. Be aggressive.
    Do NOT play it safe. If there is a >40% chance of a move, TAKE IT to gather data.
    """
    # --- STANDARD INPUTS ---
    market_structure: str = dspy.InputField(desc="Multi-timeframe analysis (1D, 4H, 1H) focusing on trend alignment")
    risk_environment: str = dspy.InputField(desc="Assessment of volatility, funding rates, and liquidation levels")
    
    # --- USER CUSTOMIZATION INPUTS ---
    social_sentiment: float = dspy.InputField(desc="Aggregated social score (0-100) from external providers")
    whale_activity: str = dspy.InputField(desc="Summary of large holder flows and significant on-chain movements")
    macro_context: str = dspy.InputField(desc="Upcoming economic events (FOMC, CPI) and their timing")
    
    # --- OUTPUT ---
    # TypedPredictor will automatically enforce the TradeSignal Pydantic schema
    plan: TradeSignal = dspy.OutputField(desc="Executable trading plan. Prefer ACTION over HOLD.")
