// src/App.js
import React, { useEffect, useState } from 'react';

function App() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [connectionError, setConnectionError] = useState(false);
  const [dangerousDetections, setDangerousDetections] = useState([]);
  const [lastDetectionTime, setLastDetectionTime] = useState(null);
  const API_URL = 'http://localhost:8000';
  
  // Define dangerous classes to watch for
  const DANGEROUS_CLASSES = ['gun', 'knife', 'pistol', 'rifle', 'weapon', 'person'];

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

    // Set up polling for detections
    const detectionsInterval = setInterval(async () => {
      if (isStreaming) {
        try {
          const response = await fetch(`${API_URL}/latest-detections`);
          if (response.ok) {
            const data = await response.json();
            if (data.detections && data.detections.length > 0) {
              // Filter for only dangerous objects
              const dangerous = data.detections.filter(detection => 
                DANGEROUS_CLASSES.some(className => 
                  detection.class_name.toLowerCase().includes(className)
                )
              );
              
              if (dangerous.length > 0) {
                setDangerousDetections(dangerous);
                setLastDetectionTime(new Date());
              }
            }
          }
        } catch (error) {
          console.error('Failed to fetch detections:', error);
        }
      }
    }, 1000); // Poll every second

    // Clean up on component unmount
    return () => {
      clearInterval(keepAliveInterval);
      clearInterval(detectionsInterval);
    };
  }, [isStreaming]);

  // Calculate if notification should be shown (show for 10 seconds after detection)
  const shouldShowNotification = lastDetectionTime && 
    ((new Date() - lastDetectionTime) < 10000);

  // const simulateDetection = () => {
  //   const mockDetections = [
  //     {
  //       class_name: "gun",
  //       confidence: 0.87,
  //       x1: 120,
  //       y1: 240,
  //       x2: 280,
  //       y2: 320
  //     }
  //   ];
    
  //   setDangerousDetections(mockDetections);
  //   setLastDetectionTime(new Date());
  // };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Critical Reach Detection System</h1>
      
      {connectionError && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          Cannot connect to streaming server. Please ensure the server is running.
        </div>
      )}

      {shouldShowNotification && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4 flex items-center animate-pulse">
          <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
          </svg>
          <div>
            <p className="font-bold"> DANGER ALERT! </p>
            <p>Dangerous objects detected: {dangerousDetections.map(d => `${d.class_name} (${(d.confidence * 100).toFixed(1)}%)`).join(', ')}</p>
          </div>
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

      <div className="mt-4 flex space-x-2">
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
        
      {/* Test button - Comment out when done  */}
      {/* <button 
      onClick={simulateDetection}
      className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600"
    >
      Test Notification
    </button> */}

      {dangerousDetections.length > 0 && shouldShowNotification && (
        <div className="mt-4">
          <h2 className="text-xl font-bold mb-2 text-red-600"> Dangerous Objects Detected</h2>
          <div className="bg-red-50 rounded-lg shadow p-4 border border-red-200">
            <ul>
              {dangerousDetections.map((detection, index) => (
                <li key={index} className="mb-1">
                  {detection.class_name}: {(detection.confidence * 100).toFixed(1)}% 
                  at [{detection.x1.toFixed(0)}, {detection.y1.toFixed(0)}]
                </li>
              ))}
            </ul>
            <p className="text-sm text-gray-500 mt-2">
              Last detected: {lastDetectionTime ? lastDetectionTime.toLocaleTimeString() : 'Never'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;