import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Meeting, MeetingStatus } from '../types';
import apiClient, { MeetingCommunicationHealth } from '../services/api';
import { PencilIcon, TrashIcon, CopyIcon, MicIcon } from './IconComponents';
import { useMobile } from '../hooks/useMobile';
import { UnidentifiedSpeakerCard } from './UnidentifiedSpeakerCard';
import { ActionItemsView } from './ActionItemsView';
import { SummaryDisplay } from './SummaryDisplay'; // Import the new component

const MeetingDetailPage: React.FC<{ meeting: Meeting; onBack: () => void; onRefresh?: () => void; }> = ({ meeting, onBack, onRefresh }) => {
  const [activeTab, setActiveTab] = useState('summary');
  const isMobile = useMobile();

  const getStatusInfo = (status: MeetingStatus) => {
    switch (status) {
      case MeetingStatus.Completed: return { text: 'הושלם', color: '#10B981' };
      case MeetingStatus.Processing: return { text: 'בעיבוד', color: '#F59E0B' };
      case MeetingStatus.Failed: return { text: 'נכשל', color: '#EF4444' };
      default: return { text: 'לא ידוע', color: '#6B7280' };
    }
  };

  const statusInfo = getStatusInfo(meeting.status);

  return (
    <div style={{ 
      paddingTop: '0', 
      paddingBottom: '2rem',
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      minHeight: 0
    }}>
      {/* Header */}
      <div style={{ marginBottom: isMobile ? '1.5rem' : '2rem', flexShrink: 0 }}>
        <button onClick={onBack} style={isMobile ? mobileBackButtonStyle : backButtonStyle}>&rarr; חזרה לפגישות</button>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: isMobile ? 'flex-start' : 'center', flexDirection: isMobile ? 'column' : 'row', gap: isMobile ? '1rem' : '0' }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <h1 style={{ fontSize: isMobile ? '1.5rem' : '2.25rem', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
              <span style={{ wordBreak: 'break-word' }}>{meeting.title}</span>
              {!isMobile && <button style={{...iconButtonSmall, color: '#6B7280'}}><PencilIcon width={20} height={20}/></button>}
            </h1>
            <div style={{ display: 'flex', gap: isMobile ? '0.5rem' : '1rem', color: '#6B7280', marginTop: '0.5rem', flexWrap: 'wrap', fontSize: isMobile ? '0.85rem' : '1rem' }}>
              <span>
                {typeof meeting.date === 'string' 
                    ? new Date(meeting.date).toLocaleString('he-IL', { dateStyle: 'medium', timeStyle: 'short' })
                    : meeting.date.toLocaleString('he-IL', { dateStyle: 'medium', timeStyle: 'short' })
                }
              </span>
              {meeting.duration && (
                <>
              <span>•</span>
              <span>{meeting.duration} דקות</span>
                </>
              )}
              <span>•</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontWeight: 500, color: statusInfo.color }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: statusInfo.color }}></div>
                {statusInfo.text}
              </span>
            </div>
          </div>
          {!isMobile && (
            <div style={{ display: 'flex', gap: '0.75rem', flexShrink: 0 }}>
              <motion.button 
                style={{...secondaryButtonStyle}}
                whileHover={{ backgroundColor: '#F9FAFB', borderColor: '#9CA3AF' }}
                whileTap={{ scale: 0.98 }}
              >
                שתף
              </motion.button>
              <motion.button 
                style={{...primaryButtonStyle}}
                whileHover={{ backgroundColor: '#0D9488' }}
                whileTap={{ scale: 0.98 }}
              >
                יצא
              </motion.button>
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div style={{ borderBottom: '1px solid #E5E7EB', marginBottom: isMobile ? '1rem' : '2rem', flexShrink: 0, overflowX: 'auto', WebkitOverflowScrolling: 'touch' }}>
        <div style={{ display: 'flex', gap: isMobile ? '0.5rem' : '0', minWidth: isMobile ? 'max-content' : 'auto' }}>
          <button onClick={() => setActiveTab('transcript')} style={{...getTabStyle(isMobile, activeTab === 'transcript')}}>תמלול</button>
          <button onClick={() => setActiveTab('summary')} style={{...getTabStyle(isMobile, activeTab === 'summary')}}>סיכום AI</button>
          <button onClick={() => setActiveTab('speakers')} style={{...getTabStyle(isMobile, activeTab === 'speakers')}}>דוברים</button>
          <button onClick={() => setActiveTab('analytics')} style={{...getTabStyle(isMobile, activeTab === 'analytics')}}>ניתוח</button>
        </div>
      </div>

      {/* Tab Content */}
      <div style={{ 
        flex: 1, 
        overflowY: 'auto', 
        overflowX: 'hidden',
        minHeight: 0 // Important for flex scrolling
      }}>
        {activeTab === 'transcript' && <TranscriptView meeting={meeting} />}
        {activeTab === 'summary' && <SummaryView meeting={meeting} />}
        {activeTab === 'speakers' && <SpeakersView meeting={meeting} onRefresh={onRefresh} />}
        {activeTab === 'analytics' && <AnalyticsView meeting={meeting} />}
      </div>
    </div>
  );
};

