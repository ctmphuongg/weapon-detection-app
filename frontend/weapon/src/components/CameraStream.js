// src/components/CameraStream.js
import React, { useRef, useEffect } from 'react';

const CameraStream = ({ apiUrl }) => {
  const imgRef = useRef(null);

  // Method 1: Direct Image Source
  // This is the simplest approach but may have limitations with MJPEG streams
  return (
    <img 
      ref={imgRef}
      src={apiUrl} 
      alt="Camera Stream" 
      width="640" 
      height="480"
      style={{ border: '1px solid #ccc' }}
    />
  );
  
  /* 
  // Method 2: Alternative approach using fetch and object URLs if needed
  // Uncomment this and comment out the above return statement if Method 1 doesn't work
  
  useEffect(() => {
    let isMounted = true;
    const controller = new AbortController();
    
    const fetchStream = async () => {
      try {
        const response = await fetch(apiUrl, {
          signal: controller.signal
        });
        
        const reader = response.body.getReader();
        
        while (isMounted) {
          const { done, value } = await reader.read();
          if (done) break;
          
          // Create a blob from the chunk and set it as the image source
          const blob = new Blob([value], { type: 'image/jpeg' });
          const url = URL.createObjectURL(blob);
          
          if (imgRef.current && isMounted) {
            imgRef.current.src = url;
            // Clean up previous object URL
            setTimeout(() => URL.revokeObjectURL(url), 100);
          }
        }
      } catch (error) {
        if (error.name !== 'AbortError') {
          console.error('Error fetching stream:', error);
        }
      }
    };
    
    fetchStream();
    
    return () => {
      isMounted = false;
      controller.abort();
    };
  }, [apiUrl]);
  
  return (
    <img 
      ref={imgRef}
      alt="Camera Stream" 
      width="640" 
      height="480"
      style={{ border: '1px solid #ccc' }}
    />
  );
  */
};

export default CameraStream;