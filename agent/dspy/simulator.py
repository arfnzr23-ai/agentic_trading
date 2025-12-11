from datetime import datetime
from sqlmodel import select
from ..db.dspy_memory import get_dspy_session, ShadowTrade, DSPyRepository

# Import notification function
from ..telegram import notify_shadow_trade_closed

# Simulated fee rate (Hyperliquid averages ~0.03% per side)
SIMULATED_FEE_RATE = 0.0003  # Entry + Exit = ~0.06% total

class ShadowSimulator:
    """
    Simulates P&L for Shadow Trades by checking if price targets were hit.
    Includes fee simulation for realistic performance tracking.
    """
    
    @staticmethod
    async def update_open_trades(current_price: float, coin: str):
        """
        Check all OPEN shadow trades for this coin and close them if TP/SL hit.
        """
        if current_price <= 0:
            return
            
        with get_dspy_session() as session:
            # Find open trades (pnl_usd is None)
            statement = select(ShadowTrade).where(ShadowTrade.coin == coin).where(ShadowTrade.pnl_usd == None)
            open_trades = session.exec(statement).all()
            
            for trade in open_trades:
                exit_price = None
                reason = None
                
                # logic for LONG
                if trade.signal == "LONG":
                    # Check SL
                    if trade.stop_loss and current_price <= trade.stop_loss:
                        exit_price = trade.stop_loss
                        reason = "STOP_LOSS"
                    # Check TP
                    elif trade.take_profit and current_price >= trade.take_profit:
                        exit_price = trade.take_profit
                        reason = "TAKE_PROFIT"
                        
                # logic for SHORT
                elif trade.signal == "SHORT":
                    # Check SL (Price goes up)
                    if trade.stop_loss and current_price >= trade.stop_loss:
                        exit_price = trade.stop_loss
                        reason = "STOP_LOSS"
                    # Check TP (Price goes down)
                    elif trade.take_profit and current_price <= trade.take_profit:
                        exit_price = trade.take_profit
                        reason = "TAKE_PROFIT"
                
                # If exited
                if exit_price:
                    # Calculate PnL
                    lev = trade.leverage or 1
                    size = trade.size_usd or 1000
                    entry = trade.entry_price
                    
                    if entry > 0:
                        if trade.signal == "LONG":
                            raw_pnl_pct = (exit_price - entry) / entry
                        else:
                            raw_pnl_pct = (entry - exit_price) / entry
                            
                        gross_pnl_usd = raw_pnl_pct * size * lev
                        pnl_percent = raw_pnl_pct * lev * 100
                        
                        # Calculate fees (entry + exit)
                        fees_usd = size * SIMULATED_FEE_RATE * 2  # Both entry and exit
                        net_pnl_usd = gross_pnl_usd - fees_usd
                        
                        # Update Trade
                        trade.exit_price = exit_price
                        trade.pnl_usd = round(net_pnl_usd, 2)
                        trade.pnl_percent = round(pnl_percent, 2)
                        trade.fees_usd = round(fees_usd, 2)
                        
                        duration = (datetime.utcnow() - trade.timestamp).total_seconds() / 60
                        trade.duration_minutes = round(duration, 1)
                        
                        session.add(trade)
                        print(f"[Shadow Mode] Closed Trade {trade.id} ({reason}): Net ${net_pnl_usd:.2f} (Fees: ${fees_usd:.2f})")
                        
                        # Get cumulative stats for notification
                        session.commit()  # Commit first so stats include this trade
                        stats = DSPyRepository.get_cumulative_stats()
                        
                        # NOTIFICATION WITH ALL STATS
                        await notify_shadow_trade_closed(
                            coin=trade.coin,
                            signal=trade.signal,
                            entry_price=trade.entry_price,
                            exit_price=exit_price,
                            pnl_usd=gross_pnl_usd,
                            pnl_pct=pnl_percent,
                            fees_usd=fees_usd,
                            reason=reason,
                            cumulative_pnl=stats.cumulative_pnl,
                            win_rate=stats.win_rate
                        )
            
            session.commit()

