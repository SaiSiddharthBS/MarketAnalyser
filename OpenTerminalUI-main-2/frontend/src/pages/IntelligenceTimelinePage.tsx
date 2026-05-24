import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { IntelligenceTimeline } from "../components/dashboard/IntelligenceTimeline";
import { TerminalInput } from "../components/terminal/TerminalInput";
import { TerminalButton } from "../components/terminal/TerminalButton";
import { useSettingsStore } from "../store/settingsStore";
import { useStockStore } from "../store/stockStore";
import { normalizeTicker } from "../utils/ticker";

export function IntelligenceTimelinePage() {
  const navigate = useNavigate();
  const selectedMarket = useSettingsStore((state) => state.selectedMarket);
  const storeTicker = useStockStore((state) => state.ticker);
  const [draft, setDraft] = useState(storeTicker || "AAPL");
  const [symbol, setSymbol] = useState(normalizeTicker(storeTicker || "AAPL"));
  const symbols = useMemo(() => [symbol].filter(Boolean), [symbol]);

  return (
    <div className="h-full min-h-0 overflow-auto bg-terminal-bg p-3 font-mono md:p-4">
      <div className="mb-3 rounded-sm border border-terminal-border bg-terminal-panel/80 p-3">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="ot-type-panel-title uppercase tracking-[0.16em] text-terminal-accent">Intelligence</p>
            <h1 className="mt-1 text-xl font-semibold uppercase tracking-[0.12em] text-terminal-text">Unified Timeline</h1>
            <p className="mt-1 max-w-3xl text-sm text-terminal-muted">
              Market-aware US and India feed for news, alerts, corporate events, insider flow, earnings, model signals, and validated runs.
            </p>
          </div>
          <form
            className="grid gap-2 sm:grid-cols-[minmax(12rem,1fr)_auto_auto]"
            onSubmit={(event) => {
              event.preventDefault();
              setSymbol(normalizeTicker(draft));
            }}
          >
            <TerminalInput value={draft} onChange={(event) => setDraft(event.target.value.toUpperCase())} placeholder="Ticker" />
            <TerminalButton type="submit" variant="accent">Load</TerminalButton>
            <TerminalButton type="button" onClick={() => navigate("/equity/alerts")}>Add Alert</TerminalButton>
          </form>
        </div>
      </div>
      <IntelligenceTimeline
        market={selectedMarket}
        symbol={symbol}
        symbols={symbols}
        limit={40}
        onAddAlert={() => navigate("/equity/alerts")}
        onOpenScreener={() => navigate("/equity/screener")}
      />
    </div>
  );
}

export default IntelligenceTimelinePage;
