from typing import Dict, Any
import pandas as pd
from .technical import calculate_technical_signal
from .transformer_engine import predict_with_transformer
from .macro import get_macro_environment

_fii_printed = False

class EnsembleVoter:
    """
    Antigravity Module 3: The 8-Model Ensemble
    Collects votes from 8 discrete models, checks correlation, and computes final confidence.
    """
    
    def __init__(self):
        self.weights = self._load_regime_weights("unknown")
        
    def _load_regime_weights(self, regime: str) -> dict:
        """Load regime-conditional weights from DB. Fall back to defaults."""
        try:
            from arena.weight_evolver import get_regime_weights
            return get_regime_weights(regime)
        except Exception as e:
            return {
                "technical": 8,
                "transformer": 15,
                "short_term_nn": 10,
                "options_flow": 10,
                "fno_bias": 10,
                "ml_engine": 10,
                "sentiment": 10,
                "insider": 5,
                "macro": 5,
                "momentum": 8,
                "value": 1,
                "quality": 6,
                "earnings": 2
            }
        
    def collect_votes(self, symbol: str, df: pd.DataFrame, regime: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Collect continuous votes (-1.0 to +1.0) from all models and return metrics.
        
        V6 Upgrade: Each model returns a continuous score instead of ternary -1/0/+1.
        This produces scores like 61.4, 58.8, 63.2 instead of 55, 57.5, 60.
        """
        votes = {}
        
        # 1. Advanced Technicals — map tech_score (range ~-10 to +10) to [-1, +1]
        tech_data = calculate_technical_signal(df)
        tech_score = tech_data.get("technical_score", 0)
        # Max practical score is ~10, so divide by 8 for good spread
        votes["technical"] = max(-1.0, min(1.0, tech_score / 8.0))
        
        # 2. Transformer AI — use probability if available, else direction
        try:
            ai_data = predict_with_transformer(df, symbol)
            pred = ai_data.get("prediction", "UNKNOWN")
            prob = ai_data.get("probability", 0.5)
            if pred == "UP":
                votes["transformer"] = min(1.0, 0.3 + (prob - 0.5) * 2.0)
            elif pred == "DOWN":
                votes["transformer"] = max(-1.0, -0.3 - (0.5 - prob) * 2.0)
            else:
                votes["transformer"] = 0.0
        except Exception:
            votes["transformer"] = 0.0
            
        # 3. Momentum Factor — continuous blended score from 1M and 3M returns
        if len(df) > 60:
            ret_1m = (df["Close"].iloc[-1] - df["Close"].iloc[-20]) / df["Close"].iloc[-20]
            ret_3m = (df["Close"].iloc[-1] - df["Close"].iloc[-60]) / df["Close"].iloc[-60]
            # Blend: 60% weight on 1M, 40% on 3M, scale so ±10% return = ±1.0
            mom_score = (ret_1m * 0.6 + ret_3m * 0.4) * 10.0
            votes["momentum"] = max(-1.0, min(1.0, mom_score))
        else:
            votes["momentum"] = 0.0
            
        # 4. ML Engine — use raw probability directly
        try:
            from analysis.ml_engine import ml_predict
            ml_pred = ml_predict(symbol, df)
            # ml_pred is 0.0 to 1.0, map to -1.0 to +1.0
            votes["ml_engine"] = max(-1.0, min(1.0, (ml_pred - 0.5) * 2.0))
        except:
            votes["ml_engine"] = 0.0
            
        # 5. Macro (Regime Context) — continuous regime scoring
        regime_scores = {
            "low_vol_uptrend": 0.8,
            "bullish": 0.8,
            "high_vol_uptrend": 0.5,
            "recovery": 0.3,
            "high_vol_chop": 0.1,      # Slight positive — dip buying
            "low_vol_chop": -0.2,
            "distribution": -0.4,
            "bearish": -0.7,
            "crisis": -0.9,
        }
        votes["macro"] = regime_scores.get(regime, 0.0)
            
        # 6. Institutional Flow & Options — continuous FII + PCR blend
        inst_score = 0.0
        try:
            from data.fii_dii_fetcher import fetch_fii_dii_daily
            fii_data = fetch_fii_dii_daily()
            if fii_data:
                fii_net = fii_data.get("fii_net_cr", 0)
                
                global _fii_printed
                if not _fii_printed:
                    print(f"📈 Institutional Flow: FII Net = ₹{fii_net} Cr")
                    _fii_printed = True
                    
                # Scale: ₹3000 Cr net = ±1.0
                inst_score = max(-1.0, min(1.0, fii_net / 3000.0))
        except Exception as e:
            print(f"Warning: FII flow check failed: {e}")
            
        # Options Flow (PCR)
        pcr_score = 0.0
        try:
            from data.options_fetcher import fetch_options_chain, calculate_pcr
            opt_data = fetch_options_chain("NIFTY")
            if opt_data:
                pcr_data = calculate_pcr(opt_data.get("data", []))
                if pcr_data:
                    pcr = pcr_data.get("pcr_oi", 1.0)
                    # PCR < 0.7 = bullish, > 1.3 = bearish. Map 0.7-1.3 to +1 to -1
                    pcr_score = max(-1.0, min(1.0, (1.0 - pcr) * 1.67))
        except Exception:
            pass
            
        # Blend FII (60%) and PCR (40%)
        votes["options_flow"] = inst_score * 0.6 + pcr_score * 0.4
            
        # 9. F&O Signal Bias — use raw directional bias (already -1 to +1 range)
        votes["fno_bias"] = 0.0
        try:
            from analysis.fno_signals import get_option_chain_signals
            fno_data = get_option_chain_signals(symbol)
            if fno_data.get("available"):
                bias = fno_data.get("directional_bias", 0.0)
                votes["fno_bias"] = max(-1.0, min(1.0, bias))
        except Exception as e:
            print(f"Warning: FNO signal check failed for {symbol}: {e}")
            
        # 9.5 Short-Term NN (LSTM Equivalent for 1-3 days)
        votes["short_term_nn"] = 0.0
        try:
            from analysis.lstm_engine import nn_predict
            votes["short_term_nn"] = nn_predict(symbol)
        except Exception:
            pass
            
        # Placeholders for other data (still stubs — honest about it)
        votes["insider"] = 0.0      # Requires insider data
        votes["sentiment"] = 0.0    # Requires NLP
        
        # 10, 11, 12. Factor Models (Phase 2 Upgrade)
        try:
            from analysis.factors import get_all_factors
            factors = get_all_factors(symbol)
            votes["value"] = max(-1.0, min(1.0, factors["value"]["score"] / 100.0))
            votes["quality"] = max(-1.0, min(1.0, factors["quality"]["score"] / 100.0))
            votes["earnings"] = max(-1.0, min(1.0, factors["earnings"]["score"] / 100.0))
        except Exception:
            votes["value"] = 0.0
            votes["quality"] = 0.0
            votes["earnings"] = 0.0
            
        # 13. Relative Strength Ranking (Sprint 2 Upgrade)
        try:
            from analysis.relative_strength import get_relative_strength
            rs_data = get_relative_strength(symbol)
            # Map percentile (0-100) to (-1.0 to 1.0)
            votes["relative_strength"] = max(-1.0, min(1.0, (rs_data["rs_percentile"] - 50) / 50.0))
        except Exception as e:
            votes["relative_strength"] = 0.0
        # 14. Smart Money Concepts (Dark Pool / Volume Profile)
        votes["smart_money"] = 0.0
        try:
            from analysis.smart_money import check_smart_money_signal
            sm_data = check_smart_money_signal(f"{symbol}.NS")
            if sm_data["signal"] == "STRONG_BUY":
                votes["smart_money"] = 1.0
            elif sm_data["signal"] == "BUY":
                votes["smart_money"] = 0.5
            elif sm_data["signal"] == "STRONG_SELL":
                votes["smart_money"] = -1.0
            elif sm_data["signal"] == "SELL":
                votes["smart_money"] = -0.5
        except Exception as e:
            pass
            
        # 15. Statistical Arbitrage (Pairs Trading Valuation)
        votes["stat_arb"] = 0.0
        try:
            from analysis.stat_arb import get_stat_arb_signal
            sa_data = get_stat_arb_signal(f"{symbol}.NS")
            if sa_data["signal"] == "STRONG_BUY":
                votes["stat_arb"] = 1.0
            elif sa_data["signal"] == "BUY":
                votes["stat_arb"] = 0.5
            elif sa_data["signal"] == "STRONG_SELL":
                votes["stat_arb"] = -1.0
            elif sa_data["signal"] == "SELL":
                votes["stat_arb"] = -0.5
        except Exception as e:
            pass
        
        return votes, tech_data.get("metrics", {})
        
    def calculate_confidence(self, symbol: str, df: pd.DataFrame, regime: str, weight_modifiers: Dict[str, float] = None) -> Dict[str, Any]:
        votes, metrics = self.collect_votes(symbol, df, regime)
        
        current_weights = self._load_regime_weights(regime)
        if weight_modifiers:
            for m, factor in weight_modifiers.items():
                if m in current_weights:
                    current_weights[m] *= factor
        
        raw_score = 0
        for model, vote in votes.items():
            weight = current_weights.get(model, 10)
            raw_score += vote * weight
            
        from analysis.patterns import detect_patterns
        detected_pattern = detect_patterns(df)
        if detected_pattern.get("confidence", 0) > 70:
            if detected_pattern.get("direction") == "bullish":
                raw_score += 5
            elif detected_pattern.get("direction") == "bearish":
                raw_score -= 5
                
        # Module 13: Sector Rotation Boost/Penalty
        try:
            from analysis.sector_rotation import get_sector_for_symbol
            sector_info = get_sector_for_symbol(symbol)
            if sector_info["classification"] == "🔥 Strong":
                raw_score += 8  # Huge boost for leading sectors
            elif sector_info["classification"] == "↗ Improving":
                raw_score += 4
            elif sector_info["classification"] in ["↘ Weakening", "❄ Avoid"]:
                raw_score -= 8  # Huge penalty for laggards
                
            if sector_info["is_best_in_class"]:
                raw_score += 5  # Extra boost for being the strongest stock in its sector
        except Exception:
            pass
                
        # Normalise to Confidence: (Raw_Score + 100) / 200
        confidence = (raw_score + 100) / 200 * 100
        
        # Apply Confidence Calibration
        try:
            from arena.calibrator import ConfidenceCalibrator
            calib = ConfidenceCalibrator()
            factor = calib.get_calibration_factor(confidence)
            confidence = confidence * factor
        except Exception:
            pass
        
        # Apply RVOL Penalty (Fix 5)
        rvol = metrics.get("rvol", 1.0)
        if rvol < 0.8:
            confidence -= 10 # Reduce score by 10 points for low volume
        
        # Upgrade 1, 5, 6: Dynamic Regime Thresholds & Caps (V6: Full 7-regime table)
        regime_params = {
            "low_vol_uptrend": {"conf_cap": 90.0, "rvol_min": 1.2, "rsi_ceil": 75, "label": "🚀 Early Breakout", "threshold": 55, "sell_threshold": 20},
            "bullish":         {"conf_cap": 90.0, "rvol_min": 1.2, "rsi_ceil": 75, "label": "🚀 Trend Continuation", "threshold": 55, "sell_threshold": 20},
            "recovery":        {"conf_cap": 75.0, "rvol_min": 1.3, "rsi_ceil": 72, "label": "📈 Recovery Play", "threshold": 58, "sell_threshold": 25},
            "high_vol_uptrend":{"conf_cap": 75.0, "rvol_min": 1.3, "rsi_ceil": 72, "label": "↩ Pullback Buy", "threshold": 58, "sell_threshold": 25},
            "high_vol_chop":   {"conf_cap": 65.0, "rvol_min": 1.4, "rsi_ceil": 68, "label": "💎 Dip Opportunity", "threshold": 60, "sell_threshold": 30},
            "low_vol_chop":    {"conf_cap": 60.0, "rvol_min": 1.4, "rsi_ceil": 65, "label": "📊 Range Breakout", "threshold": 62, "sell_threshold": 30},
            "distribution":    {"conf_cap": 50.0, "rvol_min": 1.5, "rsi_ceil": 62, "label": "⚠ Distribution Setup", "threshold": 65, "sell_threshold": 35},
            "bearish":         {"conf_cap": 45.0, "rvol_min": 1.5, "rsi_ceil": 60, "label": "🛡 Counter-trend Buy", "threshold": 68, "sell_threshold": 40},
            "crisis":          {"conf_cap": 40.0, "rvol_min": 1.6, "rsi_ceil": 58, "label": "🛡 Defensive Buy (Crisis)", "threshold": 70, "sell_threshold": 45},
        }
        params = regime_params.get(regime, {"conf_cap": 60.0, "rvol_min": 1.4, "rsi_ceil": 65, "label": "⚠ Setup", "threshold": 62, "sell_threshold": 30})
        conf_cap = params["conf_cap"]
        rvol_min_buy = params["rvol_min"]
        rsi_ceil_buy = params["rsi_ceil"]
        signal_label = params["label"]
        threshold = params["threshold"]
        sell_threshold = params["sell_threshold"]
            
        # Upgrade 1: Apply Confidence Cap
        capped_confidence = min(confidence, conf_cap)
        confidence_display = round(capped_confidence, 1)
        
        # Apply Macro Adjustment
        macro = get_macro_environment()
        macro_status = macro.get("status", "CLEAR")
        
        if macro_status == "MACRO TAILWIND":
            threshold -= 3
            sell_threshold -= 3 # Even harder to short with macro tailwind
            
        # Apply Overnight Global Intelligence Adjustment
        try:
            from analysis.overnight_intel import get_overnight_bias
            overnight = get_overnight_bias()
            overnight_score = overnight.get("score", 0)
            overnight_adj = overnight.get("regime_adjustment", "no_change")
            
            if overnight_adj == "lower_thresholds":
                threshold -= 3  # Global tailwind: easier to enter
            elif overnight_adj == "slightly_lower_thresholds":
                threshold -= 1
            elif overnight_adj == "raise_thresholds":
                threshold += 5  # Global headwind: much harder to enter
                sell_threshold -= 5  # But easier to short
            elif overnight_adj == "slightly_raise_thresholds":
                threshold += 2
                sell_threshold -= 2
        except Exception:
            pass  # Graceful: if overnight scan fails, use defaults
            
        # Determine signal based on RAW confidence so setups can still trigger
        if confidence >= 80:
            signal = "STRONG_BUY"
            signal_label = "🚀 Strong Buy"
        elif confidence >= 60:
            signal = "BUY"
            # Keep the regime-specific label for BUY (e.g., "Early Breakout", "Pullback Buy")
        elif confidence <= 20:
            signal = "STRONG_SELL"
            signal_label = "📉 Strong Sell"
        elif confidence <= 40:
            signal = "SELL"
            signal_label = "📉 Short Setup"
        elif confidence >= 45:
            signal = "WATCH"
            signal_label = "🟡 Watch (Forming)"
        elif confidence <= 35:
            signal = "WEAKENING"
            signal_label = "🟠 Weakening"
        else:
            signal = "NEUTRAL"
            signal_label = "⚪ Neutral"
            
        # Apply learned rules from Phase 2
        modifiers = {}
        try:
            from arena.self_learner import apply_learned_rules
            from datetime import datetime
            from analysis.regime import detect_market_regime
            
            vix = detect_market_regime().get("vix_level", 0)
            
            signal_context = {
                "regime": regime,
                "day_of_week": datetime.now().strftime("%A"),
                "vix_level": vix,
                "conviction": "ULTRA" if confidence >= 85 else ("HIGH" if confidence >= 75 else "MODERATE")
            }
            
            modifiers = apply_learned_rules(signal_context)
            if modifiers.get("skip") and signal in ["BUY", "STRONG_BUY"]:
                signal = "VETOED"
                veto_source = "Self-Learned Rule"
            elif modifiers.get("require_conviction") == "ULTRA" and confidence < 85:
                if signal in ["BUY", "STRONG_BUY"]:
                    signal = "VETOED"
                    veto_source = "Self-Learned Rule (Requires ULTRA)"
        except Exception as e:
            pass
            
        # Re-calculate confidence with modifiers if we haven't already
        if modifiers.get("weight_modifiers") and not weight_modifiers:
            return self.calculate_confidence(symbol, df, regime, modifiers["weight_modifiers"])
            
        # Overwrite label if short
        if signal in ["SELL", "STRONG_SELL"]:
            if regime == "crisis":
                signal_label = "📉 Breakdown Short (Trend Continuation)"
            elif regime in ["bullish", "low_vol_uptrend"]:
                signal_label = "🔥 Counter-trend Short (High Risk)"
            else:
                signal_label = "📉 Short Setup"
            
        # Hard Veto checks
        veto_source = "N/A"
        rsi = metrics.get("rsi", 50)
        
        if macro_status in ["MACRO VETO", "FULL MACRO VETO"] and signal in ["BUY", "STRONG_BUY"]:
            signal = "VETOED"
            veto_source = "Macro Asset Class"
        elif signal in ["BUY", "STRONG_BUY"] and rvol < rvol_min_buy:
            signal = "VETOED"
            veto_source = f"RVOL {rvol}x < Regime Min ({rvol_min_buy}x)"
        elif signal in ["BUY", "STRONG_BUY"] and rsi > rsi_ceil_buy:
            signal = "VETOED"
            veto_source = f"Overbought RSI ({rsi}) for Regime (Ceiling: {rsi_ceil_buy})"
            
        # Module 7: Event Calendar Blackout
        try:
            from data.macro_calendar import check_macro_veto
            calendar_veto = check_macro_veto()
            if calendar_veto.get("trigger", False) and signal in ["BUY", "STRONG_BUY"]:
                if calendar_veto.get("level") == "HARD_VETO":
                    signal = "VETOED"
                    veto_source = f"Event Calendar ({calendar_veto.get('reason')})"
        except Exception as e:
            print(f"Warning: Calendar engine not reachable - {e}")
            
        # Module 13: Relative Strength Veto & Boost
        try:
            from analysis.relative_strength import get_relative_strength
            rs_data = get_relative_strength(symbol)
            if rs_data["rs_percentile"] <= 10.0 and signal in ["BUY", "STRONG_BUY"]:
                signal = "VETOED"
                veto_source = f"Bottom Decile Relative Strength ({rs_data['rs_percentile']}th %ile)"
            elif rs_data["rs_percentile"] >= 90.0 and signal == "BUY":
                signal = "STRONG_BUY"
                signal_label = f"🔥 Momentum Leader Buy ({rs_data['rs_percentile']}th %ile)"
        except Exception:
            pass
            
        # Timeframe Classification (Sprint 1)
        timeframe_data = {}
        if signal in ["BUY", "STRONG_BUY"]:
            try:
                from analysis.timeframe_classifier import classify_timeframe
                timeframe_data = classify_timeframe(df, symbol)
            except Exception as e:
                timeframe_data = {
                    "holding_class": "SWING", 
                    "expected_days": 10, 
                    "confidence": 50.0,
                    "reason": "Classifier fallback"
                }
            
        return {
            "symbol": symbol,
            "raw_score": raw_score,
            "confidence": confidence_display,
            "confidence_cap": conf_cap,
            "threshold": threshold,
            "signal": signal,
            "signal_label": signal_label,
            "veto_source": veto_source,
            "macro_status": macro_status,
            "timeframe": timeframe_data,
            "votes": votes,
            "pattern": detected_pattern
        }

ensemble_engine = EnsembleVoter()

def get_ensemble_analysis(symbol: str, df: pd.DataFrame, regime: str = "YELLOW") -> Dict[str, Any]:
    return ensemble_engine.calculate_confidence(symbol, df, regime)
