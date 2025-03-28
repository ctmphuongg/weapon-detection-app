import React from 'react';

const DetectionPanel = ({ detections }) => {
  return (
    <div className="detection-panel">
      <h3>Latest Detections:</h3>
      <pre>{detections.length > 0 ? JSON.stringify(detections, null, 2) : "No detections yet"}</pre>
    </div>
  );
};

export default DetectionPanel;