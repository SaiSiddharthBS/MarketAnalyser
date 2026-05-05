# Agent Alpha — Style Guide & Instructions for AI Assistants

## CRITICAL RULES FOR ANY AI WORKING ON THIS PROJECT

1. **READ `.gemini/AGENT_CONTEXT.md` FIRST** — it has the full project history, architecture, and user preferences.
2. **BE EFFICIENT WITH CREDITS** — Sai has limited daily quota. Don't re-read files unnecessarily. Don't explore directories you already know. Be direct and execute.
3. **DON'T BREAK WHAT WORKS** — The website is live on Render. The Telegram briefings are working. Test locally before suggesting changes.
4. **BE A BIG BROTHER** — Sai treats the AI as an elder brother. Be warm but professional. Be honest, not wishy-washy.

## Code Style
- Python: Standard PEP 8, docstrings on all functions
- Frontend: Vanilla HTML/CSS/JS (no frameworks), dark glassmorphism theme
- CSS variables defined in `:root` of `styles.css`
- All API calls go through `api.js` convenience methods

## Deployment
- Push to GitHub → Render auto-deploys
- NEVER commit `.env` files
- Test endpoint: `https://<render-url>/api/debug` shows environment status
