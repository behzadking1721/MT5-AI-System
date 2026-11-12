"""
End-to-end local pipeline demo (no MT5/MCP, no real orders):
  ORB signal -> RiskManager -> TradeProposal -> ExecutionGateway (prepare+simulate)
Run:  set PYTHONPATH=. && python scripts/pipeline_demo.py
"""
from datetime import datetime, timedelta

from core.permission_gateway.gateway import PermissionContext
from modules.risk_manager.manager import RiskInput, RiskLimits, RiskManager
from modules.strategy_lab import Bar, DailyStats, ORBConfig, analyze_orb
from modules.trade_manager import ExecutionGateway, TradeProposal


def main():
    start = datetime(2024, 1, 2, 9, 30)
    bars = [
        Bar(start + timedelta(minutes=0), open=100.00, high=100.80, low=99.90, close=100.20, volume=120000),
        Bar(start + timedelta(minutes=1), open=100.20, high=100.60, low=100.10, close=100.40, volume=90000),
        Bar(start + timedelta(minutes=2), open=100.40, high=100.90, low=100.30, close=100.70, volume=110000),
        Bar(start + timedelta(minutes=3), open=100.70, high=101.00, low=100.50, close=100.80, volume=95000),
        Bar(start + timedelta(minutes=4), open=100.80, high=101.20, low=100.60, close=101.10, volume=85000),
    ]
    stats = DailyStats(atr14=2.50, avg_volume14=2_000_000, prev_or_volumes=[250000] * 14)
    signal = analyze_orb("SAMPLE", bars, start, stats, ORBConfig())
    print("1) ORB:", signal.direction.value, "eligible=", signal.eligible, "entry=", signal.entry_price, "sl=", signal.stop_loss)

    # 2) Risk (example: $10k equity, 0.5% risk, symbol contract inputs)
    rm = RiskManager()
    risk_in = RiskInput(
        proposal_id="demo-proposal", symbol="SAMPLE", side="buy",
        entry_price=signal.entry_price, stop_loss=signal.stop_loss,
        account_equity=10000.0, risk_percent=0.5,
        tick_value=1.0, tick_size=0.01, volume_step=0.01, volume_min=0.01, volume_max=100.0,
    )
    decision = rm.evaluate(risk_in, RiskLimits(max_risk_per_trade_pct=0.5))
    print("2) Risk:", "approved=", decision.approved, "volume=", decision.volume, "reasons=", decision.reasons)

    # 3) Trade proposal + execution gateway (SIMULATED, requires confirmation)
    proposal = TradeProposal.from_orb_signal(signal)
    # align ids for demo
    from dataclasses import replace
    proposal = replace(proposal, proposal_id=risk_in.proposal_id)
    gw = ExecutionGateway()
    ctx = PermissionContext(level="L4", trading_enabled=True, live_trading_enabled=False)
    req, rej, reason = gw.prepare_request(proposal, decision, human_confirmation_id="CONFIRM-DEMO-001", ctx=ctx)
    print("3) Prepare:", reason)
    if req:
        sim = gw.simulate_execute(req, proposal)
        print("4) Result:", sim.status, sim.server_message)
    else:
        print("4) Rejected:", rej.server_message if rej else "")


if __name__ == "__main__":
    main()
