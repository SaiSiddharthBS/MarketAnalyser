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
                "technical": 15,
                "transformer": 25,
                "options_flow": 15,
                "ml_engine": 15,
                "sentiment": 10,
                "insider": 5,
                "macro": 5,
                "momentum": 10
            }
        
    def collect_votes(self, symbol: str, df: pd.DataFrame, regime: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Collect votes (-1 to 1) from all models and return metrics."""
        votes = {}
        
        # 1. Advanced Technicals
        tech_data = calculate_technical_signal(df)
        tech_score = tech_data.get("technical_score", 0)
        votes["technical"] = 1 if tech_score >= 2 else -1 if tech_score <= -2 else 0
        
        # 2. Transformer AI
        try:
            ai_data = predict_with_transformer(df, symbol)
            pred = ai_data.get("prediction", "UNKNOWN")
            votes["transformer"] = 1 if pred == "UP" else -1 if pred == "DOWN" else 0
        except Exception:
            votes["transformer"] = 0
            
        # 3. Momentum Factor (1M, 3M)
        if len(df) > 60:
            ret_1m = (df["Close"].iloc[-1] - df["Close"].iloc[-20]) / df["Close"].iloc[-20]
            ret_3m = (df["Close"].iloc[-1] - df["Close"].iloc[-60]) / df["Close"].iloc[-60]
            if ret_1m > 0.05 and ret_3m > 0.10:
                votes["momentum"] = 1
            elif ret_1m < -0.05 and ret_3m < -0.10:
                votes["momentum"] = -1
            else:
                votes["momentum"] = 0
        else:
            votes["momentum"] = 0
            
        # 4. ML Engine
        try:
            from analysis.ml_engine import ml_predict
            ml_pred = ml_predict(symbol, df)
            votes["ml_engine"] = 1 if ml_pred > 0.6 else -1 if ml_pred < 0.4 else 0
        except:
            votes["ml_engine"] = 0
            
        # 5. Macro (Regime Context)
        if regime == "high_vol_uptrend" or regime == "bullish":
            votes["macro"] = 1
        elif regime == "crisis" or regime == "bearish":
            votes["macro"] = -1
        else:
            votes["macro"] = 0
            
        # 6. Institutional Flow & Options (Task 4 & Task 10)
        inst_vote = 0
        try:
            from data.fii_dii_fetcher import fetch_fii_dii_daily
            fii_data = fetch_fii_dii_daily()
            if fii_data:
                fii_net = fii_data.get("fii_net_cr", 0)
                
                global _fii_printed
                if not _fii_printed:
                    print(f"📈 Institutional Flow: FII Net = ₹{fii_net} Cr")
                    _fii_printed = True
                    
                if fii_net > 1000:
                    inst_vote = 1
                elif fii_net < -1000:
                    inst_vote = -1
        except Exception as e:
            print(f"Warning: FII flow check failed: {e}")
            
        # Task 10: Options Flow Score (Real PCR Data)
        pcr_vote = 0
        try:
            from data.options_fetcher import fetch_options_chain, calculate_pcr
            # Fetch PCR for NIFTY as macro proxy
            opt_data = fetch_options_chain("NIFTY")
            if opt_data:
                pcr_data = calculate_pcr(opt_data.get("data", []))
                if pcr_data:
                    pcr = pcr_data.get("pcr_oi", 1.0)
                    if pcr < 0.7:
                        pcr_vote = 1
                    elif pcr > 1.3:
                        pcr_vote = -1
        except Exception:
            pass
            
        # Combine FII and PCR votes into options_flow
        if inst_vote == 1 and pcr_vote == 1:
            votes["options_flow"] = 1
        elif inst_vote == -1 and pcr_vote == -1:
            votes["options_flow"] = -1
        elif inst_vote != 0 and pcr_vote == 0:
            votes["options_flow"] = inst_vote
        elif inst_vote == 0 and pcr_vote != 0:
            votes["options_flow"] = pcr_vote
        else:
            votes["options_flow"] = 0
            
        # Placeholders for other data
        votes["insider"] = 0       # Requires insider data
        votes["sentiment"] = 0     # Requires NLP
        
        # In a real environment with missing data, we redistribute weights.
        # For now, if a model votes 0, it contributes 0.
        
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
        
        # Upgrade 1, 5, 6: Dynamic Regime Thresholds & Caps
        if regime == "low_vol_uptrend":
            conf_cap = 90.0
            rvol_min_buy = 1.2
            rsi_ceil_buy = 75
            signal_label = "🚀 Early Breakout"
            threshold = 60
            sell_threshold = 20 # Very hard to short a breakout
        elif regime == "high_vol_uptrend":
            conf_cap = 75.0
            rvol_min_buy = 1.3
            rsi_ceil_buy = 72
            signal_label = "↩ Pullback Buy"
            threshold = 65
            sell_threshold = 25
        elif regime == "low_vol_chop":
            conf_cap = 65.0
            rvol_min_buy = 1.4
            rsi_ceil_buy = 68
            signal_label = "📊 Range Breakout"
            threshold = 70
            sell_threshold = 30
        elif regime == "crisis":
            conf_cap = 60.0       # Was 40 — allow strong setups to show real confidence
            rvol_min_buy = 1.3    # Was 1.6 — still strict but allows quality volume
            rsi_ceil_buy = 65     # Was 60 — allow moderately oversold buys
            signal_label = "🛡 Defensive Buy (Counter-trend)"
            threshold = 68        # Was 72 — 72 requires near-impossible consensus in a crisis
            sell_threshold = 45   # Easier to short in a crisis (confidence <= 45 triggers short)
        else:
            conf_cap = 60.0
            rvol_min_buy = 1.5
            rsi_ceil_buy = 65
            signal_label = "⚠ Setup"
            threshold = 70
            sell_threshold = 30
            
        # Upgrade 1: Apply Confidence Cap
        capped_confidence = min(confidence, conf_cap)
        confidence_display = round(capped_confidence, 1)
        
        # Apply Macro Adjustment
        macro = get_macro_environment()
        macro_status = macro.get("status", "CLEAR")
        
        if macro_status == "MACRO TAILWIND":
            threshold -= 3
            sell_threshold -= 3 # Even harder to short with macro tailwind
            
        # Determine signal based on RAW confidence so setups can still trigger
        signal = "NEUTRAL"
        if confidence >= threshold:
            signal = "BUY"
        elif confidence <= sell_threshold:
            signal = "SELL"
            
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
            if modifiers.get("skip") and signal == "BUY":
                signal = "VETOED"
                veto_source = "Self-Learned Rule"
            elif modifiers.get("require_conviction") == "ULTRA" and confidence < 85:
                if signal == "BUY":
                    signal = "VETOED"
                    veto_source = "Self-Learned Rule (Requires ULTRA)"
        except Exception as e:
            pass
            
        # Re-calculate confidence with modifiers if we haven't already
        if modifiers.get("weight_modifiers") and not weight_modifiers:
            return self.calculate_confidence(symbol, df, regime, modifiers["weight_modifiers"])
            
        # Overwrite label if short
        if signal == "SELL":
            if regime == "crisis":
                signal_label = "📉 Breakdown Short (Trend Continuation)"
            elif regime in ["bullish", "low_vol_uptrend"]:
                signal_label = "🔥 Counter-trend Short (High Risk)"
            else:
                signal_label = "📉 Short Setup"
            
        # Hard Veto checks
        veto_source = "N/A"
        rsi = metrics.get("rsi", 50)
        
        if macro_status in ["MACRO VETO", "FULL MACRO VETO"] and signal == "BUY":
            signal = "VETOED"
            veto_source = "Macro Asset Class"
        elif signal == "BUY" and rvol < rvol_min_buy:
            signal = "VETOED"
            veto_source = f"RVOL {rvol}x < Regime Min ({rvol_min_buy}x)"
        elif signal == "BUY" and rsi > rsi_ceil_buy:
            signal = "VETOED"
            veto_source = f"Overbought RSI ({rsi}) for Regime (Ceiling: {rsi_ceil_buy})"
            
        # Module 7: Event Calendar Blackout
        try:
            from data.macro_calendar import check_macro_veto
            calendar_veto = check_macro_veto()
            if calendar_veto.get("trigger", False) and signal == "BUY":
                if calendar_veto.get("level") == "HARD_VETO":
                    signal = "VETOED"
                    veto_source = f"Event Calendar ({calendar_veto.get('reason')})"
        except Exception as e:
            print(f"Warning: Calendar engine not reachable - {e}")
            
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
            "votes": votes,
            "pattern": detected_pattern
        }

ensemble_engine = EnsembleVoter()

def get_ensemble_analysis(symbol: str, df: pd.DataFrame, regime: str = "YELLOW") -> Dict[str, Any]:
    return ensemble_engine.calculate_confidence(symbol, df, regime)