const TranscriptView = ({ meeting }: { meeting: Meeting }) => {
    const isMobile = useMobile();
    const [transcript, setTranscript] = useState(meeting.transcript);
    const [segments, setSegments] = useState(meeting.transcriptSegments);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (meeting.id && !transcript && !segments) {
            loadTranscript();
        }
    }, [meeting.id]);

    const loadTranscript = async () => {
        if (!meeting.id) return;
        try {
            setLoading(true);
            const response = await apiClient.getMeetingTranscript(meeting.id);
            // Format segments from API response
            const formattedSegments = response.transcript_segments.map(seg => {
                const startMinutes = Math.floor(seg.start / 60);
                const startSeconds = Math.floor(seg.start % 60);
                return {
                    speakerLabel: seg.speaker || seg.speaker_id || 'Unknown',
                    timestamp: `${startMinutes}:${startSeconds.toString().padStart(2, '0')}`,
                    text: seg.text,
                };
            });
            setSegments(formattedSegments);
            // Also set full transcript as joined text
            setTranscript(response.transcript_segments.map(s => s.text).join(' '));
        } catch (err) {
            console.error('Failed to load transcript:', err);
        } finally {
            setLoading(false);
        }
    };

    return (
    <div style={getPanelStyle(isMobile)}>
            {loading ? <p>טוען תמלול...</p> : (
                segments && segments.length > 0 ? (
                    segments.map((segment, index) => (
            <div key={index} style={{ marginBottom: '1.5rem', display: 'flex', gap: '1rem' }}>
                            <img src={meeting.speakers?.find(s => s.name === segment.speakerLabel || s.label === segment.speakerLabel)?.avatarUrl || `https://i.pravatar.cc/150?u=${segment.speakerLabel}`} alt={segment.speakerLabel} style={{width: 36, height: 36, borderRadius: '50%'}}/>
                <div style={{flex: 1}}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <strong style={{ color: '#111827', fontWeight: 600 }}>{segment.speakerLabel} • <span style={{color: '#6B7280', fontWeight: 400}}>{segment.timestamp}</span></strong>
                                    <button style={iconButtonSmall} onClick={() => navigator.clipboard.writeText(segment.text)}><CopyIcon width={16} height={16}/></button>
                    </div>
                    <p style={{ margin: '0.25rem 0', lineHeight: 1.6, color: '#374151' }}>{segment.text}</p>
                </div>
            </div>
        ))
                ) : <p>{transcript || 'אין תמלול זמין.'}</p>
            )}
    </div>
);
};

const SummaryView = ({ meeting }: { meeting: Meeting }) => {
    const isMobile = useMobile();
    const [summary, setSummary] = useState<any>(meeting.summary || null);
    const [isLoading, setIsLoading] = useState(false);

    const loadSummary = async () => {
        if (!meeting.id) return;
        try {
            setIsLoading(true);
            const response = await apiClient.getMeetingSummary(meeting.id);
            if (response.summary && typeof response.summary === 'object') {
                setSummary(response.summary);
            } else if (meeting.status === MeetingStatus.Processing) {
                setSummary({ content: { executive_summary: 'הפגישה עדיין בעיבוד. הסיכום יהיה זמין כאשר העיבוד יושלם.' } });
            } else {
                setSummary({ content: { executive_summary: 'אין סיכום זמין לפגישה זו.' } });
            }
        } catch (err) {
            console.error('Failed to load summary:', err);
            setSummary({ content: { executive_summary: 'שגיאה בטעינת הסיכום.' } });
        } finally {
            setIsLoading(false);
        }
    };
    
    useEffect(() => {
        if (!summary && meeting.id) {
            loadSummary();
        }
    }, [meeting.id, summary]);

    return (
        <div style={getPanelStyle(isMobile)}>
            {isLoading ? (
                <p>טוען סיכום...</p>
            ) : summary ? (
                <SummaryDisplay summary={summary} />
            ) : (
                <p>אין סיכום זמין.</p>
            )}
        </div>
    );
};

