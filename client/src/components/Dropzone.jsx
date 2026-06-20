import React, { useCallback, useState } from 'react';
import styles from './Dropzone.module.css';
import { uploadCSV } from '../utils/api';

export default function Dropzone({ onUploadSuccess }) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(async (e) => {
    e.preventDefault();
    setIsDragging(false);
    setError(null);

    const files = e.dataTransfer.files;
    if (files.length === 0) return;

    const file = files[0];
    if (file.type !== 'text/csv' && !file.name.endsWith('.csv')) {
      setError('Please upload a valid CSV file.');
      return;
    }

    await handleUpload(file);
  }, []);

  const handleFileInput = async (e) => {
    setError(null);
    const file = e.target.files[0];
    if (file) {
      await handleUpload(file);
    }
  };

  const handleUpload = async (file) => {
    setIsUploading(true);
    try {
      const result = await uploadCSV(file);
      onUploadSuccess(result.job_id || result.id);
    } catch (err) {
      setError(err.message || 'An error occurred during upload.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className={`${styles.dropzoneContainer} animate-fade-in`}>
      <div 
        className={`${styles.dropArea} ${isDragging ? styles.dragging : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className={styles.iconWrapper}>
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="17 8 12 3 7 8"></polyline>
            <line x1="12" y1="3" x2="12" y2="15"></line>
          </svg>
        </div>
        
        <h3 className={styles.title}>Upload Transactions</h3>
        <p className={styles.subtitle}>Drag and drop your CSV file here</p>
        
        <div className={styles.divider}>
          <span className={styles.dividerText}>or</span>
        </div>
        
        <label className="btn">
          Browse Files
          <input 
            type="file" 
            accept=".csv" 
            className={styles.fileInput} 
            onChange={handleFileInput}
            disabled={isUploading}
          />
        </label>
        
        {isUploading && <p className={styles.uploadingText}>Uploading and processing...</p>}
        {error && <p className={styles.errorText}>{error}</p>}
      </div>
    </div>
  );
}
