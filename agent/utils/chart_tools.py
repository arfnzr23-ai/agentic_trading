"""
Chart Tools Module

Provides robust technical analysis using TA-Lib and compressed string formatting
for zero-hallucination LLM context.
"""

import numpy as np
import talib
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

def calculate_indicators(candles: list, interval: str = "1h") -> dict:
    """
    Calculate institutional-grade indicators using TA-Lib.
    
    Args:
        candles: List of dicts (o, h, l, c, v)
        interval: Timeframe (affects parameters)
        
    Returns:
        dict with keys: rsi, bbands, atr, obv, vwap, regime
    """
    if not candles:
        return {}
        
    # extract arrays
    closes = np.array([c.get("c", 0) for c in candles], dtype=float)
    highs = np.array([c.get("h", 0) for c in candles], dtype=float)
    lows = np.array([c.get("l", 0) for c in candles], dtype=float)
    opens = np.array([c.get("o", 0) for c in candles], dtype=float)
    volumes = np.array([c.get("v", 0) for c in candles], dtype=float)
    
    # 1. Period Settings based on Interval
    if interval in ["1m", "5m", "15m"]:
        # Scalp Settings
        bb_period = 10
        bb_dev = 1.5
    else:
        # Swing Settings
        bb_period = 20
        bb_dev = 2.0
        
    # 2. Calculate Indicators (TA-Lib)
    rsi = talib.RSI(closes, timeperiod=14)
    upper, middle, lower = talib.BBANDS(closes, timeperiod=bb_period, nbdevup=bb_dev, nbdevdn=bb_dev, matype=0)
    atr = talib.ATR(highs, lows, closes, timeperiod=14)
    obv = talib.OBV(closes, volumes)
    
    # NEW: ADX (Trend Strength)
    adx = talib.ADX(highs, lows, closes, timeperiod=14)
    
    # NEW: EMA Crossover (9/21)
    ema9 = talib.EMA(closes, timeperiod=9)
    ema21 = talib.EMA(closes, timeperiod=21)
    
    # VWAP (Manual calculation for robustness if pandas avail, else simple avg)
    # Simple Rolling VWAP approc for context window
    typical_price = (highs + lows + closes) / 3
    vwap = np.cumsum(volumes * typical_price) / np.cumsum(volumes)
    
    # 3. Current Values (Last closed candle)
    curr_close = closes[-1]
    curr_rsi = rsi[-1]
    curr_atr = atr[-1]
    curr_upper = upper[-1]
    curr_lower = lower[-1]
    curr_obv = obv[-1]
    curr_vwap = vwap[-1]
    
    # 4. Derived Interpretations
    # Regime
    if curr_close > curr_vwap:
        regime = "UPTREND"
    elif curr_close < curr_vwap:
        regime = "DOWNTREND"
    else:
        regime = "NEUTRAL"
        
    # Volatility
    atr_pct = (curr_atr / curr_close) * 100 if curr_close > 0 else 0
    vol_tag = "HIGH" if atr_pct > 1.0 else "LOW"
    
    # Flow (OBV Slope of last 5)
    obv_slope = obv[-1] - obv[-5] if len(obv) > 5 else 0
    flow_tag = "ACCUMULATION" if obv_slope > 0 else "DISTRIBUTION"
    
    # NEW: Trend Strength (ADX)
    curr_adx = adx[-1] if not np.isnan(adx[-1]) else 0
    trend_strength = "STRONG" if curr_adx > 25 else "WEAK"
    
    # NEW: EMA Cross
    curr_ema9 = ema9[-1] if not np.isnan(ema9[-1]) else curr_close
    curr_ema21 = ema21[-1] if not np.isnan(ema21[-1]) else curr_close
    ema_cross = "BULLISH" if curr_ema9 > curr_ema21 else "BEARISH"
    
    return {
        "price": curr_close,
        "rsi": curr_rsi,
        "atr": curr_atr,
        "atr_pct": atr_pct,
        "bb_upper": curr_upper,
        "bb_lower": curr_lower,
        "obv_slope": obv_slope,
        "vwap": curr_vwap,
        "regime": regime,
        "vol_tag": vol_tag,
        "flow_tag": flow_tag,
        "bb_width_pct": ((curr_upper - curr_lower) / curr_lower) * 100 if curr_lower > 0 else 0,
        # NEW Fields
        "adx": curr_adx,
        "trend_strength": trend_strength,
        "ema9": curr_ema9,
        "ema21": curr_ema21,
        "ema_cross": ema_cross
    }

def format_context_string(coin: str, interval: str, indicators: dict, candles: list) -> str:
    """
    Format indicators into a compressed, zero-hallucination string.
    """
    if not indicators:
        return "No data available."
        
    # Header
    header = f"[{coin} {interval.upper()}]\n"
    header += f"Price: ${indicators['price']:.2f} | Regime: {indicators['regime']} (Price vs VWAP)\n"
    header += f"Vol: {indicators['vol_tag']} (ATR={indicators['atr_pct']:.2f}%) | Flow: {indicators['flow_tag']} (OBV)\n"
    
    # Momentum Detail
    rsi_state = "Overbought" if indicators['rsi'] > 70 else "Oversold" if indicators['rsi'] < 30 else "Neutral"
    header += f"Momentum: RSI={indicators['rsi']:.1f} ({rsi_state}) | Bands: Width={indicators['bb_width_pct']:.1f}%\n"
    
    # Body (Compressed Candles - Last 10)
    body = "Recent Shape: "
    recent = candles[-10:] if len(candles) > 10 else candles
    
    formatted_candles = []
    for c in recent:
        close = float(c.get("c", 0))
        open_p = float(c.get("o", 0))
        color = "🟢" if close >= open_p else "🔴"
        formatted_candles.append(f"{color}{int(close)}")
        
    body += " -> ".join(formatted_candles)
    
    return header + body

def format_compressed_json(coin: str, interval: str, indicators: dict) -> dict:
    """
    Format indicators into a structured JSON object for token-efficient LLM context.
    ~80% token reduction vs string format.
    """
    if not indicators:
        return {}
    
    return {
        "tf": interval.upper(),
        "px": round(indicators.get("price", 0), 2),
        "regime": indicators.get("regime", "N/A"),
        "strength": indicators.get("trend_strength", "WEAK"),
        "ema": indicators.get("ema_cross", "N/A"),
        "rsi": round(indicators.get("rsi", 0), 1),
        "adx": round(indicators.get("adx", 0), 1),
        "atr_pct": round(indicators.get("atr_pct", 0), 2),
        "flow": indicators.get("flow_tag", "N/A")
    }

def format_ultra_compressed(coin: str, indicators: dict) -> str:
    """
    Ultra-compressed single-line format.
    Example: BTC|5M|UP|STRONG|BULL|RSI55|ADX30|ATR1.5%|ACC
    """
    if not indicators:
        return "NO_DATA"
    
    regime_short = indicators.get("regime", "N")[0]  # U/D/N
    strength_short = "S" if indicators.get("trend_strength") == "STRONG" else "W"
    ema_short = "B" if indicators.get("ema_cross") == "BULLISH" else "S"
    flow_short = "A" if indicators.get("flow_tag") == "ACCUMULATION" else "D"
    
    return f"{coin}|{regime_short}{strength_short}|EMA{ema_short}|RSI{int(indicators.get('rsi', 0))}|ADX{int(indicators.get('adx', 0))}|{flow_short}"
