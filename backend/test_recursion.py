from arena.weight_evolver import get_regime_weights

print("Calling get_regime_weights...")
try:
    weights = get_regime_weights("unknown")
    print(weights)
except Exception as e:
    import traceback
    traceback.print_exc()

print("Done")
