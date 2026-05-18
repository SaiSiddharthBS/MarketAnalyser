"""
Agent Alpha v4.0 - Confidence Calibrator
Tracks predicted vs actual win rates to prevent overconfidence.
"""
import logging
import database as db

logger = logging.getLogger(__name__)

class ConfidenceCalibrator:
    def __init__(self):
        pass
        
    def _get_bucket(self, confidence: float) -> str:
        if confidence < 60: return "50-60"
        if confidence < 70: return "60-70"
        if confidence < 80: return "70-80"
        if confidence < 90: return "80-90"
        return "90-100"

    def log_outcome(self, confidence: float, is_win: bool):
        bucket = self._get_bucket(confidence)
        
        # Check if bucket exists
        res = db.db_execute("SELECT * FROM calibration_log WHERE confidence_bucket = ?", (bucket,))
        if res:
            wins = (res[0]["actual_win_rate"] * res[0]["sample_size"]) if res[0]["actual_win_rate"] else 0
            new_sample_size = res[0]["sample_size"] + 1
            new_wins = wins + (1 if is_win else 0)
            new_win_rate = new_wins / new_sample_size
            
            pred_rate = res[0]["predicted_win_rate"]
            calib_factor = new_win_rate / pred_rate if pred_rate > 0 else 1.0
            
            db.db_execute("""
                UPDATE calibration_log 
                SET actual_win_rate = ?, sample_size = ?, calibration_factor = ?
                WHERE confidence_bucket = ?
            """, (new_win_rate, new_sample_size, calib_factor, bucket))
        else:
            # Initialize bucket
            pred_rate = float(bucket.split("-")[0]) / 100.0 + 0.05 # e.g. 50-60 -> 0.55
            act_rate = 1.0 if is_win else 0.0
            db.db_execute("""
                INSERT INTO calibration_log (confidence_bucket, predicted_win_rate, actual_win_rate, sample_size, calibration_factor)
                VALUES (?, ?, ?, ?, ?)
            """, (bucket, pred_rate, act_rate, 1, act_rate / pred_rate))

    def get_calibration_factor(self, confidence: float) -> float:
        bucket = self._get_bucket(confidence)
        res = db.db_execute("SELECT calibration_factor, sample_size FROM calibration_log WHERE confidence_bucket = ?", (bucket,))
        if res and res[0]["sample_size"] >= 10:
            return float(res[0]["calibration_factor"])
        return 1.0

