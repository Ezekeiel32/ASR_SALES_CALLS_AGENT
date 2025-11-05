import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import apiClient, { AggregatedHealth, CommunicationHealthScores } from '../services/api';
import { useMobile } from '../hooks/useMobile';

interface AnalyticsPageProps {
  onBack?: () => void;
  initialTab?: 'retail' | 'email';
}

const AnalyticsPage: React.FC<AnalyticsPageProps> = ({ onBack, initialTab = 'retail' }) => {
  const [activeTab, setActiveTab] = useState<'retail' | 'email'>(initialTab);

  // Update tab when initialTab prop changes
  useEffect(() => {
    if (initialTab) {
      setActiveTab(initialTab);
    }
  }, [initialTab]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retailResults, setRetailResults] = useState<any>(null);
  const [emailResults, setEmailResults] = useState<any>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const isMobile = useMobile();

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.name.endsWith('.csv') || file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        setSelectedFile(file);
        setError(null);
      } else {
        setError('Please select a CSV or Excel file (.csv, .xlsx, .xls)');
      }
    }
  };

  const handleRetailAnalysis = async () => {
    if (!selectedFile) {
      setError('Please select a file first');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await apiClient.analyzeRetailData(selectedFile);
      setRetailResults(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze retail data');
    } finally {
      setLoading(false);
    }
  };

  const handleEmailAnalysis = async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await apiClient.analyzeEmails();
      setEmailResults(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze emails. Ensure Gmail credentials are configured.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      style={{
        padding: isMobile ? '1rem' : '2rem',
        maxWidth: '1200px',
        margin: '0 auto',
      }}
    >
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: isMobile ? '1.5rem' : '2rem', fontWeight: 600, marginBottom: '0.5rem' }}>
          Analytics Dashboard
        </h1>
        <p style={{ color: '#64748B', fontSize: '1rem' }}>
          Analyze retail data and emails using XGBoost and LangGraph workflows
        </p>
      </div>

      {/* Tabs */}
      <div
        style={{
          display: 'flex',
          gap: '1rem',
          borderBottom: '2px solid #E2E8F0',
          marginBottom: '2rem',
        }}
      >
        <button
          onClick={() => setActiveTab('retail')}
          style={{
            padding: '0.75rem 1.5rem',
            border: 'none',
            background: 'transparent',
            borderBottom: activeTab === 'retail' ? '2px solid #14B8A6' : '2px solid transparent',
            color: activeTab === 'retail' ? '#14B8A6' : '#64748B',
            fontWeight: activeTab === 'retail' ? 600 : 400,
            cursor: 'pointer',
            fontSize: '1rem',
            marginBottom: '-2px',
          }}
        >
          Retail Analysis
        </button>
        <button
          onClick={() => setActiveTab('email')}
          style={{
            padding: '0.75rem 1.5rem',
            border: 'none',
            background: 'transparent',
            borderBottom: activeTab === 'email' ? '2px solid #14B8A6' : '2px solid transparent',
            color: activeTab === 'email' ? '#14B8A6' : '#64748B',
            fontWeight: activeTab === 'email' ? 600 : 400,
            cursor: 'pointer',
            fontSize: '1rem',
            marginBottom: '-2px',
          }}
        >
          Email Analysis
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div
          style={{
            padding: '1rem',
            backgroundColor: '#FEE2E2',
            color: '#991B1B',
            borderRadius: '8px',
            marginBottom: '1.5rem',
          }}
        >
          {error}
        </div>
      )}

      {/* Retail Analysis Tab */}
      {activeTab === 'retail' && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          style={{
            backgroundColor: '#fff',
            borderRadius: '12px',
            padding: '2rem',
            border: '1px solid #E2E8F0',
          }}
        >
          <h2 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '1.5rem' }}>
            Retail Data Analysis
          </h2>

          <div style={{ marginBottom: '2rem' }}>
            <label
              style={{
                display: 'block',
                marginBottom: '0.5rem',
                fontWeight: 500,
                fontSize: '1rem',
              }}
            >
              Upload CSV or Excel File
            </label>
            <input
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={handleFileSelect}
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #D1D5DB',
                borderRadius: '8px',
                fontSize: '1rem',
              }}
            />
            {selectedFile && (
              <p style={{ marginTop: '0.5rem', color: '#64748B', fontSize: '0.875rem' }}>
                Selected: {selectedFile.name}
              </p>
            )}
          </div>

          <button
            onClick={handleRetailAnalysis}
            disabled={loading || !selectedFile}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: loading || !selectedFile ? '#94A3B8' : '#14B8A6',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '1rem',
              fontWeight: 600,
              cursor: loading || !selectedFile ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Analyzing...' : 'Run Analysis'}
          </button>

          {/* Results Display */}
          {retailResults && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              style={{ marginTop: '2rem' }}
            >
              <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1rem' }}>
                Analysis Results
              </h3>

              {/* Data Validation Results */}
              {retailResults.validation_results && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ fontWeight: 600, marginBottom: '1rem' }}>Data Validation</h4>
                  <div style={{ backgroundColor: '#F8FAFC', padding: '1rem', borderRadius: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.875rem', color: '#64748B' }}>Data Quality Score</span>
                      <span style={{ fontSize: '1.25rem', fontWeight: 600 }}>
                        {(retailResults.validation_results.quality_score * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                      <div style={{ flex: 1, backgroundColor: '#E2E8F0', borderRadius: '4px', height: '20px', overflow: 'hidden' }}>
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${retailResults.validation_results.quality_score * 100}%` }}
                          transition={{ duration: 0.8 }}
                          style={{
                            height: '100%',
                            backgroundColor: retailResults.validation_results.quality_score >= 0.8 ? '#10B981' :
                              retailResults.validation_results.quality_score >= 0.6 ? '#14B8A6' :
                              retailResults.validation_results.quality_score >= 0.4 ? '#F59E0B' : '#EF4444',
                          }}
                        />
                      </div>
                    </div>
                    {retailResults.validation_results.missing_columns && retailResults.validation_results.missing_columns.length > 0 && (
                      <div style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: '#EF4444' }}>
                        Missing columns: {retailResults.validation_results.missing_columns.join(', ')}
                      </div>
                    )}
                    {retailResults.validation_results.total_records && (
                      <div style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: '#64748B' }}>
                        Total records: {retailResults.validation_results.total_records}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Data Exploration Results */}
              {retailResults.data_exploration && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ fontWeight: 600, marginBottom: '1rem' }}>Data Exploration</h4>
                  <div style={{ backgroundColor: '#F8FAFC', padding: '1rem', borderRadius: '8px' }}>
                    {retailResults.data_exploration.total_records && (
                      <div style={{ marginBottom: '0.5rem', fontSize: '0.875rem' }}>
                        <span style={{ color: '#64748B' }}>Total Records: </span>
                        <span style={{ fontWeight: 600 }}>{retailResults.data_exploration.total_records}</span>
                      </div>
                    )}
                    {retailResults.data_exploration.outlier_analysis && Object.keys(retailResults.data_exploration.outlier_analysis).length > 0 && (
                      <div style={{ marginBottom: '0.5rem' }}>
                        <div style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.25rem' }}>Outlier Analysis</div>
                        {Object.entries(retailResults.data_exploration.outlier_analysis).map(([feature, data]: [string, any]) => (
                          <div key={feature} style={{ fontSize: '0.875rem', color: '#64748B', marginLeft: '1rem' }}>
                            {feature}: {data.count} outliers ({data.percentage.toFixed(1)}%)
                          </div>
                        ))}
                      </div>
                    )}
                    {retailResults.data_exploration.numeric_features && (
                      <div style={{ fontSize: '0.875rem' }}>
                        <span style={{ color: '#64748B' }}>Features Analyzed: </span>
                        <span style={{ fontWeight: 600 }}>{retailResults.data_exploration.numeric_features.join(', ')}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Engineered Features */}
              {retailResults.engineered_features && retailResults.engineered_features.new_features && retailResults.engineered_features.new_features.length > 0 && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ fontWeight: 600, marginBottom: '1rem' }}>Engineered Features</h4>
                  <div style={{ backgroundColor: '#F8FAFC', padding: '1rem', borderRadius: '8px' }}>
                    <div style={{ fontSize: '0.875rem', color: '#64748B', marginBottom: '0.5rem' }}>
                      {retailResults.engineered_features.new_features.length} new features created
                    </div>
                    <div style={{ fontSize: '0.875rem', fontWeight: 500 }}>
                      {retailResults.engineered_features.new_features.join(', ')}
                    </div>
                  </div>
                </div>
              )}

              {/* Summary */}
              {retailResults.summary && (
                <div
                  style={{
                    backgroundColor: '#F8FAFC',
                    padding: '1.5rem',
                    borderRadius: '8px',
                    marginBottom: '1.5rem',
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  <h4 style={{ fontWeight: 600, marginBottom: '0.5rem' }}>Summary</h4>
                  <p style={{ color: '#475569', lineHeight: '1.6' }}>{retailResults.summary}</p>
                </div>
              )}

              {/* Model Performance */}
              {retailResults.analysis_results?.model_performance && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ fontWeight: 600, marginBottom: '1rem' }}>Model Performance</h4>
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: isMobile ? '1fr' : 'repeat(4, 1fr)',
                      gap: '1rem',
                    }}
                  >
                    <div style={{ backgroundColor: '#F8FAFC', padding: '1rem', borderRadius: '8px' }}>
                      <div style={{ fontSize: '0.875rem', color: '#64748B', marginBottom: '0.25rem' }}>
                        RMSE
                      </div>
                      <div style={{ fontSize: '1.5rem', fontWeight: 600 }}>
                        {retailResults.analysis_results.model_performance.rmse?.toFixed(2)}
                      </div>
                    </div>
                    <div style={{ backgroundColor: '#F8FAFC', padding: '1rem', borderRadius: '8px' }}>
                      <div style={{ fontSize: '0.875rem', color: '#64748B', marginBottom: '0.25rem' }}>
                        MAE
                      </div>
                      <div style={{ fontSize: '1.5rem', fontWeight: 600 }}>
                        {retailResults.analysis_results.model_performance.mae?.toFixed(2)}
                      </div>
                    </div>
                    <div style={{ backgroundColor: '#F8FAFC', padding: '1rem', borderRadius: '8px' }}>
                      <div style={{ fontSize: '0.875rem', color: '#64748B', marginBottom: '0.25rem' }}>
                        R² Score
                      </div>
                      <div style={{ fontSize: '1.5rem', fontWeight: 600 }}>
                        {(retailResults.analysis_results.model_performance.r2_score * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div style={{ backgroundColor: '#F8FAFC', padding: '1rem', borderRadius: '8px' }}>
                      <div style={{ fontSize: '0.875rem', color: '#64748B', marginBottom: '0.25rem' }}>
                        MSE
                      </div>
                      <div style={{ fontSize: '1.5rem', fontWeight: 600 }}>
                        {retailResults.analysis_results.model_performance.mse?.toFixed(2)}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Feature Importances */}
              {retailResults.analysis_results?.feature_importances && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ fontWeight: 600, marginBottom: '1rem' }}>Feature Importance</h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {Object.entries(retailResults.analysis_results.feature_importances)
                      .sort((a, b) => b[1] - a[1])
                      .map(([feature, importance]) => (
                        <div key={feature} style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                          <div style={{ minWidth: '150px', fontSize: '0.875rem', fontWeight: 500 }}>
                            {feature}
                          </div>
                          <div
                            style={{
                              flex: 1,
                              height: '24px',
                              backgroundColor: '#E2E8F0',
                              borderRadius: '4px',
                              overflow: 'hidden',
                            }}
                          >
                            <div
                              style={{
                                width: `${(importance as number) * 100}%`,
                                height: '100%',
                                backgroundColor: '#14B8A6',
                                transition: 'width 0.3s',
                              }}
                            />
                          </div>
                          <div style={{ minWidth: '60px', textAlign: 'right', fontSize: '0.875rem', color: '#64748B' }}>
                            {(importance as number).toFixed(3)}
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </motion.div>
      )}

      {/* Email Analysis Tab */}
      {activeTab === 'email' && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          style={{
            backgroundColor: '#fff',
            borderRadius: '12px',
            padding: '2rem',
            border: '1px solid #E2E8F0',
          }}
        >
          <h2 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '1.5rem' }}>
            Email Analysis
          </h2>

          <p style={{ color: '#64748B', marginBottom: '1.5rem' }}>
            Analyze your Gmail inbox using XGBoost to identify urgent emails, extract insights, and generate reply drafts.
          </p>

          <button
            onClick={handleEmailAnalysis}
            disabled={loading}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: loading ? '#94A3B8' : '#14B8A6',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '1rem',
              fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
              marginBottom: '2rem',
            }}
          >
            {loading ? 'Analyzing Emails...' : 'Analyze Emails'}
          </button>

          {/* Results Display */}
          {emailResults && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              style={{ marginTop: '2rem' }}
            >
              <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1rem' }}>
                Email Analysis Results
              </h3>

              {/* Overall Health Score */}
              {emailResults.email_analysis_results?.overall !== undefined && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ fontWeight: 600, marginBottom: '1rem' }}>Overall Communication Health</h4>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ flex: 1, backgroundColor: '#E2E8F0', borderRadius: '8px', height: '32px', overflow: 'hidden' }}>
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${emailResults.email_analysis_results.overall * 100}%` }}
                        transition={{ duration: 0.8 }}
                        style={{
                          height: '100%',
                          backgroundColor: emailResults.email_analysis_results.overall >= 0.8 ? '#10B981' :
                            emailResults.email_analysis_results.overall >= 0.6 ? '#14B8A6' :
                            emailResults.email_analysis_results.overall >= 0.4 ? '#F59E0B' : '#EF4444',
                        }}
                      />
                    </div>
                    <div style={{ minWidth: '80px', textAlign: 'right', fontSize: '1.25rem', fontWeight: 600 }}>
                      {(emailResults.email_analysis_results.overall * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
              )}

              {/* Statistics */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)',
                  gap: '1rem',
                  marginBottom: '1.5rem',
                }}
              >
                <div style={{ backgroundColor: '#F8FAFC', padding: '1rem', borderRadius: '8px' }}>
                  <div style={{ fontSize: '0.875rem', color: '#64748B', marginBottom: '0.25rem' }}>
                    Emails Analyzed
                  </div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 600 }}>{emailResults.emails_count}</div>
                </div>
                <div style={{ backgroundColor: '#F8FAFC', padding: '1rem', borderRadius: '8px' }}>
                  <div style={{ fontSize: '0.875rem', color: '#64748B', marginBottom: '0.25rem' }}>
                    Low Health Emails
                  </div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 600 }}>
                    {emailResults.email_analysis_results?.dimensions ? 
                      Object.values(emailResults.email_analysis_results.dimensions).filter((score: any) => score < 0.4).length : 
                      emailResults.drafts_count}
                  </div>
                </div>
                <div style={{ backgroundColor: '#F8FAFC', padding: '1rem', borderRadius: '8px' }}>
                  <div style={{ fontSize: '0.875rem', color: '#64748B', marginBottom: '0.25rem' }}>
                    Drafts Generated
                  </div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 600 }}>{emailResults.drafts_count}</div>
                </div>
              </div>

              {/* Communication Health Dimensions */}
              {emailResults.email_analysis_results?.dimensions && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ fontWeight: 600, marginBottom: '1rem' }}>Communication Health Dimensions</h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {Object.entries(emailResults.email_analysis_results.dimensions).map(([dimension, score]: [string, any]) => {
                      const dimensionLabels: Record<string, string> = {
                        clarity: 'Clarity & Conciseness',
                        completeness: 'Completeness',
                        correctness: 'Correctness & Coherence',
                        courtesy: 'Courtesy & Tone',
                        audience: 'Audience-Centricity',
                        timeliness: 'Timeliness & Responsiveness'
                      };
                      const label = dimensionLabels[dimension] || dimension;
                      const healthColor = score >= 0.8 ? '#10B981' :
                        score >= 0.6 ? '#14B8A6' :
                        score >= 0.4 ? '#F59E0B' : '#EF4444';
                      
                      return (
                        <div key={dimension} style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                          <div style={{ minWidth: '180px', fontSize: '0.875rem', fontWeight: 500 }}>
                            {label}
                          </div>
                          <div style={{ flex: 1, backgroundColor: '#E2E8F0', borderRadius: '4px', height: '24px', overflow: 'hidden' }}>
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: `${score * 100}%` }}
                              transition={{ duration: 0.8 }}
                              style={{
                                height: '100%',
                                backgroundColor: healthColor,
                              }}
                            />
                          </div>
                          <div style={{ minWidth: '60px', textAlign: 'right', fontSize: '0.875rem', color: '#64748B' }}>
                            {(score * 100).toFixed(1)}%
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Detailed Dimension Scores with Reasoning */}
              {emailResults.communication_health_scores && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ fontWeight: 600, marginBottom: '1rem' }}>Detailed Analysis</h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {Object.entries(emailResults.communication_health_scores).map(([dimension, data]: [string, any]) => {
                      const dimensionLabels: Record<string, string> = {
                        clarity: 'Clarity & Conciseness',
                        completeness: 'Completeness',
                        correctness: 'Correctness & Coherence',
                        courtesy: 'Courtesy & Tone',
                        audience: 'Audience-Centricity',
                        timeliness: 'Timeliness & Responsiveness'
                      };
                      const label = dimensionLabels[dimension] || dimension;
                      
                      return (
                        <div key={dimension} style={{ backgroundColor: '#F8FAFC', padding: '1rem', borderRadius: '8px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                            <div style={{ fontWeight: 600 }}>{label}</div>
                            <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>
                              {data.overall ? (data.overall * 100).toFixed(1) : 'N/A'}%
                            </div>
                          </div>
                          {data.reasoning && (
                            <p style={{ fontSize: '0.875rem', color: '#64748B', margin: 0, lineHeight: '1.5' }}>
                              {data.reasoning}
                            </p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Summary */}
              {emailResults.email_summary && (
                <div
                  style={{
                    backgroundColor: '#F8FAFC',
                    padding: '1.5rem',
                    borderRadius: '8px',
                    marginBottom: '1.5rem',
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  <h4 style={{ fontWeight: 600, marginBottom: '0.5rem' }}>Summary</h4>
                  <p style={{ color: '#475569', lineHeight: '1.6' }}>{emailResults.email_summary}</p>
                </div>
              )}
            </motion.div>
          )}
        </motion.div>
      )}
    </motion.div>
  );
};

export default AnalyticsPage;



