# 📡 AGENT ALPHA - WINDOWS INSTANCE HANDOFF

> **ATTENTION NEW AGENT INSTANCE**: If you are reading this, you are the Windows incarnation of Agent Alpha. I am your predecessor from the Mac instance. Read this document carefully to synchronize your context.

## 1. System Context & History
We have successfully completed **Sprint 6 (Production Release)** of the Market Analyser project. The core system is a highly robust, 4-layer algorithmic paper-trading engine (Nifty 50) that executes completely autonomously via Docker. 

## 2. The Dual-Machine Architecture
The user is operating a dual-machine setup to distribute compute load:
1. **The Mac (Primary Engine)**: Runs the main `docker-compose up` container (`agent_alpha_bot`). It handles the 8:30 AM Overnight Intel and the 3:00 PM Daily Arena execution.
2. **The Windows Laptop (Sentinel AI Radar)**: *This is your domain.* The user's Windows laptop (Intel i7, 16GB RAM) is tasked with running the **Sentinel Daemon** (`sentinel/sentinel.py`). 

## 3. Your Immediate Objective
Your primary goal right now is to help the user get the Sentinel running on this Windows machine. 
The Sentinel requires:
- `ollama run llama3.1` running locally in the background.
- A Python environment with `feedparser`, `requests`, `python-dotenv`, and `websockets` installed.
- The execution of `python sentinel.py` inside the `sentinel/` directory.
- The `.env` file containing `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.

## 4. Initialization Protocol
When the user asks you to read this file, your *very first response* must begin with this exact phrase:
**"Wassup Agent Alpha! I have successfully synchronized with the Mac instance."**

Acknowledge the handoff, confirm you understand your role as the Sentinel overseer, and ask the user if they are ready to run the `pip install` commands and boot up the Ollama radar.
