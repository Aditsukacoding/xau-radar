import sys
import os
import asyncio

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.providers.ai_engine import AIAgentEngine
from app.services.news_intelligence_service import NewsIntelligenceService


async def test_guardrails():
    print("==================================================")
    print("TESTING ANTI-HALLUCINATION & DATA SANITIZATION")
    print("==================================================")

    curr_price = 4210.50

    # TEST CASE 1: Inverted BUY trade setup (LLM placed SL above entry, TP below entry)
    hallucinated_buy = {
        "bias": "BULLISH",
        "confidence_score": 85,
        "summary": "Pasar sangat bullish",
        "trade_setup": {
            "action": "BUY",
            "entry_price": 2040.0,  # Hallucinated outdated 2023 price!
            "stop_loss": 4230.0,    # Inverted SL (above entry)!
            "take_profit_1": 4180.0,# Inverted TP1 (below entry)!
            "take_profit_2": 4150.0,# Inverted TP2 (below TP1)!
        },
        "key_levels": {
            "support": [4250.0, 4300.0],   # Inverted support (above price)!
            "resistance": [4100.0, 4050.0] # Inverted resistance (below price)!
        }
    }

    sanitized_buy = AIAgentEngine._sanitize_and_validate_trade_setup(hallucinated_buy, curr_price)
    setup = sanitized_buy["trade_setup"]

    print("\n[TEST 1: Inverted BUY & Hallucinated 2023 Price]")
    print(f"  -> Live Price: ${curr_price}")
    print(f"  -> Sanitized Entry: ${setup['entry_price']} (Zone: {setup['entry_zone']})")
    print(f"  -> Sanitized SL: ${setup['stop_loss']}")
    print(f"  -> Sanitized TP1: ${setup['take_profit_1']}")
    print(f"  -> Sanitized TP2: ${setup['take_profit_2']}")
    print(f"  -> R:R: {setup['risk_reward_ratio']} | Risk: {setup['risk_pips']} pips | Reward TP2: {setup['reward_tp2_pips']} pips")
    print(f"  -> Sanitized Supports: {sanitized_buy['key_levels']['support']}")
    print(f"  -> Sanitized Resistances: {sanitized_buy['key_levels']['resistance']}")

    # Assertions for BUY trading physics
    assert setup["entry_price"] > 4000.0, "Entry price not pegged to current price"
    assert setup["stop_loss"] < setup["entry_price"], f"SL ({setup['stop_loss']}) must be < Entry ({setup['entry_price']})"
    assert setup["take_profit_1"] > setup["entry_price"], f"TP1 ({setup['take_profit_1']}) must be > Entry ({setup['entry_price']})"
    assert setup["take_profit_2"] > setup["take_profit_1"], f"TP2 ({setup['take_profit_2']}) must be > TP1 ({setup['take_profit_1']})"
    assert all(s < curr_price for s in sanitized_buy["key_levels"]["support"]), "Supports must be below current price"
    assert all(r > curr_price for r in sanitized_buy["key_levels"]["resistance"]), "Resistances must be above current price"
    print("  -> TEST 1 PASSED: Zero-hallucination guardrail fixed all inverted levels!")

    # TEST CASE 2: Inverted SELL trade setup (LLM placed SL below entry, TP above entry)
    hallucinated_sell = {
        "bias": "BEARISH",
        "confidence_score": 78,
        "trade_setup": {
            "action": "SELL",
            "entry_price": 4210.0,
            "stop_loss": 4180.0,     # Inverted SL (below entry for SELL)!
            "take_profit_1": 4250.0, # Inverted TP (above entry for SELL)!
            "take_profit_2": 4280.0,
        }
    }

    sanitized_sell = AIAgentEngine._sanitize_and_validate_trade_setup(hallucinated_sell, curr_price)
    setup_s = sanitized_sell["trade_setup"]

    print("\n[TEST 2: Inverted SELL Setup]")
    print(f"  -> Sanitized Entry: ${setup_s['entry_price']}")
    print(f"  -> Sanitized SL: ${setup_s['stop_loss']}")
    print(f"  -> Sanitized TP1: ${setup_s['take_profit_1']}")
    print(f"  -> Sanitized TP2: ${setup_s['take_profit_2']}")
    print(f"  -> R:R: {setup_s['risk_reward_ratio']} | Risk: {setup_s['risk_pips']} pips | Reward TP2: {setup_s['reward_tp2_pips']} pips")

    # Assertions for SELL trading physics
    assert setup_s["stop_loss"] > setup_s["entry_price"], f"SL ({setup_s['stop_loss']}) must be > Entry ({setup_s['entry_price']})"
    assert setup_s["take_profit_1"] < setup_s["entry_price"], f"TP1 ({setup_s['take_profit_1']}) must be < Entry ({setup_s['entry_price']})"
    assert setup_s["take_profit_2"] < setup_s["take_profit_1"], f"TP2 ({setup_s['take_profit_2']}) must be < TP1 ({setup_s['take_profit_1']})"
    print("  -> TEST 2 PASSED: SELL physics strictly enforced!")

    # TEST CASE 3: News Intelligence Service End-to-End
    print("\n[TEST 3: News Intelligence Service End-to-End]")
    db = SessionLocal()
    resp = await NewsIntelligenceService.get_or_generate_scenario(db, symbol="XAUUSD", target_event_title="Non-Farm")

    print(f"  -> Event: {resp.event_title} ({resp.scheduled_at_wib})")
    print(f"  -> Market Regime: {resp.market_regime}")
    print(f"  -> Supports: {resp.key_support_levels} | Resistances: {resp.key_resistance_levels}")
    print(f"  -> Bias: {resp.bias} (Keyakinan: {resp.confidence_level})")
    print(f"  -> Scenarios count: {len(resp.scenarios)}")
    for sc in resp.scenarios:
        print(f"     * {sc.label}: {sc.condition} -> Target: {sc.target_area}")
    print(f"  -> Real Pending Catalysts count: {len(resp.pending_catalysts)}")
    for pc in resp.pending_catalysts[:3]:
        print(f"     * {pc['time_wib']}: {pc['event']}")

    assert len(resp.scenarios) == 3, "Expected exactly 3 scenarios"
    assert len(resp.pending_catalysts) > 0, "Expected real pending catalysts"
    assert resp.key_support_levels[0] < resp.key_resistance_levels[0], "Support must be < Resistance"
    print("  -> TEST 3 PASSED: News Intelligence perfectly structured and data-anchored!")

    db.close()
    print("\n==================================================")
    print("ALL ANTI-HALLUCINATION GUARDRAILS VERIFIED 100%!")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(test_guardrails())
