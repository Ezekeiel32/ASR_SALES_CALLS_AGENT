import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Meeting, MeetingStatus } from '../types';
import { TrashIcon } from './IconComponents';

interface MeetingCardProps {
  meeting: Meeting;
  isListView: boolean;
  onClick: () => void;
  onDelete?: (meeting: Meeting) => void;
}

const getStatusStyle = (status: MeetingStatus): { color: string, bg: string } => {
  switch (status) {
    case MeetingStatus.Completed: return { color: '#166534', bg: '#D1FAE5' }; // Green
    case MeetingStatus.Processing: return { color: '#92400E', bg: '#FEF3C7' }; // Amber
    case MeetingStatus.Failed: return { color: '#991B1B', bg: '#FEE2E2' }; // Red
    default: return { color: '#374151', bg: '#F3F4F6' }; // Gray
  }
};

const StatusBadge = ({ status }: { status: MeetingStatus }) => {
  const { color, bg } = getStatusStyle(status);
  return (
    <div style={{
        padding: '0.25rem 0.75rem',
        borderRadius: '9999px',
        fontSize: '0.8rem',
        fontWeight: 600,
        backgroundColor: bg,
        color: color,
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.3rem'
    }}>
        <span style={{width: 8, height: 8, borderRadius: '50%', backgroundColor: color}}></span>
        {status}
    </div>
  );
};

const MeetingCard: React.FC<MeetingCardProps> = ({ meeting, isListView, onClick, onDelete }) => {
  const cardStyles = isListView ? listViewStyle : gridViewStyle;
  const [isHovered, setIsHovered] = useState(false);
  const canDelete = onDelete && meeting.status !== MeetingStatus.Processing;

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent triggering card onClick
    if (canDelete && onDelete) {
      onDelete(meeting);
    }
  };

  return (
    <motion.div
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{ ...baseCardStyle, ...cardStyles, position: 'relative' }}
      whileHover={{ y: -5, boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05)' }}
    >
        {/* Delete Button - positioned top-left (RTL) */}
        {canDelete && isHovered && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            onClick={handleDeleteClick}
            style={deleteButtonStyle}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            aria-label="Delete meeting"
          >
            <TrashIcon width={16} height={16} />
          </motion.button>
        )}
        <div style={{ display: 'flex', flexDirection: isListView ? 'row' : 'column', alignItems: isListView ? 'center' : 'stretch' }}>
            {/* Main Info */}
            <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                    <h4 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600, color: '#1A202C' }}>{meeting.title}</h4>
                    {!isListView && <StatusBadge status={meeting.status} />}
                </div>
                <div style={{ display: 'flex', gap: '1rem', color: '#718096', fontSize: '0.85rem' }}>
                    <p style={{margin:0}}>
                        {typeof meeting.date === 'string' 
                            ? new Date(meeting.date).toLocaleDateString('he-IL', { year: 'numeric', month: 'long', day: 'numeric' })
                            : meeting.date.toLocaleDateString('he-IL', { year: 'numeric', month: 'long', day: 'numeric' })
                        }
                    </p>
                    {meeting.duration && <p style={{margin:0}}>{meeting.duration} דקות</p>}
                </div>
            </div>

            {isListView && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '2rem', flexBasis: '40%' }}>
                    {/* Speaker Avatars */}
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                        {meeting.speakers?.slice(0, 3).map((speaker, index) => (
                        <img
                            key={speaker.id}
                            src={speaker.avatarUrl}
                            alt={speaker.name}
                            style={{
                                width: 32,
                                height: 32,
                                borderRadius: '50%',
                                border: '2px solid white',
                                marginRight: index > 0 ? '-10px' : 0,
                                zIndex: 3 - index,
                            }}
                        />
                        ))}
                        {meeting.speakerCount > 3 && <div style={avatarMoreStyle}>+{meeting.speakerCount - 3}</div>}
                    </div>
                    {/* Status */}
                    <div style={{flexBasis: '120px'}}><StatusBadge status={meeting.status} /></div>
                </div>
            )}

            {!isListView && (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1.5rem' }}>
                    {/* Speaker Avatars */}
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                        {meeting.speakers?.slice(0, 3).map((speaker, index) => (
                        <img
                            key={speaker.id}
                            src={speaker.avatarUrl}
                            alt={speaker.name}
                            style={{
                                width: 40,
                                height: 40,
                                borderRadius: '50%',
                                border: '3px solid white',
                                marginRight: index > 0 ? '-15px' : 0,
                                zIndex: 3 - index,
                            }}
                        />
                        ))}
                        {meeting.speakerCount > 3 && <div style={avatarMoreStyle}>+{meeting.speakerCount - 3}</div>}
                    </div>
                </div>
            )}
        </div>
    </motion.div>
  );
};

// Styles
const baseCardStyle: React.CSSProperties = {
  backgroundColor: 'white',
  borderRadius: '12px',
  boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06)',
  border: '1px solid #E2E8F0',
  cursor: 'pointer',
  transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
};

const gridViewStyle: React.CSSProperties = {
  padding: '1.5rem',
};

const listViewStyle: React.CSSProperties = {
  padding: '1rem 1.5rem',
};

const avatarMoreStyle: React.CSSProperties = {
    width: 32,
    height: 32,
    borderRadius: '50%',
    backgroundColor: '#E2E8F0',
    color: '#4A5568',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '0.75rem',
    fontWeight: 600,
    border: '2px solid white',
    marginRight: '-10px',
    zIndex: 0
}

const deleteButtonStyle: React.CSSProperties = {
    position: 'absolute',
    top: '0.75rem',
    left: '0.75rem', // RTL: left is top-left corner
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    backgroundColor: '#EF4444',
    color: 'white',
    border: 'none',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
    zIndex: 10,
    transition: 'background-color 0.2s',
};

export default MeetingCard;
