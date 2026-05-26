import sys
sys.path.append("backend")
from analysis.regime import get_smoothed_market_regime
print(get_smoothed_market_regime())
