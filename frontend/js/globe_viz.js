/**
 * Agent Alpha v3.0 — 3D WebGL Globe
 * Visualizes global macro events and capital flow.
 */

document.addEventListener("DOMContentLoaded", () => {
    const globeContainer = document.getElementById('globeViz');
    
    if (!globeContainer || typeof Globe === 'undefined') return;
    
    // Create the Globe
    const world = Globe()(globeContainer)
        .globeImageUrl('https://unpkg.com/three-globe/example/img/earth-dark.jpg')
        .bumpImageUrl('https://unpkg.com/three-globe/example/img/earth-topology.png')
        .backgroundImageUrl('https://unpkg.com/three-globe/example/img/night-sky.png')
        .pointOfView({ lat: 20, lng: 78, altitude: 2.5 }) // Focus on India
        .width(globeContainer.clientWidth)
        .height(globeContainer.clientHeight);
        
    // Add glowing arcs to simulate capital flow / macro connections
    const arcsData = [
        // US Fed to India (Foreign Institutional Flow)
        { startLat: 40.71, startLng: -74.00, endLat: 19.07, endLng: 72.87, color: '#00F0FF' },
        // London to India
        { startLat: 51.50, startLng: -0.12, endLat: 19.07, endLng: 72.87, color: '#8A2BE2' },
        // Singapore to India (SGX Nifty Flow)
        { startLat: 1.35, startLng: 103.81, endLat: 19.07, endLng: 72.87, color: '#00FF66' }
    ];
    
    world.arcsData(arcsData)
        .arcColor('color')
        .arcDashLength(0.4)
        .arcDashGap(4)
        .arcDashInitialGap(() => Math.random() * 5)
        .arcDashAnimateTime(2000)
        .arcStroke(1.5);
        
    // Add rings for major financial hubs
    const ringsData = [
        { lat: 19.07, lng: 72.87, name: 'Mumbai (BSE/NSE)', maxR: 5 }, // Mumbai
        { lat: 40.71, lng: -74.00, name: 'New York (NYSE)', maxR: 3 }, // NYC
        { lat: 1.35, lng: 103.81, name: 'Singapore (SGX)', maxR: 3 }   // Singapore
    ];
    
    world.ringsData(ringsData)
        .ringColor(() => '#00F0FF')
        .ringMaxRadius('maxR')
        .ringPropagationSpeed(2)
        .ringRepeatPeriod(1000);
        
    // Add custom glowing atmosphere
    const scene = world.scene();
    scene.fog = new THREE.FogExp2(0x000000, 0.02);
    
    // Auto-rotate
    world.controls().autoRotate = true;
    world.controls().autoRotateSpeed = 0.5;
    world.controls().enableZoom = false; // Disable zoom to keep layout clean
    
    // Handle resize
    window.addEventListener('resize', () => {
        if (globeContainer.clientWidth > 0) {
            world.width(globeContainer.clientWidth);
            world.height(globeContainer.clientHeight);
        }
    });
});
