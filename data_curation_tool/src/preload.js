/**
 * This file sets up the context bridge to expose Electron APIs to the renderer process.
 */
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  selectFolder: () => ipcRenderer.invoke('select-folder'),
  runPythonScript: (args) => ipcRenderer.invoke('run-python', args),
  cancelPythonScript: () => ipcRenderer.invoke('cancel-python')
});
