// src/App.js
import React, { useEffect, useState } from 'react';
import './index.css';

function App() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [connectionError, setConnectionError] = useState(false);
  const [dangerousDetections, setDangerousDetections] = useState([]);
  const [lastDetectionTime, setLastDetectionTime] = useState(null);
  const [stats, setStats] = useState({
    highestThreatLevel: 0, // Highest confidence percentage seen
    lastHourDetections: 0,
    detectionHistory: [], // Add this to track detection timestamps
  });
  const [previousDetections, setPreviousDetections] = useState([]); // Track previous detections to compare
  const [detectionLog, setDetectionLog] = useState([]); // Add this state
  const API_URL = 'http://localhost:8000';
  
  // Define dangerous classes to watch for
  const DANGEROUS_CLASSES = ['gun', 'knife', 'pistol', 'rifle', 'weapon', 'suitcase'];

  // Function to simulate a detection
  const simulateDetection = () => {
    const mockDetections = [
      {
        class_name: 'gun',
        confidence: 0.95,
        x1: 100,
        y1: 150,
      },
      {
        class_name: 'knife',
        confidence: 0.88,
        x1: 200,
        y1: 300,
      }
    ];
    
    setDangerousDetections(mockDetections);
    setLastDetectionTime(new Date());
    setStats(prev => ({
      highestThreatLevel: Math.max(prev.highestThreatLevel, 0.95),
      lastHourDetections: prev.lastHourDetections + mockDetections.length,
    }));
  };

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
              const dangerous = data.detections.filter(detection => 
                DANGEROUS_CLASSES.some(className => 
                  detection.class_name.toLowerCase().includes(className)
                )
              );
              
              if (dangerous.length > 0) {
                const currentTime = new Date();
                setDangerousDetections(dangerous);
                setLastDetectionTime(currentTime);
                
                // Update detection log
                setDetectionLog(prev => {
                  const newLog = [
                    ...dangerous.map(detection => ({
                      ...detection,
                      timestamp: currentTime
                    })),
                    ...prev
                  ].slice(0, 50); // Keep last 50 detections
                  return newLog;
                });

                setStats(prev => ({
                  highestThreatLevel: Math.max(prev.highestThreatLevel, 
                    Math.max(...dangerous.map(d => d.confidence * 100))
                  ),
                  lastHourDetections: prev.lastHourDetections + dangerous.length,
                }));
              } else {
                setDangerousDetections([]);
                setPreviousDetections([]);
              }
            } else {
              setDangerousDetections([]);
              setPreviousDetections([]);
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

  // Calculate if notification should be shown (show for 5 minutes after detection)
  const shouldShowNotification = lastDetectionTime && 
    ((new Date() - lastDetectionTime) < 300000); // 5 minutes in milliseconds

  // Helper function to format time
  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <div className="flex items-center">
              <svg className="h-8 w-8 text-red-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <h1 className="text-2xl font-bold text-gray-900">Critical Reach Detection System</h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className={`flex items-center px-3 py-1 rounded-full ${isStreaming ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                <div className={`w-2 h-2 rounded-full mr-2 ${isStreaming ? 'bg-green-500' : 'bg-red-500'} animate-pulse`}></div>
                <span className="text-sm font-medium">{isStreaming ? 'Live' : 'Offline'}</span>
              </div>
              <button 
                onClick={() => {
                  fetch(`${API_URL}/keep-alive`);
                  setIsStreaming(true);
                }}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Refresh Stream
              </button>
              {/* Test Detection Button */}
              <button 
                onClick={simulateDetection}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                Test Detection
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Main video feed */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="p-4 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">Live Feed</h2>
              </div>
              <div className="relative bg-black aspect-video">
                {isStreaming ? (
                  <img 
                    src={`${API_URL}/`} 
                    alt="Camera Stream" 
                    className="w-full h-full object-contain"
                    onError={() => {
                      setConnectionError(true);
                      setIsStreaming(false);
                    }}
                  />
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center">
                      <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                      <p className="mt-2 text-sm text-gray-500">{connectionError ? 'Connection error' : 'Loading stream...'}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Stats and Alerts */}
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white rounded-lg shadow p-4">
                <h3 className="text-sm font-medium text-gray-500">Highest Threat Level</h3>
                <p className="mt-2 text-3xl font-semibold text-gray-900">
                  {stats.highestThreatLevel > 0 ? `${stats.highestThreatLevel.toFixed(1)}%` : 'None'}
                </p>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <h3 className="text-sm font-medium text-gray-500">Last Hour</h3>
                <p className="mt-2 text-3xl font-semibold text-gray-900">{stats.lastHourDetections}</p>
              </div>
            </div>

            {/* Active Alerts */}
            {shouldShowNotification && (
              <div className={`bg-red-50 rounded-lg shadow-lg border-2 border-red-500 transition-all duration-500 ${shouldShowNotification ? 'opacity-100 transform translate-y-0' : 'opacity-0 transform -translate-y-4'}`}>
                <div className="p-4">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <svg className="h-8 w-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                    </div>
                    <div className="ml-4">
                      <h3 className="text-lg font-medium text-red-800">DANGER ALERT!</h3>
                      <div className="mt-2 text-red-700">
                        {dangerousDetections.map((detection, index) => (
                          <div key={index} className="flex items-center space-x-2 mb-1">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                              {detection.class_name}
                            </span>
                            <span className="text-sm">
                              Confidence: {(detection.confidence * 100).toFixed(1)}%
                            </span>
                          </div>
                        ))}
                      </div>
                      <p className="mt-2 text-sm text-red-600">
                        Last detected: {lastDetectionTime?.toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Recent Detections Log */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-4 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">Detection Log</h2>
              </div>
              <div className="p-4">
                {detectionLog.length > 0 ? (
                  <div className="space-y-4 max-h-96 overflow-y-auto">
                    {detectionLog.map((detection, index) => (
                      <div key={index} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                        <div className="flex flex-col">
                          <div className="flex items-center">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 mr-2">
                              {detection.class_name}
                            </span>
                            <span className="text-sm text-gray-500">
                              [{detection.x1.toFixed(0)}, {detection.y1.toFixed(0)}]
                            </span>
                          </div>
                          <span className="text-xs text-gray-400 mt-1">
                            {formatTime(detection.timestamp)}
                          </span>
                        </div>
                        <span className="text-sm font-medium text-gray-900">
                          {(detection.confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-sm">No recent detections</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;