// src/App.js
import React, { useEffect, useState } from 'react';

function App() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [connectionError, setConnectionError] = useState(false);
  const API_URL = 'http://localhost:8000'; // Change this to match your server address

  useEffect(() => {
    // Keep-alive function to maintain the stream
    const keepAlive = async () => {
      try {
        const response = await fetch(`${API_URL}/keep-alive`);
        if (response.ok) {
          setConnectionError(false);
          setIsStreaming(true);
        } else {
          setConnectionError(true);
          setIsStreaming(false);
        }
      } catch (error) {
        console.error('Keep-alive error:', error);
        setConnectionError(true);
        setIsStreaming(false);
      }
    };

    // Call keep-alive immediately
    keepAlive();

    // Set up interval to call keep-alive every 30 seconds
    const keepAliveInterval = setInterval(keepAlive, 30000);

    // Clean up on component unmount
    return () => clearInterval(keepAliveInterval);
  }, []);

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Camera Stream</h1>
      
      {connectionError && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          Cannot connect to streaming server. Please ensure the server is running.
        </div>
      )}

      <div className="relative bg-gray-200 rounded-lg overflow-hidden">
        {isStreaming ? (
          <img 
            src={`${API_URL}/`} 
            alt="Camera Stream" 
            className="w-full h-auto"
            onError={() => {
              setConnectionError(true);
              setIsStreaming(false);
            }}
          />
        ) : (
          <div className="flex items-center justify-center h-96">
            <p className="text-gray-500">{connectionError ? 'Connection error' : 'Loading stream...'}</p>
          </div>
        )}
      </div>

      <div className="mt-4">
        <button 
          onClick={() => {
            fetch(`${API_URL}/keep-alive`);
            setIsStreaming(true);
          }}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Refresh Stream
        </button>
      </div>
    </div>
  );
}

export default App;