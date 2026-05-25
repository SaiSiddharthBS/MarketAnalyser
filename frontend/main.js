const { app, BrowserWindow, WebContentsView, ipcMain } = require('electron');
const path = require('path');

// Fix hardware acceleration for fluid GSAP on mac
app.commandLine.appendSwitch('enable-gpu-rasterization');
app.commandLine.appendSwitch('enable-zero-copy');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    show: false,
    frame: false,
    titleBarStyle: 'hiddenInset', // Pushes traffic lights down slightly
    trafficLightPosition: { x: 20, y: 20 },
    backgroundColor: '#051114',
    webPreferences: {
      zoomFactor: 0.85, // Zooms out to standard size
      nodeIntegration: false,
      contextIsolation: true,
    }
  });

  // Inject CSS to fix sidebar overlapping traffic lights
  mainWindow.webContents.on('did-finish-load', () => {
    mainWindow.webContents.insertCSS(`
      .sidebar { padding-top: 35px !important; }
      .mobile-header { padding-top: 20px !important; height: calc(var(--header-h) + 20px) !important; }
    `);
  });

  mainWindow.loadURL('http://localhost:8000');

  // Create the Splash Screen View natively
  const splashView = new WebContentsView({
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });
  
  splashView.setBackgroundColor('#00000000'); // Ensure it can fade to transparent
  mainWindow.contentView.addChildView(splashView);
  
  // Set it to fill the entire window
  const updateSplashBounds = () => {
    const bounds = mainWindow.getBounds();
    splashView.setBounds({ x: 0, y: 0, width: bounds.width, height: bounds.height });
  };
  updateSplashBounds();
  mainWindow.on('resize', updateSplashBounds);

  splashView.webContents.loadFile(path.join(__dirname, 'splash.html'));

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    if (app.dock) {
      app.dock.setIcon(path.join(__dirname, 'images/logo.png'));
    }
  });

  // Listen for the splash GSAP sequence to finish
  ipcMain.once('splash-finished', () => {
    // Fade out natively
    splashView.webContents.executeJavaScript(`
      document.body.style.transition = 'opacity 0.8s ease';
      document.body.style.opacity = '0';
    `).then(() => {
      setTimeout(() => {
        mainWindow.contentView.removeChildView(splashView);
      }, 850);
    });
  });
}

app.whenReady().then(() => {
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
