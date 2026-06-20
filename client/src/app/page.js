'use client';

import React, { useState } from 'react';
import Dropzone from '../components/Dropzone';
import Dashboard from '../components/Dashboard';
import { pollJobStatus, getJobResults } from '../utils/api';
import styles from './page.module.css';

export default function Home() {
  const [jobId, setJobId] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handleUploadSuccess = (id) => {
    setJobId(id);
    setIsProcessing(true);
    setError(null);
    
    pollJobStatus(id, async (statusData) => {
      if (statusData.status === 'completed') {
        try {
          const finalResults = await getJobResults(id);
          setResults(finalResults);
        } catch (err) {
          setError('Failed to load final results.');
        } finally {
          setIsProcessing(false);
        }
      } else if (statusData.status === 'failed') {
        setError('Processing failed. Please try again with a valid CSV.');
        setIsProcessing(false);
      }
    });
  };

  const resetState = () => {
    setJobId(null);
    setResults(null);
    setIsProcessing(false);
    setError(null);
  };

  return (
    <main className="container">
      <header className={styles.header}>
        <div className={styles.logo}>
          <div className={styles.logoIcon}></div>
          <h1>Transaction Intelligence</h1>
        </div>
        <p>AI-powered categorization and anomaly detection</p>
      </header>

      {error && (
        <div className={`${styles.alert} animate-fade-in`}>
          {error}
        </div>
      )}

      {!jobId && !results && !isProcessing && (
        <Dropzone onUploadSuccess={handleUploadSuccess} />
      )}

      {isProcessing && (
        <div className={`${styles.processingState} animate-fade-in`}>
          <div className={styles.spinner}></div>
          <h2>Processing your transactions</h2>
          <p>Our AI is categorizing and analyzing your data for anomalies...</p>
        </div>
      )}

      {results && !isProcessing && (
        <Dashboard results={results} onReset={resetState} />
      )}
    </main>
  );
}
