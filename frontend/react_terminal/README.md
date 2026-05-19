# Agent Alpha - Terminal UI Transition

This directory (`frontend/react_terminal/`) is the future home of the Agent Alpha Terminal interface.
It is scaffolded with React + TypeScript + Vite.

## Transition Plan
1. Maintain the existing lightweight PWA (`frontend/` root) for current monitoring.
2. Build reusable UI components (Glassmorphic cards, charts) in `src/components`.
3. Integrate the new `/api/arena/monte-carlo` and `/api/ai/*` endpoints.
4. Gradually switch the primary interface over once feature parity is reached.

## Technology Stack
- React + TypeScript
- Vite
- Vanilla CSS (Glassmorphism, High-end aesthetics)
- Recharts / Lightweight chart libraries (To be added)
