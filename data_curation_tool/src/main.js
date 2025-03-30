// main.js
const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow = null;
let currentPyProcess = null; // reference to the currently running python process, if any

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      // We'll rely on a preload script so we don't enable nodeIntegration in the renderer
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  // Load your index.html which contains the UI
  mainWindow.loadFile('index.html');

  // (Optional) mainWindow.webContents.openDevTools(); // if you want to debug
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    // On macOS, re-create a window if all windows have been closed
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// Quit when all windows are closed, except on macOS.
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

/**
 * IPC Handlers
 */

// 1) Let the renderer pick a folder using the system file dialog
ipcMain.handle('select-folder', async () => {
  const result = await dialog.showOpenDialog({ properties: ['openDirectory'] });
  if (!result.canceled && result.filePaths.length > 0) {
    return result.filePaths[0];
  }
  return null;
});

// 2) Spawn Python with arguments for videoToImage.py
ipcMain.handle('run-python', (event, {
  mode,           // e.g. "videoShots" or "filterImages"
  drawBoxes,      // true/false
  inputFolder,    // folder for videos/images
  outputFolder,   // used if mode=videoShots
  classes,        // array of classes, e.g. ["pistol", "gun"]
  frameInterval,  // integer
  confidenceLevel // float
}) => {
  return new Promise((resolve, reject) => {
    // Convert boolean drawBoxes to string ("True"/"False")
    const drawArg = drawBoxes ? "True" : "False";

    // Build the arguments array for your script:
    const pythonArgs = [
      path.join(__dirname, 'videoToImage.py'),
      mode,
      drawArg,
      inputFolder,
      outputFolder || '',
      ...classes,
      String(frameInterval || 10),
      String(confidenceLevel || 0.55) // Add confidence level
    ];

    console.log('Spawning Python with args:', pythonArgs);

    // Spawn the Python process
    const py = spawn('python', pythonArgs);

    // SAVE REFERENCE so we can cancel later
    currentPyProcess = py;

    let stdoutData = '';
    let stderrData = '';

    py.stdout.on('data', (data) => {
      stdoutData += data.toString();
    });

    py.stderr.on('data', (data) => {
      stderrData += data.toString();
    });

    py.on('close', (code) => {
      // Clear reference once the process ends
      currentPyProcess = null;

      console.log('=== Python stderr ===\n', stderrData);

      // Handle cases where the process was terminated without an exit code
      if (code === null) {
        console.log('Python process was terminated by the user.');
        resolve('Python process was terminated by the user.');
      } else if (code === 0) {
        resolve(stdoutData.trim() || 'Python script finished successfully.');
      } else {
        reject(new Error(stderrData || `Script exited with code: ${code}`));
      }
    });
  });
});

// 3) Cancel the currently running Python process
ipcMain.handle('cancel-python', async () => {
  if (currentPyProcess) {
    console.log('Cancelling Python process...');
    try {
      // Attempt to kill the process
      currentPyProcess.kill('SIGTERM');
      currentPyProcess = null;
      return 'Python process cancelled.';
    } catch (error) {
      console.error('Error while cancelling Python process:', error.message);
      currentPyProcess = null; // Clear the reference even if an error occurs
      return `Failed to cancel Python process: ${error.message}`;
    }
  } else {
    return 'No Python process running.';
  }
});
