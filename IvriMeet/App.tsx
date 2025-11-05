import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './components/Dashboard';
import MeetingDetailPage from './components/MeetingDetailPage';
import SpeakersPage from './components/SpeakersPage';
import SettingsPage from './components/SettingsPage';
import LiveMeetingPage from './components/LiveMeetingPage';
import AnalyticsPage from './components/AnalyticsPage';
import UploadModal from './components/UploadModal';
import LoginModal from './components/LoginModal';
import { Meeting, Speaker, MeetingStatus, apiMeetingToUIMeeting } from './types';
import apiClient from './services/api';
import { useAuth } from './contexts/AuthContext';

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
  const { isAuthenticated, isLoading: authLoading, user, token } = useAuth();
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(null);
  const [isUploadModalOpen, setUploadModalOpen] = useState(false);
  const [isLoginModalOpen, setLoginModalOpen] = useState(false);
  const [analyticsTab, setAnalyticsTab] = useState<'retail' | 'email'>('retail');
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [speakers, setSpeakers] = useState<Speaker[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isMobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  // Update API client token when auth changes
  useEffect(() => {
    if (token) {
      apiClient.setToken(token);
    } else {
      apiClient.setToken(null);
    }
  }, [token]);

  // Detect mobile on mount and resize
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Show login modal if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      setLoginModalOpen(true);
    } else if (isAuthenticated) {
      // Close modal when user becomes authenticated
      setLoginModalOpen(false);
    }
  }, [authLoading, isAuthenticated]);

  // Load meetings from backend (only when authenticated)
  useEffect(() => {
    if (!isAuthenticated || authLoading) return;

    // Initial load with retry logic
    const initialLoad = async () => {
      let retries = 0;
      const maxRetries = 5;
      const retryDelay = 3000; // 3 seconds between retries
      
      while (retries < maxRetries) {
        try {
          await loadMeetings();
          break; // Success, exit retry loop
        } catch (err) {
          retries++;
          if (retries >= maxRetries) {
            console.error('Failed to load meetings after all retries:', err);
            // If auth error, show login modal
            if (err instanceof Error && (err.message.includes('401') || err.message.includes('Not authenticated') || err.message.includes('422'))) {
              setLoginModalOpen(true);
            }
            break;
          }
          console.debug(`Initial load attempt ${retries} failed, retrying in ${retryDelay}ms...`);
          await new Promise(resolve => setTimeout(resolve, retryDelay));
        }
      }
    };
    
    initialLoad();
    
    // Listen for custom event to open upload modal from empty state
    const handleOpenModal = () => {
      setUploadModalOpen(true);
    };
    window.addEventListener('openUploadModal', handleOpenModal);
    
    // Keepalive ping to prevent backend deep sleep (every 4 minutes, before 5 min timeout)
    // This ensures backend stays awake even if scaling.min isn't respected
    const keepaliveInterval = setInterval(async () => {
      try {
        await apiClient.healthCheck(1, 1000); // Single retry, 1 second delay for keepalive
      } catch (e) {
        // Silently ignore errors - just keeping the instance alive
        console.debug('Keepalive ping failed (backend may be sleeping):', e);
      }
    }, 4 * 60 * 1000); // Every 4 minutes (before 5 min deep sleep threshold)
    
    return () => {
      window.removeEventListener('openUploadModal', handleOpenModal);
      clearInterval(keepaliveInterval);
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
    if (isMobile) {
      setMobileSidebarOpen(false); // Close sidebar on mobile after navigation
    }
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
      case 'analytics':
        return <AnalyticsPage onBack={() => navigateTo('dashboard')} initialTab={analyticsTab} />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <Dashboard meetings={meetings} onMeetingClick={viewMeetingDetails} loading={loading} error={error} />;
    }
  };

  return (
    <div dir="rtl" style={{ display: 'flex', height: '100vh', backgroundColor: '#F9FAFB', position: 'relative', overflow: 'hidden' }}>
      {/* Sidebar - Hidden on mobile, drawer on mobile when open */}
      <Sidebar 
        currentPage={currentPage} 
        onNavigate={navigateTo} 
        isMobile={isMobile}
        isOpen={isMobileSidebarOpen}
        onClose={() => setMobileSidebarOpen(false)}
      />
      
      {/* Mobile Sidebar Overlay */}
      {isMobile && isMobileSidebarOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => setMobileSidebarOpen(false)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            zIndex: 999,
          }}
        />
      )}
      
      <main style={{ 
        flex: 1, 
        display: 'flex', 
        flexDirection: 'column', 
        overflow: 'hidden',
        marginRight: isMobile ? '0' : '280px', // No margin on mobile
        width: isMobile ? '100%' : 'calc(100% - 280px)',
        boxSizing: 'border-box',
        position: 'relative'
      }}>
        <Header 
          onNewMeetingClick={() => setUploadModalOpen(true)}
          onGmailClick={async () => {
            try {
              // Check if Gmail is already connected
              const status = await apiClient.getGmailStatus();
              
              if (status.connected) {
                // Gmail is connected, navigate to email analysis
                setAnalyticsTab('email');
                navigateTo('analytics');
              } else {
                // Gmail not connected, initiate OAuth flow
                const oauthData = await apiClient.initiateGmailOAuth();
                
                // Open OAuth popup window
                const width = 500;
                const height = 600;
                const left = (window.screen.width - width) / 2;
                const top = (window.screen.height - height) / 2;
                
                const popup = window.open(
                  oauthData.authorization_url,
                  'Gmail OAuth',
                  `width=${width},height=${height},left=${left},top=${top},toolbar=no,location=no,status=no,menubar=no,scrollbars=yes`
                );
                
                // Listen for OAuth callback message
                const messageHandler = (event: MessageEvent) => {
                  if (event.data.type === 'gmail_connected') {
                    window.removeEventListener('message', messageHandler);
                    popup?.close();
                    
                    // Navigate to email analysis
                    setAnalyticsTab('email');
                    navigateTo('analytics');
                  }
                };
                
                window.addEventListener('message', messageHandler);
                
                // Check if popup was closed manually
                const checkClosed = setInterval(() => {
                  if (popup?.closed) {
                    clearInterval(checkClosed);
                    window.removeEventListener('message', messageHandler);
                  }
                }, 1000);
              }
            } catch (error) {
              console.error('Gmail OAuth failed:', error);
              alert(`Failed to connect Gmail: ${error instanceof Error ? error.message : 'Unknown error'}`);
            }
          }}
          onMenuClick={() => setMobileSidebarOpen(!isMobileSidebarOpen)}
          isMobile={isMobile}
        />
        <div style={{ 
          padding: isMobile ? '1rem' : '1rem 2.5rem 2.5rem 2.5rem', 
          flex: 1,
          marginTop: isMobile ? '70px' : '80px', // Smaller header on mobile
          boxSizing: 'border-box',
          maxWidth: '100%',
          overflowY: 'auto',
          overflowX: 'hidden',
          minHeight: 0, // Important for flex scrolling
          WebkitOverflowScrolling: 'touch' // Smooth scrolling on iOS
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
      <LoginModal isOpen={isLoginModalOpen} onClose={() => setLoginModalOpen(false)} />
    </div>
  );
};

export default App;
