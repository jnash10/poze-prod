// frontend/src/components/ResultsView.jsx
import React from 'react';
import styles from './ResultsView.module.css';
import { AlertCircle, CheckCircle2, Loader } from 'lucide-react';

// Receive videoSrc as a prop
function ResultsView({ status, statusMessage, error, attributes, feedback, videoSrc, onReset }) {

    const renderStatusIcon = () => {
        switch (status) {
            case 'processing':
            case 'attributes_ready':
            case 'feedback_ready':
                return <Loader size={20} className={styles.spinner} />;
            case 'complete':
                return <CheckCircle2 size={20} className={styles.successIcon} />;
            case 'error':
                return <AlertCircle size={20} className={styles.errorIcon} />;
            default:
                return null;
        }
    };

    return (
        <div className={styles.resultsContainer}>
            {/* Status Bar */}
            <div className={`${styles.statusCard} ${styles[`status-${status}`]}`}>
                <div className={styles.statusHeader}>
                    {renderStatusIcon()}
                    <h2>Status: {status.replace('_', ' ')}</h2>
                </div>
                {statusMessage && <p>{statusMessage}</p>}
                {error && <p className={styles.errorMessageDetail}>Error: {error}</p>}
                {(status === 'complete' || status === 'error') && (
                    <button onClick={onReset} className={styles.resetButton}>Analyze Another Video</button>
                )}
            </div>

            {/* Main Content Grid */}
            <div className={styles.contentGrid}>
                {/* Video Area - Updated */}
                <div className={`${styles.resultCard} ${styles.videoArea}`}>
                    <h3>User Video</h3>
                    {videoSrc ? (
                        <video
                            key={videoSrc} // Add key to force re-render if src changes
                            className={styles.videoPlayer}
                            src={videoSrc}
                            loop // Autoloop
                            autoPlay // Autoplay
                            muted // Muted is often required for autoplay
                            playsInline // Important for mobile
                            controls // Show default browser controls
                        // You might remove 'controls' for a cleaner look if desired
                        />
                    ) : (
                        // Fallback if videoSrc is somehow not available
                        <div className={styles.videoPlaceholder}>
                            <p>(Video not available)</p>
                        </div>
                    )}
                </div>

                {/* Attributes Area */}
                <div className={`${styles.resultCard} ${styles.attributesArea}`}>
                    <h3>Assistant Coach Analysis</h3>
                    {status === 'processing' && !attributes && <p>Extracting...</p>}
                    {attributes ? (
                        <ul>
                            {Object.entries(attributes).map(([key, value]) =>
                                value !== null && value !== undefined && (
                                    <li key={key}>
                                        <strong>{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</strong> {String(value)}
                                    </li>
                                )
                            )}
                        </ul>
                    ) : (status !== 'processing' && status !== 'idle' && status !== 'uploading' && <p>No attributes extracted.</p>)}
                </div>

                {/* Recommendations Area */}
                <div className={`${styles.resultCard} ${styles.recommendationsArea}`}>
                    <h3>Coach Recommendations</h3>
                    {(status === 'processing' || status === 'attributes_ready') && !feedback && <p>Generating feedback...</p>}
                    {feedback ? (
                        <div>
                            {Object.entries(feedback).map(([category, points]) => (
                                Array.isArray(points) && points.length > 0 && (
                                    <div key={category} className={styles.feedbackCategory}>
                                        <h4>{category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</h4>
                                        <ul>
                                            {points.map((point, index) => <li key={`${category}-${index}`}>{point}</li>)}
                                        </ul>
                                    </div>
                                )
                            ))}
                        </div>
                    ) : (status !== 'processing' && status !== 'attributes_ready' && status !== 'idle' && status !== 'uploading' && <p>No feedback generated.</p>)}
                </div>
            </div>
        </div>
    );
}

export default ResultsView;