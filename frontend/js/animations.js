/**
 * Agent Alpha v3.0 — GSAP Animation Engine
 * Creates Awwwards-style 120Hz smooth transitions and entry effects.
 */

document.addEventListener("DOMContentLoaded", () => {
    // 1. Initial Load Stagger Animation
    // Elements with the .gs-reveal class will slide up and fade in smoothly
    gsap.fromTo(".gs-reveal", 
        { y: 30, opacity: 0 }, 
        { 
            y: 0, 
            opacity: 1, 
            duration: 0.8, 
            stagger: 0.1, 
            ease: "power3.out",
            delay: 0.2
        }
    );

    // 2. Continuous Background Glow effect
    gsap.to(".logo-orb", {
        boxShadow: "0 0 20px rgba(0, 240, 255, 0.8), 0 0 10px rgba(0, 240, 255, 0.4) inset",
        duration: 2,
        yoyo: true,
        repeat: -1,
        ease: "sine.inOut"
    });
    
    // 3. Live Clock Update
    const timeEl = document.getElementById("live-time");
    if (timeEl) {
        setInterval(() => {
            const now = new Date();
            timeEl.innerText = now.toLocaleTimeString('en-US', { hour12: false }) + " IST";
        }, 1000);
    }
});

// Function to animate page transitions (called when nav items are clicked)
function animatePageTransition(hidePageId, showPageId) {
    const tl = gsap.timeline();
    
    if (hidePageId) {
        tl.to(`#${hidePageId}`, { 
            opacity: 0, 
            y: -20, 
            duration: 0.3, 
            ease: "power2.in",
            onComplete: () => {
                document.getElementById(hidePageId).classList.remove('active');
                document.getElementById(hidePageId).style.display = 'none';
            }
        });
    }
    
    tl.call(() => {
        const target = document.getElementById(showPageId);
        if (target) {
            target.style.display = 'block';
            target.classList.add('active');
        }
    });
    
    tl.fromTo(`#${showPageId}`, 
        { opacity: 0, y: 20 }, 
        { opacity: 1, y: 0, duration: 0.4, ease: "power2.out" }
    );
}
