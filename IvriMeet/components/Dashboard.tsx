import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Meeting } from '../types';
import StatsWidget from './StatsWidget';
import MeetingCard from './MeetingCard';
import DeleteConfirmModal from './DeleteConfirmModal';
import { PlusIcon, ViewGridIcon, ViewListIcon, UsersIcon, MicIcon, HomeIcon } from './IconComponents';
import apiClient from '../services/api';

interface DashboardProps {
  meetings: Meeting[];
  onMeetingClick: (meeting: Meeting) => void;
  loading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: { y: 0, opacity: 1 },
};

const EmptyState = () => (
    <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        style={{ textAlign: 'center', padding: '4rem 2rem', backgroundColor: '#fff', borderRadius: '12px', border: '1px solid #E2E8F0' }}
    >
        <HomeIcon width={60} height={60} style={{ color: '#14B8A6', marginBottom: '1.5rem' }} />
        <h2 style={{ fontSize: '1.75rem', fontWeight: 600, marginBottom: '0.5rem' }}>ברוכים הבאים ל-IvriMeet</h2>
        <p style={{ fontSize: '1.1rem', color: '#4A5568', marginBottom: '2rem' }}>נראה שעדיין לא העלית פגישות. <br/> לחץ על הכפתור כדי להתחיל.</p>
        <button 
            onClick={(e) => {
                e.preventDefault();
                // This will be handled by the parent component
                window.dispatchEvent(new CustomEvent('openUploadModal'));
            }}
            style={{ 
                display: 'inline-flex', 
                alignItems: 'center', 
                padding: '0.75rem 1.5rem', 
                border: 'none', 
                borderRadius: '8px', 
                backgroundColor: '#14B8A6', 
                color: 'white', 
                cursor: 'pointer', 
                fontSize: '1rem', 
                fontWeight: 600,
                transition: 'background-color 0.2s, transform 0.1s'
            }}
            onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#0D9488';
            }}
            onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#14B8A6';
            }}
        >
            <PlusIcon style={{ marginLeft: '0.5rem' }} width={20} height={20}/>
            <span>העלה את הפגישה הראשונה שלך</span>
        </button>
    </motion.div>
);

