import React from 'react';
import { motion } from 'framer-motion';
import { UsersIcon } from './IconComponents'; // Assuming you have these

// Define the structure of the summary JSON
interface McpSummary {
    content: {
        executive_summary?: string;
        meeting_metadata?: { title?: string; date?: string; };
        participants?: Array<{ id: string; name: string; role: string; }>;
        discussion?: Array<{ topic: string; summary: string; segments: Array<{ speaker_name: string; content: string; }> }>;
        decisions?: Array<{ decision_id: string; title: string; decision_text: string; }>;
        action_items?: Array<{ action_id: string; title: string; assigned_to: { name: string; }; due_date: string; priority: string; status: string; }>;
        key_insights?: Array<{ insight_id: string; description: string; }>;
    };
}

const SummarySection: React.FC<{ title: string; children: React.ReactNode; delay?: number }> = ({ title, children, delay = 0 }) => (
    <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: delay * 0.1, duration: 0.5 }}
        style={{ marginBottom: '2.5rem' }}
    >
        <h3 style={sectionTitleStyle}>{title}</h3>
        {children}
    </motion.div>
);

const PriorityBadge: React.FC<{ priority: string }> = ({ priority }) => {
    const getPriorityStyle = (p: string) => {
        switch (p.toLowerCase()) {
            case 'critical': return { color: '#DC2626', bgColor: '#FEE2E2' };
            case 'high': return { color: '#D97706', bgColor: '#FEF3C7' };
            case 'medium': return { color: '#6D28D9', bgColor: '#EDE9FE' };
            case 'low': return { color: '#059669', bgColor: '#D1FAE5' };
            default: return { color: '#4B5563', bgColor: '#F3F4F6' };
        }
    };
    const style = getPriorityStyle(priority);
    return (
        <span style={{
            padding: '0.25rem 0.75rem',
            borderRadius: '9999px',
            fontSize: '0.75rem',
            fontWeight: 500,
            color: style.color,
            backgroundColor: style.bgColor,
        }}>
            {priority}
        </span>
    );
};

export const SummaryDisplay: React.FC<{ summary: McpSummary }> = ({ summary }) => {
    const {
        executive_summary,
        participants,
        discussion,
        decisions,
        action_items,
        key_insights
    } = summary?.content || {};

    const formatSummaryText = (text: string) => {
        const lines = text.split('\\n');
        return lines.map((line, index) => {
            if (line.startsWith('🎯') || line.startsWith('🧩') || line.startsWith('✅') || line.startsWith('📌') || line.startsWith('📈') || line.startsWith('⚠️')) {
                const [emoji, ...rest] = line.split(' ');
                return <p key={index} style={{ margin: '0.5rem 0' }}><span style={{ marginRight: '0.75rem' }}>{emoji}</span><strong>{rest.join(' ').split(':')[0]}:</strong> {rest.join(' ').split(':').slice(1).join(':')}</p>;
            }
            return <p key={index} style={{ margin: '0.5rem 0' }}>{line}</p>;
        });
    };

    return (
        <div style={{ fontFamily: 'sans-serif', color: '#1F2937' }}>
            {executive_summary && (
                <SummarySection title="Executive Summary" delay={0}>
                    <div style={cardStyle}>
                        {formatSummaryText(executive_summary)}
                    </div>
                </SummarySection>
            )}

            {action_items && action_items.length > 0 && (
                <SummarySection title="Action Items" delay={1}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        {action_items.map(item => (
                            <div key={item.action_id} style={cardStyle}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                    <p style={{ fontWeight: 'bold', margin: 0 }}>{item.title}</p>
                                    <PriorityBadge priority={item.priority} />
                                </div>
                                <div style={{ display: 'flex', gap: '1.5rem', color: '#6B7280', fontSize: '0.875rem', marginTop: '0.75rem' }}>
                                    {item.assigned_to?.name && <span style={metaItemStyle}><UsersIcon width={14} /> {item.assigned_to.name}</span>}
                                    {item.due_date && <span style={metaItemStyle}>{new Date(item.due_date).toLocaleDateString('he-IL')}</span>}
                                    {item.status && <span style={metaItemStyle}>{item.status}</span>}
                                </div>
                            </div>
                        ))}
                    </div>
                </SummarySection>
            )}

            {decisions && decisions.length > 0 && (
                <SummarySection title="Key Decisions" delay={2}>
                     <ul style={{ margin: 0, paddingLeft: '1.5rem' }}>
                        {decisions.map(decision => (
                            <li key={decision.decision_id} style={{ marginBottom: '0.75rem' }}>
                                <strong>{decision.title}:</strong> {decision.decision_text}
                            </li>
                        ))}
                    </ul>
                </SummarySection>
            )}
            
            {discussion && discussion.length > 0 && (
                <SummarySection title="Discussion Topics" delay={3}>
                    {discussion.map(topic => (
                        <div key={topic.topic} style={{ marginBottom: '1.5rem' }}>
                            <h4 style={{ fontWeight: 'bold', borderBottom: '1px solid #E5E7EB', paddingBottom: '0.5rem', marginBottom: '1rem' }}>{topic.topic}</h4>
                            <p style={{ fontStyle: 'italic', color: '#6B7280' }}>{topic.summary}</p>
                            {topic.segments.map((seg, i) => (
                                <div key={i} style={{ fontSize: '0.9rem', marginBottom: '0.5rem'}}>
                                    <strong>{seg.speaker_name}:</strong> {seg.content}
                                </div>
                            ))}
                        </div>
                    ))}
                </SummarySection>
            )}
            
            {key_insights && key_insights.length > 0 && (
                 <SummarySection title="Key Insights" delay={4}>
                     <ul style={{ margin: 0, paddingLeft: '1.5rem' }}>
                        {key_insights.map(insight => (
                            <li key={insight.insight_id} style={{ marginBottom: '0.75rem' }}>{insight.description}</li>
                        ))}
                    </ul>
                </SummarySection>
            )}

            {participants && participants.length > 0 && (
                <SummarySection title="Participants" delay={5}>
                    <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                        {participants.map(p => (
                            <span key={p.id} style={{ backgroundColor: '#F3F4F6', padding: '0.5rem 1rem', borderRadius: '8px' }}>
                                {p.name} ({p.role})
                            </span>
                        ))}
                    </div>
                </SummarySection>
            )}
        </div>
    );
};

const sectionTitleStyle: React.CSSProperties = {
    fontSize: '1.5rem',
    fontWeight: 'bold',
    marginBottom: '1rem',
    color: '#111827',
    borderBottom: '2px solid #14B8A6',
    paddingBottom: '0.5rem',
};

const cardStyle: React.CSSProperties = {
    backgroundColor: '#FFFFFF',
    padding: '1.5rem',
    borderRadius: '8px',
    border: '1px solid #E5E7EB',
    lineHeight: 1.7,
};

const metaItemStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem'
};
