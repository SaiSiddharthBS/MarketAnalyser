// preload.js
const { ipcRenderer } = require('electron');

// Instantly inject the splash overlay before anything renders.
// This guarantees zero screen flashing and absolute smoothness.
const style = document.createElement('style');
style.innerHTML = `
  #aa-splash-overlay {
    position: fixed;
    top: 0; left: 0; width: 100vw; height: 100vh;
    background: #051114; /* Deep obsidian teal from themes */
    z-index: 999999;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    -webkit-app-region: drag; /* Draggable */
  }
  .aa-logo {
    width: 140px;
    height: auto;
    border-radius: 20px;
    box-shadow: 0 10px 40px rgba(0, 255, 136, 0.15);
    opacity: 0;
  }
  .aa-welcome {
    font-family: 'JetBrains Mono', 'SF Mono', 'Fira Code', monospace;
    font-size: 1.6rem;
    font-weight: 500;
    color: #00FF88;
    text-transform: uppercase;
    letter-spacing: 6px;
    opacity: 0;
    position: absolute; /* So it can replace the logo seamlessly */
  }
  .aa-init {
    font-family: 'JetBrains Mono', 'SF Mono', 'Fira Code', monospace;
    font-size: 0.9rem;
    color: rgba(255, 255, 255, 0.5);
    margin-top: 40px;
    opacity: 0;
    display: flex;
    align-items: center;
    gap: 8px;
    position: absolute;
    transform: translateY(40px);
  }
  .aa-cursor {
    width: 8px;
    height: 16px;
    background-color: #00FF88;
    animation: blink 1s step-end infinite;
  }
  @keyframes blink { 50% { opacity: 0; } }
`;
document.documentElement.appendChild(style);

const splash = document.createElement('div');
splash.id = 'aa-splash-overlay';
splash.innerHTML = `
  <img src="/static/images/logo.png" class="aa-logo" alt="Agent Alpha">
  <div class="aa-welcome">Welcome Agent</div>
  <div class="aa-init">
    <span>> SYSTEM INITIALIZING...</span>
    <div class="aa-cursor"></div>
  </div>
`;
document.documentElement.appendChild(splash);

// Wait for DOM and GSAP to load from the main index.html
window.addEventListener('DOMContentLoaded', () => {
  const checkInterval = setInterval(() => {
    if (window.gsap) {
      clearInterval(checkInterval);
      runAnimation();
    }
  }, 50);
});

function runAnimation() {
  const tl = window.gsap.timeline({
    onComplete: () => {
      // Fade out the entire overlay, revealing the fully loaded dashboard
      window.gsap.to('#aa-splash-overlay', {
        opacity: 0,
        duration: 1.2,
        ease: "power2.inOut",
        onComplete: () => {
          document.getElementById('aa-splash-overlay').remove();
        }
      });
    }
  });

  // 1. Logo fades in (GTA style entry)
  tl.fromTo('.aa-logo',
    { opacity: 0, scale: 1.05, y: 10 },
    { opacity: 1, scale: 1, y: 0, duration: 1.5, ease: "expo.out" }
  )
  // 2. Logo fades out
  .to('.aa-logo', 
    { opacity: 0, scale: 0.95, duration: 1, ease: "power2.inOut" },
    "+=0.8"
  )
  // 3. Welcome Agent fades in (Cyber Green)
  .fromTo('.aa-welcome',
    { opacity: 0, scale: 0.95, filter: 'blur(4px)' },
    { opacity: 1, scale: 1, filter: 'blur(0px)', duration: 1.2, ease: "power3.out" },
    "-=0.2"
  )
  // 4. Initializing hacker text appears below it
  .fromTo('.aa-init',
    { opacity: 0 },
    { opacity: 1, duration: 0.2, ease: "none" },
    "+=0.5"
  )
  // Hold briefly before transitioning to dashboard
  .to({}, { duration: 1.8 });
}
