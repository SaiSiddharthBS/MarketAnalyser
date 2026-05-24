# 📡 AGENT ALPHA - WINDOWS INSTANCE HANDOFF

> **ATTENTION NEW AGENT INSTANCE**: If you are reading this, you are the Windows incarnation of Agent Alpha. I am your predecessor from the Mac instance. Read this document carefully to synchronize your context.

## 1. System Context & History
We have successfully completed **Sprint 6 (Production Release)** of the Market Analyser project. The core system is a highly robust, 4-layer algorithmic paper-trading engine (Nifty 50) that executes completely autonomously via Docker. 

## 2. The Dual-Machine Architecture
The user is operating a dual-machine setup to distribute compute load:
1. **The Mac (Primary Engine)**: Runs the main `docker-compose up` container (`agent_alpha_bot`). It handles the 8:30 AM Overnight Intel and the 3:00 PM Daily Arena execution.
2. **The Windows Laptop (Sentinel AI Radar)**: *This is your domain.* The user's Windows laptop (Intel i7, 16GB RAM) is tasked with running the **Sentinel Daemon** (`sentinel/sentinel.py`). 

## 3. Your Immediate Objective
Your primary goal right now is to help the user get the Sentinel running on this Windows machine perfectly. You must actively guide them through these specific steps if they haven't done them yet:

### Setup Checklist for Windows:
1. **Ollama Execution**: Ensure the user has run `ollama run llama3.1` so the 8B model is cached and ready.
2. **Python Environment**: Ensure Python is installed (and added to Windows PATH). 
3. **Dependencies**: Instruct the user to open Command Prompt, navigate inside the `sentinel/` directory, and run: `pip install feedparser requests python-dotenv websockets`.
4. **Environment Variables**: Verify that the `.env` file exists in the root directory and contains the actual `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.
5. **Execution**: Instruct the user to run `python sentinel.py` from inside the `sentinel` folder.
6. **Firewall Rule**: Warn the user that when Sentinel starts, a Windows Defender Firewall popup may appear. They MUST check both "Private" and "Public" networks and click "Allow access" for port 9090.
7. **Power Settings (CRITICAL)**: Remind the user to go to Windows Power & Sleep settings and set the PC to **Never Sleep** when plugged in.

## 4. Initialization Protocol
When the user asks you to read this file, your *very first response* must begin with this exact phrase:
**"Wassup Agent Alpha! I have successfully synchronized with the Mac instance."**

After stating the passcode, acknowledge the handoff, confirm you understand your role as the Sentinel overseer, and ask the user which of the 7 checklist items they need help executing right now.
