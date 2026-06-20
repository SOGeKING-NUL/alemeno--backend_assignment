import React from 'react';
import styles from './Dashboard.module.css';

export default function Dashboard({ results, onReset }) {
  if (!results) return null;

  const { transactions, summary } = results;

  return (
    <div className={`animate-fade-in ${styles.dashboard}`}>
      <div className={styles.header}>
        <h2>Analysis Results</h2>
        <button className="btn" onClick={onReset}>Upload Another</button>
      </div>

      <div className="card">
        <h3 className={styles.sectionTitle}>Executive Summary</h3>
        <p className={styles.narrative}>{summary?.narrative || 'No summary available.'}</p>
        
        <div className={styles.metricsGrid}>
          <div className={styles.metricCard}>
            <span className={styles.metricLabel}>Total Transactions</span>
            <span className={styles.metricValue}>{summary?.total_records || transactions?.length || 0}</span>
          </div>
          <div className={styles.metricCard}>
            <span className={styles.metricLabel}>Anomalies Detected</span>
            <span className={`${styles.metricValue} ${summary?.anomaly_count > 0 ? styles.alertValue : ''}`}>
              {summary?.anomaly_count || 0}
            </span>
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className={styles.sectionTitle}>Transaction Details</h3>
        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Date</th>
                <th>Description / Merchant</th>
                <th>Amount</th>
                <th>Category</th>
                <th>Anomaly</th>
              </tr>
            </thead>
            <tbody>
              {transactions?.map((t) => (
                <tr key={t.id} className={t.is_anomaly ? styles.anomalyRow : ''}>
                  <td>{new Date(t.date).toLocaleDateString()}</td>
                  <td>{t.merchant || t.description}</td>
                  <td className={t.amount < 0 ? styles.expense : styles.income}>
                    {t.amount < 0 ? '-' : ''}{t.currency === 'USD' ? '$' : '₹'}{Math.abs(t.amount).toFixed(2)}
                  </td>
                  <td>
                    <span className={styles.categoryPill}>{t.category}</span>
                  </td>
                  <td>
                    {t.is_anomaly ? (
                      <span className={styles.anomalyBadge}>Flagged</span>
                    ) : (
                      <span className={styles.normalBadge}>Normal</span>
                    )}
                  </td>
                </tr>
              ))}
              {(!transactions || transactions.length === 0) && (
                <tr>
                  <td colSpan="5" className={styles.emptyState}>No transactions found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
