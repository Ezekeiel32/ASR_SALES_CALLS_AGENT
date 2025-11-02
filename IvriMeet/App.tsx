import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './components/Dashboard';
import MeetingDetailPage from './components/MeetingDetailPage';
import SpeakersPage from './components/SpeakersPage';
import SettingsPage from './components/SettingsPage';
import LiveMeetingPage from './components/LiveMeetingPage';
import UploadModal from './components/UploadModal';
import { Meeting, Speaker, MeetingStatus, apiMeetingToUIMeeting } from './types';
import apiClient from './services/api';

const pageVariants = {
  initial: { opacity: 0, y: 20 },
  in: { opacity: 1, y: 0 },
  out: { opacity: 0, y: -20 },
};

const pageTransition = {
  type: 'tween',
  ease: 'anticipate',
  duration: 0.5,
};

const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(null);
  const [isUploadModalOpen, setUploadModalOpen] = useState(false);
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [speakers, setSpeakers] = useState<Speaker[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load meetings from backend
  useEffect(() => {
    loadMeetings();
    
    // Listen for custom event to open upload modal from empty state
    const handleOpenModal = () => {
      setUploadModalOpen(true);
    };
    window.addEventListener('openUploadModal', handleOpenModal);
    
    return () => {
      window.removeEventListener('openUploadModal', handleOpenModal);
    };
  }, []);

  const loadMeetings = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.listMeetings();
      const uiMeetings = response.meetings.map(apiMeetingToUIMeeting);
      setMeetings(uiMeetings);
    } catch (err) {
      console.error('Failed to load meetings:', err);
      setError(err instanceof Error ? err.message : 'Failed to load meetings');
    } finally {
      setLoading(false);
    }
  };

  const navigateTo = (page: string) => {
    setCurrentPage(page);
    setSelectedMeeting(null);
    if (page === 'speakers') {
      loadSpeakers();
    }
  };

  const loadSpeakers = async () => {
    try {
      // For now, use a default org ID - in production this would come from auth
      const orgId = 'default-org-id';
      const response = await apiClient.listSpeakers(orgId);
      setSpeakers(response.speakers.map(s => ({
        id: s.id,
        label: s.label,
        name: s.name,
        meetings: s.meetings_count,
        lastSeen: s.last_seen ? new Date(s.last_seen) : undefined,
        avatarUrl: s.avatar_url || `https://i.pravatar.cc/150?u=${s.id}`,
      })));
    } catch (err) {
      console.error('Failed to load speakers:', err);
    }
  };

  const viewMeetingDetails = async (meeting: Meeting) => {
    try {
      // Load full meeting details from backend
      const fullMeeting = await apiClient.getMeeting(meeting.id);
      const uiMeeting = apiMeetingToUIMeeting(fullMeeting);
      setSelectedMeeting(uiMeeting);
      setCurrentPage('meeting-details');
    } catch (err) {
      console.error('Failed to load meeting details:', err);
      // Fallback to the meeting we have
    setSelectedMeeting(meeting);
    setCurrentPage('meeting-details');
    }
  };

  const handleUploadSuccess = () => {
    setUploadModalOpen(false);
    loadMeetings(); // Refresh meetings list
  };

  const renderPage = () => {
    if (selectedMeeting && currentPage === 'meeting-details') {
      return <MeetingDetailPage meeting={selectedMeeting} onBack={() => navigateTo('dashboard')} onRefresh={loadMeetings} />;
    }

    switch (currentPage) {
      case 'dashboard':
        return <Dashboard meetings={meetings} onMeetingClick={viewMeetingDetails} loading={loading} error={error} onRefresh={loadMeetings} />;
      case 'speakers':
        return <SpeakersPage speakers={speakers} />;
      case 'live':
        return <LiveMeetingPage />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <Dashboard meetings={meetings} onMeetingClick={viewMeetingDetails} loading={loading} error={error} />;
    }
  };

  return (
    <div dir="rtl" style={{ display: 'flex', height: '100vh', backgroundColor: '#F9FAFB' }}>
      <Sidebar currentPage={currentPage} onNavigate={navigateTo} />
      <main style={{ 
        flex: 1, 
        display: 'flex', 
        flexDirection: 'column', 
        overflow: 'hidden',
        marginRight: '280px', // Account for sidebar width
        width: 'calc(100% - 280px)',
        boxSizing: 'border-box',
        position: 'relative'
      }}>
        <Header onNewMeetingClick={() => setUploadModalOpen(true)} />
        <div style={{ 
          padding: '1rem 2.5rem 2.5rem 2.5rem', 
          flex: 1,
          marginTop: '80px', // Account for fixed header
          boxSizing: 'border-box',
          maxWidth: '100%',
          overflowY: 'auto',
          overflowX: 'hidden',
          minHeight: 0 // Important for flex scrolling
        }}>
          <AnimatePresence mode="wait">
            <motion.div
              key={currentPage + (selectedMeeting?.id || '')}
              initial="initial"
              animate="in"
              exit="out"
              variants={pageVariants}
              transition={pageTransition}
            >
              {renderPage()}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
      <UploadModal isOpen={isUploadModalOpen} onClose={() => setUploadModalOpen(false)} onSuccess={handleUploadSuccess} />
    </div>
  );
};

export default App;
