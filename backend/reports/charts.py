"""
Generates matplotlib charts for the War Room PDF.
"""
import matplotlib.pyplot as plt
import numpy as np
import os
from pathlib import Path

CHART_DIR = Path(__file__).parent / "charts"
CHART_DIR.mkdir(parents=True, exist_ok=True)

def generate_equity_curve(portfolio_data):
    """Generates an equity curve chart."""
    plt.figure(figsize=(10, 4))
    
    dates = [d.get("date") for d in portfolio_data]
    equity = [d.get("total_equity") for d in portfolio_data]
    nifty = [d.get("benchmark_nifty_return_pct", 0) for d in portfolio_data]
    
    if not dates:
        dates = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        equity = [1000000, 1005000, 1002000, 1010000, 1015000]
        nifty = [0, 0.2, -0.1, 0.5, 0.8]
        
    fig, ax1 = plt.subplots(figsize=(10, 4))
    
    color = 'tab:blue'
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Arena Equity (₹)', color=color)
    ax1.plot(dates, equity, color=color, linewidth=2, label="Arena Portfolio")
    ax1.tick_params(axis='y', labelcolor=color)
    
    ax2 = ax1.twinx()
    color = 'tab:gray'
    ax2.set_ylabel('Nifty Return %', color=color)
    ax2.plot(dates, nifty, color=color, linestyle='--', label="Nifty 50")
    ax2.tick_params(axis='y', labelcolor=color)
    
    plt.title("Arena Performance vs Nifty 50")
    fig.tight_layout()
    
    path = str(CHART_DIR / "equity_curve.png")
    plt.savefig(path)
    plt.close('all')
    return path

def generate_model_accuracy_bar(championship_data):
    """Generates a bar chart of model accuracy."""
    plt.figure(figsize=(8, 4))
    
    if not championship_data:
        models = ["Technical", "Transformer", "Options Flow"]
        accuracies = [65.0, 55.0, 70.0]
    else:
        models = [c["model"].replace("_", " ").title() for c in championship_data]
        accuracies = [c["accuracy"] for c in championship_data]
        
    # Sort
    models_accs = sorted(zip(models, accuracies), key=lambda x: x[1])
    models = [x[0] for x in models_accs]
    accuracies = [x[1] for x in models_accs]
    
    colors = ['#ef4444' if a < 50 else '#22c55e' for a in accuracies]
    
    plt.barh(models, accuracies, color=colors)
    plt.axvline(50, color='gray', linestyle='--', alpha=0.7)
    plt.title("Model Championship (Rolling 60-Day Win Rate %)")
    plt.xlabel("Accuracy %")
    plt.xlim(0, 100)
    plt.tight_layout()
    
    path = str(CHART_DIR / "model_bar.png")
    plt.savefig(path)
    plt.close('all')
    return path
