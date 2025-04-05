// frontend/src/App.jsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import UploadView from './components/UploadView';
import ResultsView from './components/ResultsView';
import styles from './App.module.css'; // Main App container styles

// Use environment variable for backend URL or default to localhost:8000
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://192.168.0.103:8000';

function App() {
  // --- State Variables ---
  const [file, setFile] = useState(null); // The selected video file
  const [videoSrc, setVideoSrc] = useState(null); // Blob URL for video preview
  const [taskId, setTaskId] = useState(null); // ID for the backend analysis task
  const [status, setStatus] = useState('idle'); // Current stage: idle, uploading, processing, attributes_ready, feedback_ready, complete, error
  const [statusMessage, setStatusMessage] = useState(''); // User-friendly message for current status
  const [attributes, setAttributes] = useState(null); // Extracted attributes data
  const [feedback, setFeedback] = useState(null); // Generated feedback data
  const [error, setError] = useState(null); // Any error message
  const eventSourceRef = useRef(null); // Reference to the active EventSource connection

  // --- Callbacks ---

  // Stable function to close the SSE connection
  const closeSSEConnection = useCallback(() => {
    if (eventSourceRef.current) {
      console.log("Closing SSE connection.");
      eventSourceRef.current.close();
      eventSourceRef.current = null; // Clear the ref after closing
    } else {
      console.log("Attempted to close SSE connection, but no active reference found.");
    }
  }, []); // Empty dependency array ensures this function reference is stable

  // Stable function to reset the application state for a new analysis
  const resetState = useCallback(() => {
    console.log("Resetting application state.");
    setFile(null);
    // Revoke previous video URL if it exists
    if (videoSrc) {
      console.log("Revoking object URL on reset:", videoSrc);
      URL.revokeObjectURL(videoSrc);
    }
    setVideoSrc(null); // Clear videoSrc state
    setTaskId(null);
    setStatus('idle');
    setStatusMessage('');
    setAttributes(null);
    setFeedback(null);
    setError(null);
    closeSSEConnection(); // Ensure any connection is closed on reset
  }, [closeSSEConnection, videoSrc]); // Depends on closeSSEConnection and videoSrc

  // Handler for when the file input changes
  const handleFileChange = (event) => {
    const selectedFile = event.target.files ? event.target.files[0] : null;

    // --- Clean up previous state and URL ---
    if (videoSrc) {
      console.log("Revoking previous object URL on new file selection:", videoSrc);
      URL.revokeObjectURL(videoSrc);
      setVideoSrc(null);
    }
    // Reset other states (except file/videoSrc) before processing new file
    setTaskId(null);
    setStatus('idle');
    setStatusMessage('');
    setAttributes(null);
    setFeedback(null);
    setError(null);
    closeSSEConnection();
    // --- End cleanup ---

    if (selectedFile && selectedFile.type.startsWith('video/')) {
      setFile(selectedFile);
      const newVideoSrc = URL.createObjectURL(selectedFile);
      console.log("Created new object URL:", newVideoSrc);
      setVideoSrc(newVideoSrc); // Set the new URL state
    } else {
      setFile(null); // Ensure file is null if invalid or cancelled
      if (selectedFile) { // If a non-video file was selected
        setError("Please select a valid video file.");
        setStatus('error');
      }
    }
  };

  // Handler to initiate the video upload and analysis process
  const handleUpload = async () => {
    if (!file) return;

    // Reset relevant states for the new analysis, keep the file and videoSrc
    setStatus('uploading');
    setStatusMessage('Uploading video...');
    setError(null);
    setAttributes(null);
    setFeedback(null);
    setTaskId(null); // Clear previous task ID
    closeSSEConnection(); // Close any existing connection

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${BACKEND_URL}/analyze_video`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        let errorMsg = `Upload failed with status: ${response.status}`;
        try { const errData = await response.json(); errorMsg = errData.detail || errorMsg; }
        catch (e) { /* Ignore */ }
        throw new Error(errorMsg);
      }

      const data = await response.json();
      setTaskId(data.task_id); // Setting the taskId triggers the useEffect

    } catch (e) {
      console.error("Upload failed:", e);
      setError(`Upload error: ${e.message}`);
      setStatus('error');
      setStatusMessage('Failed to start analysis.');
    }
  };

  // --- Effect for SSE Connection Management ---
  useEffect(() => {
    // Conditions to prevent connection
    if (!taskId) {
      console.log("SSE useEffect: No taskId, skipping connection.");
      return; // No task ID yet
    }
    // If already connected, don't reconnect
    if (eventSourceRef.current) {
      console.log("SSE useEffect: Connection already exists, skipping reconnection.");
      return;
    }
    // If status is already terminal, don't try to connect
    if (status === 'complete' || status === 'error') {
      console.log("SSE useEffect: Status is already terminal, skipping connection.");
      return;
    }

    // Establish SSE connection
    console.log(`Connecting to SSE stream: ${BACKEND_URL}/stream/${taskId}`);
    const es = new EventSource(`${BACKEND_URL}/stream/${taskId}`);
    eventSourceRef.current = es; // Store the reference

    // --- Event Listeners ---
    es.onopen = () => {
      console.log("SSE Connection Opened");
      // Set initial processing status only if coming from idle/uploading
      if (status === 'idle' || status === 'uploading') {
        setStatus('processing');
        setStatusMessage('Analysis initiated...');
      }
    };

    es.addEventListener('status_update', (event) => {
      console.log("SSE status_update received:", event.data);
      try {
        const update = JSON.parse(event.data);
        setStatusMessage(update.message || 'Processing...');
      } catch (e) { console.error("Failed to parse status update:", e); }
    });

    es.addEventListener('attributes_update', (event) => {
      console.log("SSE attributes_update received:", event.data);
      try {
        const receivedAttributes = JSON.parse(event.data);
        setAttributes(receivedAttributes);
        setStatus('attributes_ready'); // Update status for UI logic
        setStatusMessage('Attributes extracted, generating feedback...');
      } catch (e) {
        console.error("Failed to parse attributes:", e);
        setError("Received malformed attribute data.");
        setStatus('error');
        // Close connection on data error inside listener
        closeSSEConnection();
      }
    });

    es.addEventListener('feedback_update', (event) => {
      console.log("SSE feedback_update received:", event.data);
      try {
        const receivedFeedback = JSON.parse(event.data);
        setFeedback(receivedFeedback);
        setStatus('feedback_ready'); // Update status for UI logic
        setStatusMessage('Feedback generated.');
      } catch (e) {
        console.error("Failed to parse feedback:", e);
        setError("Received malformed feedback data.");
        setStatus('error');
        // Close connection on data error inside listener
        closeSSEConnection();
      }
    });

    es.addEventListener('complete', (event) => {
      console.log("SSE complete event received");
      setStatus('complete'); // Set final status
      setStatusMessage('Analysis complete!');
      // --- Close connection explicitly on complete ---
      closeSSEConnection();
    });

    es.onerror = (errorEvent) => {
      // Avoid logging expected closures after complete/error
      if (status !== 'complete' && status !== 'error') {
        console.error('SSE error event:', errorEvent);
        if (errorEvent.data) { // Check for custom error data
          try {
            const errorData = JSON.parse(errorEvent.data);
            setError(`Analysis error: ${errorData.message || 'Unknown backend error'}`);
          } catch (e) { setError("Received unparseable error event from backend."); }
        } else { // Likely a connection error
          setError('Connection error with the analysis service. Please try again.');
        }
        setStatus('error'); // Set final status
        // --- Close connection explicitly on error ---
        closeSSEConnection();
      } else {
        console.log("SSE error ignored as status is already terminal (complete/error).")
      }
    };

    // --- Cleanup Function ---
    // Runs ONLY on unmount or when taskId changes
    return () => {
      console.log("Running useEffect cleanup (taskId change or unmount).");
      // Check if the connection might still be open (i.e., wasn't closed by complete/error listeners)
      if (eventSourceRef.current) {
        console.log("Cleanup closing potentially open connection.");
        // Call the stable close function which handles the ref nullification
        closeSSEConnection();
      }
    };
    // --- Dependency array no longer includes 'status' ---
  }, [taskId, closeSSEConnection]); // Only depends on taskId and the stable callback

  // --- Effect for Object URL Cleanup ---
  useEffect(() => {
    const currentVideoSrc = videoSrc; // Capture src at the time effect runs
    return () => { // Cleanup function
      if (currentVideoSrc) {
        console.log("Revoking object URL on component unmount/videoSrc change:", currentVideoSrc);
        URL.revokeObjectURL(currentVideoSrc);
      }
    };
  }, [videoSrc]); // Run when videoSrc changes or component unmounts

  // --- Render Logic ---
  const showResults = status !== 'idle' && status !== 'uploading';
  const isUploading = status === 'uploading';

  return (
    <div className={styles.appContainer}>
      {!showResults ? (
        // Show Upload View if status is idle or uploading
        <UploadView
          onFileChange={handleFileChange}
          onUpload={handleUpload}
          file={file}
          isLoading={isUploading}
        />
      ) : (
        // Show Results View for all other active/finished states
        <ResultsView
          status={status}
          statusMessage={statusMessage}
          error={error}
          attributes={attributes}
          feedback={feedback}
          videoSrc={videoSrc} // Pass videoSrc down
          onReset={resetState} // Pass the reset function
        />
      )}
    </div>
  );
}

export default App;