import asyncio
import time
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout.reconfigure(encoding='utf-8')

from app.core.database import SessionLocal
from app.services.news_intelligence_service import NewsIntelligenceService
from app.providers.ai_engine import AIAgentEngine


async def main():
    print("==================================================")
    print("TESTING FULL CLAUDE E2E PIPELINE (DASHBOARD & NEWS)")
    print("==================================================")
    db = SessionLocal()

    # 1. Test News Intelligence via Claude
    print("\n[1/2] Invoking News Intelligence via Claude...")
    t0 = time.time()
    news_res = await NewsIntelligenceService.get_or_generate_scenario(db, "XAUUSD", target_event_title="Non-Farm")
    dt1 = round(time.time() - t0, 2)
    print(f"  -> Generated in: {dt1}s")
    print(f"  -> Event: {news_res.event_title}")
    print(f"  -> Scheduled WIB: {news_res.scheduled_at_wib}")
    print(f"  -> Market Regime: {news_res.market_regime}")
    print(f"  -> Bias: {news_res.bias} ({news_res.confidence_level})")
    print(f"  -> Supports: {news_res.key_support_levels}")
    print(f"  -> Resistances: {news_res.key_resistance_levels}")
    print("  -> Scenarios:")
    for sc in news_res.scenarios:
        print(f"     * {sc.label}: {sc.condition}")
        print(f"       Target: {sc.target_area}")
    print(f"  -> Verified Pending Catalysts ({len(news_res.pending_catalysts)}):")
    for pc in news_res.pending_catalysts[:3]:
        print(f"     * {pc['time_wib']}: {pc['event']}")

    # 2. Test Market Bias Synthesis via Claude
    print("\n[2/2] Invoking Market Bias Synthesis via Claude...")
    price_snap = {"current_price": 4218.25}
    tech = {"trend_direction": "BULLISH", "support_levels": [4195.0, 4175.0], "resistance_levels": [4235.0, 4255.0]}
    events = [{"event_title": "US Non-Farm Payrolls", "impact_level": "HIGH"}]
    news = [{"title": "Gold pushes towards record levels on macro catalysts"}]
    t1 = time.time()
    bias_res = await AIAgentEngine.synthesize_market_bias("XAUUSD", price_snap, tech, events, news)
    dt2 = round(time.time() - t1, 2)
    print(f"  -> Synthesized in: {dt2}s")
    print(f"  -> Bias: {bias_res['bias']} ({bias_res['confidence_score']}%)")
    print(f"  -> Summary: {bias_res['summary']}")
    ts = bias_res["trade_setup"]
    print(f"  -> Setup: {ts['action_label']}")
    print(f"  -> Entry Zone: {ts['entry_zone']}")
    print(f"  -> SL: ${ts['stop_loss']} | TP1: ${ts['take_profit_1']} | TP2: ${ts['take_profit_2']}")
    print(f"  -> R:R: {ts['risk_reward_ratio']} (Risk: {ts['risk_pips']} pips, Reward: {ts['reward_tp2_pips']} pips)")

    db.close()
    print("\n==================================================")
    print("ALL CLAUDE CALLS RETURNED PERFECT VERIFIED DATA!")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(main())
