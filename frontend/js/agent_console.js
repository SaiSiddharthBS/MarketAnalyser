/**
 * Agent Alpha v3.0 — The Alpha Console
 * Simulates a high-tech terminal interface where the AI "types" out its reasoning.
 */

class AgentConsole {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.queue = [];
        this.isTyping = false;
        
        // Initial boot sequence
        this.logSystem("INITIALIZING AGENT ALPHA v3.0...");
        this.logSystem("LOADING PYTORCH TRANSFORMER MODULE... [OK]");
        this.logSystem("CONNECTING TO ALT-DATA STREAMS... [OK]");
        this.logSystem("SYSTEM READY. AWAITING MARKET DATA.");
    }

    logSystem(text) {
        this.queue.push({ text: `> ${text}`, type: 'system' });
        this.processQueue();
    }

    logAnalysis(text) {
        this.queue.push({ text: text, type: 'analysis' });
        this.processQueue();
    }
    
    logAlert(text) {
        this.queue.push({ text: `[!] ${text}`, type: 'alert' });
        this.processQueue();
    }

    async processQueue() {
        if (this.isTyping || this.queue.length === 0) return;
        
        this.isTyping = true;
        const item = this.queue.shift();
        
        const lineEl = document.createElement('div');
        lineEl.className = `console-line ${item.type}`;
        
        // Color coding
        if (item.type === 'alert') lineEl.style.color = 'var(--accent-danger)';
        if (item.type === 'system') lineEl.style.color = 'var(--text-muted)';
        if (item.type === 'analysis') lineEl.style.color = 'var(--accent-primary)';
        
        this.container.appendChild(lineEl);
        
        // Typewriter effect
        for (let i = 0; i < item.text.length; i++) {
            lineEl.textContent += item.text.charAt(i);
            // Append cursor
            lineEl.innerHTML += '<span class="cursor-blink"></span>';
            
            this.container.scrollTop = this.container.scrollHeight;
            
            // Random typing delay (faster for system, slower for analysis)
            const delay = item.type === 'system' ? 10 : Math.random() * 30 + 10;
            await new Promise(r => setTimeout(r, delay));
            
            // Remove cursor for next char
            lineEl.innerHTML = lineEl.textContent;
        }
        
        this.isTyping = false;
        this.processQueue();
    }
}

// Global instance
let alphaConsole;
document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("alpha-console")) {
        alphaConsole = new AgentConsole("alpha-console");
    }
});