const SpeakersView = ({ meeting, onRefresh }: { meeting: Meeting; onRefresh?: () => void }) => {
    const isMobile = useMobile();
    const [unidentifiedSpeakers, setUnidentifiedSpeakers] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (meeting.id) {
            loadUnidentifiedSpeakers();
        }
    }, [meeting.id]);

    const loadUnidentifiedSpeakers = async () => {
        try {
            setLoading(true);
            const response = await apiClient.getUnidentifiedSpeakers(meeting.id);
            // Convert response format to array of speakers with suggestions and snippet URLs
            const speakersArray = Object.entries(response.unidentified_speakers || {}).map(([label, data]: [string, any]) => ({
                label,
                snippet_url: data.snippet_url || data.snippet_path,
                name_suggestions: data.suggestions?.map(s => ({
                    speaker_label: label,
                    suggested_name: s.name,
                    confidence: s.confidence,
                })) || [],
            }));
            setUnidentifiedSpeakers(speakersArray);
        } catch (err) {
            console.error('Failed to load unidentified speakers:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleAssignName = async (speakerLabel: string, name: string) => {
        if (!meeting.id) return;
        try {
            await apiClient.assignSpeakerName(meeting.id, speakerLabel, name);
            onRefresh?.();
            loadUnidentifiedSpeakers();
        } catch (err) {
            console.error('Failed to assign speaker name:', err);
            alert('שגיאה בהשמת שם הדובר');
        }
    };

    return (
    <div style={{...getPanelStyle(isMobile), display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fill, minmax(350px, 1fr))', gap: isMobile ? '1rem' : '1.5rem'}}>
            {meeting.speakers?.map(speaker => (
                <motion.div 
                    key={speaker.id} 
                    style={speakerCardStyle}
                    layout
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <img src={speaker.avatar_url || `https://i.pravatar.cc/150?u=${speaker.id}`} alt={speaker.name} style={{width: 50, height: 50, borderRadius: '50%', flexShrink: 0}}/>
                    <div style={{flex: 1, minWidth: 0}}>
                        <h4 style={{margin: 0, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'}}>{speaker.name || speaker.label}</h4>
                        <p style={{margin: 0, color: '#6B7280', fontSize: '0.9rem'}}>{speaker.label}</p>
                    </div>
                    <button style={{...iconButtonSmall, color: '#9CA3AF'}}><PencilIcon width={18} height={18}/></button>
                </motion.div>
            ))}
            <AnimatePresence>
                {unidentifiedSpeakers.map((speaker: any) => (
                    <UnidentifiedSpeakerCard 
                        key={speaker.label}
                        speaker={speaker}
                        meetingId={meeting.id}
                        onNameAssigned={() => {
                            onRefresh?.();
                            loadUnidentifiedSpeakers();
                        }}
                    />
                ))}
            </AnimatePresence>
        </div>
    );
};

const AnalyticsView = ({ meeting }: { meeting: Meeting }) => {
    const isMobile = useMobile();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [communicationHealth, setCommunicationHealth] = useState<MeetingCommunicationHealth | null>(null);
    const [transcript, setTranscript] = useState<string>('');

    useEffect(() => {
        // Load communication health if available
        if (meeting.id) {
            loadCommunicationHealth();
        }
    }, [meeting.id]);

    const loadCommunicationHealth = async () => {
        if (!meeting.id) return;
        try {
            const health = await apiClient.getMeetingCommunicationHealth(meeting.id);
            setCommunicationHealth(health);
        } catch (err) {
            // If not found, that's okay - user can run analysis
            console.debug('Communication health not yet available:', err);
        }
    };

    const runCommunicationHealthAnalysis = async () => {
        if (!meeting.id) return;
        
        setLoading(true);
        setError(null);
        
        try {
            // Use the dedicated communication health endpoint instead of the workflow endpoint
            const health = await apiClient.getMeetingCommunicationHealth(meeting.id);
            setCommunicationHealth(health);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to run communication health analysis');
        } finally {
            setLoading(false);
        }
    };

    return (
    <div style={getPanelStyle(isMobile)}>
        {/* Communication Health Analysis Section */}
        <div style={{ marginBottom: '2rem' }}>
            <h3 style={chartTitleStyle}>Communication Health Analysis</h3>
            <p style={{ color: '#6B7280', marginBottom: '1rem', fontSize: '0.9rem' }}>
                Analyze meeting communication across 6 dimensions: clarity, completeness, correctness, courtesy, audience-centricity, and timeliness
            </p>
            
            {!communicationHealth && (
                <button
                    onClick={runCommunicationHealthAnalysis}
                    disabled={loading || !meeting.id}
                    style={{
                        padding: '0.75rem 1.5rem',
                        backgroundColor: loading || !meeting.id ? '#94A3B8' : '#14B8A6',
                        color: 'white',
                        border: 'none',
                        borderRadius: '8px',
                        fontSize: '1rem',
                        fontWeight: 600,
                        cursor: loading || !meeting.id ? 'not-allowed' : 'pointer',
                        marginBottom: '1rem',
                    }}
                >
                    {loading ? 'Analyzing Communication Health...' : 'Run Communication Health Analysis'}
                </button>
            )}

            {error && (
                <div style={{
                    padding: '1rem',
                    backgroundColor: '#FEE2E2',
                    color: '#991B1B',
                    borderRadius: '8px',
                    marginBottom: '1rem',
                }}>
                    {error}
                </div>
            )}

            {communicationHealth && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    style={{ marginTop: '1rem' }}
                >
                    {/* Overall Health Score */}
                    {communicationHealth.aggregated_health?.overall !== undefined && (
                        <div style={{ marginBottom: '1.5rem' }}>
                            <h4 style={{ fontWeight: 600, marginBottom: '1rem', fontSize: '1.1rem' }}>
                                Overall Communication Health
                            </h4>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                <div style={{ flex: 1, backgroundColor: '#E2E8F0', borderRadius: '8px', height: '40px', overflow: 'hidden' }}>
                                    <motion.div
                                        initial={{ width: 0 }}
                                        animate={{ width: `${communicationHealth.aggregated_health.overall * 100}%` }}
                                        transition={{ duration: 0.8 }}
                                        style={{
                                            height: '100%',
                                            backgroundColor: communicationHealth.aggregated_health.overall >= 0.8 ? '#10B981' :
                                                communicationHealth.aggregated_health.overall >= 0.6 ? '#14B8A6' :
                                                communicationHealth.aggregated_health.overall >= 0.4 ? '#F59E0B' : '#EF4444',
                                        }}
                                    />
                                </div>
                                <div style={{ minWidth: '100px', textAlign: 'right', fontSize: '1.5rem', fontWeight: 600 }}>
                                    {(communicationHealth.aggregated_health.overall * 100).toFixed(1)}%
                                </div>
                            </div>
                            <div style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: '#64748B' }}>
                                {communicationHealth.aggregated_health.overall >= 0.8 ? 'Excellent' :
                                    communicationHealth.aggregated_health.overall >= 0.6 ? 'Good' :
                                    communicationHealth.aggregated_health.overall >= 0.4 ? 'Fair' : 'Poor'} Communication Health
                            </div>
                        </div>
                    )}

                    {/* Communication Health Dimensions */}
                    {communicationHealth.aggregated_health?.dimensions && (
                        <div style={{ marginBottom: '1.5rem' }}>
                            <h4 style={{ fontWeight: 600, marginBottom: '1rem', fontSize: '1.1rem' }}>
                                Dimension Scores
                            </h4>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                {Object.entries(communicationHealth.aggregated_health.dimensions).map(([dimension, score]: [string, any]) => {
                                    const dimensionLabels: Record<string, string> = {
                                        clarity: 'Clarity & Conciseness',
                                        completeness: 'Completeness',
                                        correctness: 'Correctness & Coherence',
                                        courtesy: 'Courtesy & Tone',
                                        audience: 'Audience-Centricity',
                                        timeliness: 'Timeliness & Efficiency'
                                    };
                                    const label = dimensionLabels[dimension] || dimension;
                                    const healthColor = score >= 0.8 ? '#10B981' :
                                        score >= 0.6 ? '#14B8A6' :
                                        score >= 0.4 ? '#F59E0B' : '#EF4444';
                                    
                                    return (
                                        <div key={dimension} style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                            <div style={{ minWidth: '200px', fontSize: '0.875rem', fontWeight: 500 }}>
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

                    {/* Per-Speaker Health Scores */}
                    {communicationHealth.aggregated_health?.per_speaker && Object.keys(communicationHealth.aggregated_health.per_speaker).length > 0 && (
                        <div style={{ marginBottom: '1.5rem' }}>
                            <h4 style={{ fontWeight: 600, marginBottom: '1rem', fontSize: '1.1rem' }}>
                                Per-Speaker Health Scores
                            </h4>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                {Object.entries(communicationHealth.aggregated_health.per_speaker).map(([speaker, score]: [string, any]) => {
                                    const healthColor = score >= 0.8 ? '#10B981' :
                                        score >= 0.6 ? '#14B8A6' :
                                        score >= 0.4 ? '#F59E0B' : '#EF4444';
                                    
                                    return (
                                        <div key={speaker} style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                            <div style={{ minWidth: '150px', fontSize: '0.875rem', fontWeight: 500 }}>
                                                {speaker}
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

                    {/* Detailed Dimension Analysis with Reasoning */}
                    {communicationHealth.communication_health_scores && (
                        <div style={{ marginBottom: '1.5rem' }}>
                            <h4 style={{ fontWeight: 600, marginBottom: '1rem', fontSize: '1.1rem' }}>
                                Detailed Dimension Analysis
                            </h4>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                                {Object.entries(communicationHealth.communication_health_scores).map(([dimension, data]: [string, any]) => {
                                    const dimensionLabels: Record<string, string> = {
                                        clarity: 'Clarity & Conciseness',
                                        completeness: 'Completeness',
                                        correctness: 'Correctness & Coherence',
                                        courtesy: 'Courtesy & Tone',
                                        audience: 'Audience-Centricity',
                                        timeliness: 'Timeliness & Efficiency'
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
                                            {/* Per-speaker breakdown for clarity and courtesy */}
                                            {data.per_speaker && Object.keys(data.per_speaker).length > 0 && (
                                                <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid #E2E8F0' }}>
                                                    <div style={{ fontSize: '0.75rem', fontWeight: 600, marginBottom: '0.5rem', color: '#64748B' }}>
                                                        Per-Speaker Scores:
                                                    </div>
                                                    {Object.entries(data.per_speaker).map(([speaker, score]: [string, any]) => (
                                                        <div key={speaker} style={{ fontSize: '0.875rem', marginBottom: '0.25rem' }}>
                                                            <span style={{ fontWeight: 500 }}>{speaker}:</span> {(score * 100).toFixed(1)}%
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    {/* Health Explanation */}
                    {communicationHealth.health_explanation && (
                        <div style={{ marginBottom: '1.5rem' }}>
                            <h4 style={{ fontWeight: 600, marginBottom: '1rem', fontSize: '1.1rem' }}>
                                Analysis Summary
                            </h4>
                            <div style={{
                                backgroundColor: '#F8FAFC',
                                padding: '1.5rem',
                                borderRadius: '8px',
                                whiteSpace: 'pre-wrap',
                            }}>
                                <p style={{ color: '#475569', lineHeight: '1.6', margin: 0, fontSize: '0.875rem' }}>
                                    {communicationHealth.health_explanation}
                                </p>
                            </div>
                        </div>
                    )}
                </motion.div>
            )}
        </div>

        {/* Basic Analytics */}
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: isMobile ? '1rem' : '2rem', marginTop: '2rem' }}>
            <div>
                <h3 style={chartTitleStyle}>זמן דיבור</h3>
                <div style={{...chartContainerStyle, height: '250px'}}>
                    {meeting.speakers?.map(s => (
                        <div key={s.id} style={{display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem'}}>
                            <img src={s.avatarUrl} alt={s.name} style={{width: 24, height: 24, borderRadius: '50%'}}/>
                            <span style={{width: '80px'}}>{s.name}</span>
                            <div style={{flex: 1, backgroundColor: '#E5E7EB', borderRadius: '4px', overflow: 'hidden'}}>
                                <motion.div initial={{width: 0}} animate={{width: `${Math.random() * 80 + 20}%`}} transition={{duration: 0.8}} style={{height: '20px', backgroundColor: '#14B8A6', borderRadius: '4px'}}></motion.div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
            <div>
                <h3 style={chartTitleStyle}>ניתוח סנטימנט</h3>
                <div style={{...chartContainerStyle, height: '250px', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                    <p style={{ color: '#6B7280', fontSize: '0.9rem' }}>תרשים סנטימנט לאורך זמן...</p>
                </div>
            </div>
        </div>
    </div>
    );
};


// Styles
const backButtonStyle: React.CSSProperties = { 
  marginBottom: '1rem', 
  border: 'none', 
  background: 'none', 
  color: '#14B8A6', 
  cursor: 'pointer', 
  fontSize: '1rem', 
  fontWeight: 500,
  minHeight: '44px',
  minWidth: '44px',
  padding: '0.5rem'
};

const mobileBackButtonStyle: React.CSSProperties = { 
  ...backButtonStyle,
  fontSize: '0.9rem',
  marginBottom: '0.75rem'
};

const getTabStyle = (isMobile: boolean, isActive: boolean): React.CSSProperties => ({
  padding: isMobile ? '0.75rem 1rem' : '1rem 1.5rem',
  border: 'none',
  background: 'none',
  borderBottom: isActive ? '2px solid #14B8A6' : '2px solid transparent',
  color: isActive ? '#14B8A6' : '#6B7280',
  cursor: 'pointer',
  fontSize: isMobile ? '0.9rem' : '1rem',
  fontWeight: isActive ? 600 : 500,
  whiteSpace: 'nowrap',
  minHeight: '44px',
  transition: 'color 0.2s, border-color 0.2s'
});

const tabStyle: React.CSSProperties = {
  padding: '1rem 1.5rem',
  border: 'none',
  background: 'none',
  borderBottom: '2px solid transparent',
  color: '#6B7280',
  cursor: 'pointer',
  fontSize: '1rem',
  fontWeight: 500,
  transition: 'color 0.2s, border-color 0.2s'
};

const activeTabStyle: React.CSSProperties = {
  borderBottom: '2px solid #14B8A6',
  color: '#14B8A6',
  fontWeight: 600
};
const primaryButtonStyle: React.CSSProperties = { 
  padding: '0.6rem 1.25rem', 
  border: 'none', 
  borderRadius: '8px', 
  backgroundColor: '#14B8A6', 
  color: 'white', 
  cursor: 'pointer', 
  fontSize: '0.9rem', 
  fontWeight: 600,
  transition: 'background-color 0.2s, transform 0.1s'
};
const secondaryButtonStyle: React.CSSProperties = { 
  padding: '0.6rem 1.25rem', 
  border: '1px solid #D1D5DB', 
  borderRadius: '8px', 
  backgroundColor: 'white', 
  color: '#374151', 
  cursor: 'pointer', 
  fontSize: '0.9rem', 
  fontWeight: 600,
  transition: 'background-color 0.2s, border-color 0.2s, transform 0.1s'
};
const iconButtonSmall: React.CSSProperties = { 
  background: 'none', 
  border: 'none', 
  cursor: 'pointer', 
  padding: '0.25rem', 
  color: '#9CA3AF',
  minWidth: '44px',
  minHeight: '44px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center'
};

const getPanelStyle = (isMobile: boolean): React.CSSProperties => ({
  backgroundColor: 'white', 
  padding: isMobile ? '1rem' : '2rem', 
  borderRadius: '12px', 
  border: '1px solid #E5E7EB',
  width: '100%',
  boxSizing: 'border-box'
});

const panelStyle: React.CSSProperties = { 
  backgroundColor: 'white', 
  padding: '2rem', 
  borderRadius: '12px', 
  border: '1px solid #E5E7EB',
  width: '100%',
  boxSizing: 'border-box'
};
const speakerCardStyle: React.CSSProperties = { display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem', borderRadius: '12px', border: '1px solid #E5E7EB', backgroundColor: '#fff', boxShadow: '0 1px 3px rgba(0,0,0,0.03)' };
const chartTitleStyle: React.CSSProperties = { fontSize: '1.25rem', fontWeight: 600, marginBottom: '1.5rem' };
const chartContainerStyle: React.CSSProperties = { padding: '1rem', borderRadius: '8px', border: '1px solid #E5E7EB' };

export default MeetingDetailPage;
