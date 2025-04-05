// frontend/src/components/UploadView.jsx
import React from 'react';
import styles from './UploadView.module.css'; // We'll create this CSS module next
import { UploadCloud } from 'lucide-react'; // Using lucide-react for icons (npm install lucide-react)

function UploadView({ onFileChange, onUpload, file, isLoading }) {
    const handleDragOver = (event) => {
        event.preventDefault(); // Necessary to allow dropping
        // Optional: Add visual feedback on drag over
    };

    const handleDrop = (event) => {
        event.preventDefault();
        if (event.dataTransfer.files && event.dataTransfer.files[0]) {
            const droppedFile = event.dataTransfer.files[0];
            // Simulate the file input event structure for handleFileChange
            onFileChange({ target: { files: [droppedFile] } });
        }
        // Optional: Remove visual feedback
    };

    return (
        <div className={styles.uploadContainer}>
            <h1 className={styles.title}>POZE</h1> {/* Your Logo/Title */}
            <p className={styles.subtitle}>AI Video Technique Analysis</p>

            <div
                className={styles.dropZone}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                onClick={() => document.getElementById('fileInput').click()} // Trigger hidden input
            >
                <input
                    type="file"
                    id="fileInput"
                    accept="video/mp4,video/quicktime,video/*" // Be more specific if needed
                    onChange={onFileChange}
                    disabled={isLoading}
                    style={{ display: 'none' }} // Hide the default input
                />
                <UploadCloud size={48} className={styles.uploadIcon} />
                {file ? (
                    <p>Selected: {file.name}</p>
                ) : (
                    <p>Drag & drop your video file here, or click to select (.mp4)</p>
                )}
            </div>

            <button
                onClick={onUpload}
                disabled={!file || isLoading}
                className={styles.analyzeButton}
            >
                {isLoading ? 'Analyzing...' : 'Analyze Video'}
            </button>
        </div>
    );
}

export default UploadView;