const Dashboard: React.FC<DashboardProps> = ({ meetings, onMeetingClick, loading = false, error = null, onRefresh }) => {
  const [isListView, setListView] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedMeetingForDelete, setSelectedMeetingForDelete] = useState<Meeting | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [deleteSuccess, setDeleteSuccess] = useState(false);
  
  // Example stats
  const totalMeetings = meetings.length;
  const totalDuration = meetings.reduce((acc, m) => acc + (m.duration || 0), 0);
  const uniqueSpeakers = new Set(meetings.flatMap(m => m.speakers?.map(s => s.id) || [])).size;

  const handleDeleteClick = (meeting: Meeting) => {
    setSelectedMeetingForDelete(meeting);
    setDeleteModalOpen(true);
    setDeleteError(null);
    setDeleteSuccess(false);
  };

  const handleDeleteConfirm = async () => {
    if (!selectedMeetingForDelete) return;

    try {
      setIsDeleting(true);
      setDeleteError(null);
      
      await apiClient.deleteMeeting(selectedMeetingForDelete.id);
      
      setDeleteSuccess(true);
      setDeleteModalOpen(false);
      
      // Auto-hide success notification after 3 seconds
      setTimeout(() => {
        setDeleteSuccess(false);
      }, 3000);
      
      // Refresh meetings list
      if (onRefresh) {
        setTimeout(() => {
          onRefresh();
        }, 500);
      }
    } catch (err) {
      console.error('Delete error:', err);
      const errorMessage = err instanceof Error ? err.message : 'שגיאה במחיקת הפגישה';
      setDeleteError(errorMessage);
      // Auto-hide error notification after 5 seconds
      setTimeout(() => {
        setDeleteError(null);
      }, 5000);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteModalOpen(false);
    setSelectedMeetingForDelete(null);
    setDeleteError(null);
  };

  if (loading) {
    return (
      <div style={{ paddingTop: '0', textAlign: 'center', padding: '4rem' }}>
        <p style={{ fontSize: '1.1rem', color: '#4A5568' }}>טוען פגישות...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ paddingTop: '0', textAlign: 'center', padding: '4rem' }}>
        <p style={{ fontSize: '1.1rem', color: '#EF4444' }}>שגיאה: {error}</p>
      </div>
    );
  }


  return (
    <div style={{ paddingTop: '0', width: '100%', boxSizing: 'border-box' }}>
      <h1 style={{ fontSize: '2.25rem', fontWeight: 700, marginBottom: '2rem' }}>דשבורד</h1>
      
      {/* Stats Grid */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem', marginBottom: '3rem' }}
      >
        <StatsWidget icon={<HomeIcon width={24} height={24}/>} title="סך הכל פגישות" value={totalMeetings.toString()} />
        <StatsWidget icon={<MicIcon width={24} height={24}/>} title="זמן כולל (דקות)" value={totalDuration.toString()} />
        <StatsWidget icon={<UsersIcon width={24} height={24}/>} title="דוברים שזוהו" value={uniqueSpeakers.toString()} />
      </motion.div>
      
      {/* Meetings Section */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 600, margin: 0 }}>פגישות אחרונות</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {/* View Toggle */}
            <div style={{ display: 'flex', backgroundColor: '#E2E8F0', padding: '0.25rem', borderRadius: '8px' }}>
                <motion.button 
                    onClick={() => setListView(false)} 
                    style={{...toggleButtonStyle, backgroundColor: !isListView ? '#fff' : 'transparent', color: !isListView ? '#14B8A6' : '#4A5568' }}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                >
                    <ViewGridIcon width={20} height={20}/>
                </motion.button>
                <motion.button 
                    onClick={() => setListView(true)} 
                    style={{...toggleButtonStyle, backgroundColor: isListView ? '#fff' : 'transparent', color: isListView ? '#14B8A6' : '#4A5568'}}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                >
                    <ViewListIcon width={20} height={20}/>
                </motion.button>
            </div>
          </div>
        </div>

        <AnimatePresence>
            {meetings.length > 0 ? (
                <motion.div
                    key="meeting-list"
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                    style={{
                    display: 'grid',
                    gridTemplateColumns: isListView ? '1fr' : 'repeat(auto-fill, minmax(280px, 1fr))',
                    gap: '1.5rem',
                    width: '100%',
                    boxSizing: 'border-box'
                    }}
                >
                    {meetings.map(meeting => (
                    <motion.div key={meeting.id} variants={itemVariants}>
                        <MeetingCard 
                          meeting={meeting} 
                          isListView={isListView} 
                          onClick={() => onMeetingClick(meeting)}
                          onDelete={handleDeleteClick}
                        />
                    </motion.div>
                    ))}
                </motion.div>
            ) : (
                <EmptyState key="empty-state" />
            )}
        </AnimatePresence>
      </div>

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={deleteModalOpen}
        meeting={selectedMeetingForDelete}
        onClose={handleDeleteCancel}
        onConfirm={handleDeleteConfirm}
        isDeleting={isDeleting}
      />

      {/* Success/Error Messages */}
      {deleteSuccess && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          style={notificationStyle}
        >
          <p style={{ color: '#10B981', margin: 0 }}>✓ הפגישה נמחקה בהצלחה</p>
        </motion.div>
      )}
      {deleteError && !deleteModalOpen && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          style={notificationStyle}
        >
          <p style={{ color: '#EF4444', margin: 0 }}>✗ {deleteError}</p>
        </motion.div>
      )}
    </div>
  );
};

const toggleButtonStyle: React.CSSProperties = {
    border: 'none',
    padding: '0.5rem',
    borderRadius: '6px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'background-color 0.2s, color 0.2s'
}

const notificationStyle: React.CSSProperties = {
  position: 'fixed',
  top: '100px',
  left: '50%',
  transform: 'translateX(-50%)',
  backgroundColor: 'white',
  padding: '1rem 1.5rem',
  borderRadius: '8px',
  boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05)',
  zIndex: 100,
  fontSize: '0.95rem',
  fontWeight: 500,
}

export default Dashboard;
