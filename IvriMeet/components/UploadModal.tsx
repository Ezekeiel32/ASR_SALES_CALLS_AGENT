import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { UploadCloudIcon, MicIcon } from './IconComponents';
import apiClient from '../services/api';
import { useMobile } from '../hooks/useMobile';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const UploadModal: React.FC<UploadModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [activeTab, setActiveTab] = useState('upload');
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const isMobile = useMobile();
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleDragEnter = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };
  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };
  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };
  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileUpload = async (file: File, retryCount = 0) => {
    // Validate file type
    const allowedTypes = ['audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/aac', 'audio/webm'];
    if (!allowedTypes.includes(file.type)) {
      setUploadError('פורמט קובץ לא נתמך. אנא העלה קובץ MP3, WAV, M4A, AAC או WebM.');
      return;
    }

    try {
      setUploading(true);
      setUploadProgress(0);
      setUploadError(null);
      setUploadSuccess(false);

      // Check backend health before upload (only on first attempt)
      // Use retries to handle cold starts
      if (retryCount === 0) {
        try {
          await apiClient.healthCheck(3, 2000); // 3 retries, 2 second delay
        } catch (healthErr) {
          console.warn('Health check failed, but continuing with upload:', healthErr);
          // Continue anyway - sometimes health check fails but upload works
          // The upload itself will retry if it fails
        }
      }

      // Upload with real-time progress tracking
      const response = await apiClient.uploadMeeting(
        file,
        undefined, // title
        undefined, // organizationId
        (progress) => {
          // Update progress from real upload events
          setUploadProgress(progress);
        }
      );
      
      setUploadProgress(100);
      
      setUploadSuccess(true);
      setTimeout(() => {
        onSuccess?.();
        onClose();
        setUploadSuccess(false);
        setUploadProgress(0);
      }, 1500);
    } catch (err) {
      console.error('Upload error:', err);
      const errorMessage = err instanceof Error ? err.message : 'שגיאה בהעלאת הקובץ';
      
      // Retry logic for network errors
      const isNetworkError = errorMessage.includes('Network error') || 
                            errorMessage.includes('Failed to fetch') ||
                            errorMessage.includes('ERR_TIMED_OUT') ||
                            errorMessage.includes('timeout') ||
                            errorMessage.includes('CORS');
      
      if (isNetworkError && retryCount < 2) {
        // Wait 2 seconds before retry
        await new Promise(resolve => setTimeout(resolve, 2000));
        setUploadProgress(0);
        return handleFileUpload(file, retryCount + 1);
      }
      
      setUploadError(errorMessage);
      setUploadProgress(0);
    } finally {
      setUploading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          style={backdropStyle}
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            style={getModalStyle(isMobile)}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 style={{ textAlign: 'center', fontWeight: 600, fontSize: '1.5rem' }}>פגישה חדשה</h2>
            <p style={{ textAlign: 'center', color: '#4A5568', marginTop: '-0.5rem', marginBottom: '2rem' }}>העלה הקלטה קיימת או התחל הקלטה חיה.</p>
            
            {/* Tabs */}
            <div style={{ display: 'flex', border: '1px solid #E2E8F0', borderRadius: '8px', padding: '0.25rem', marginBottom: '2rem' }}>
              <button onClick={() => setActiveTab('upload')} style={{ ...tabStyle, ...(activeTab === 'upload' ? activeTabStyle : {}) }}>
                <UploadCloudIcon width={20} height={20} style={{ marginLeft: '0.5rem' }}/> העלאת קובץ
              </button>
              <button onClick={() => setActiveTab('live')} style={{ ...tabStyle, ...(activeTab === 'live' ? activeTabStyle : {}) }}>
                <MicIcon width={20} height={20} style={{ marginLeft: '0.5rem' }}/> הקלטה חיה
              </button>
            </div>
            
            {/* Tab Content */}
            {activeTab === 'upload' && (
              <div 
                onDragEnter={handleDragEnter}
                onDragLeave={handleDragLeave}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                className={isDragging || uploading ? 'upload-dropzone-animated' : ''}
                style={{ 
                  ...dropzoneStyle, 
                  ...(isDragging ? dropzoneDraggingStyle : {}),
                  ...(uploading ? uploadingDropzoneStyle : {}),
                  position: 'relative',
                  overflow: 'visible'
                }}
              >
                <UploadCloudIcon width="48" height="48" style={{ color: '#14B8A6', marginBottom: '1rem' }} />
                <p style={{ fontWeight: 600, color: '#1A202C' }}>גרור ושחרר קבצים לכאן</p>
                <p style={{ color: '#718096', fontSize: '0.9rem' }}>
                  או <span 
                    style={{ color: '#14B8A6', fontWeight: 600, cursor: 'pointer' }}
                    onClick={() => fileInputRef.current?.click()}
                  >לחץ כדי לבחור קובץ</span>
                </p>
                <input 
                  type="file" 
                  ref={fileInputRef}
                  hidden 
                  accept="audio/*,.mp3,.wav,.m4a,.aac,.webm"
                  onChange={handleFileSelect}
                  disabled={uploading}
                />
                
                {/* Progress Bar */}
                {uploading && (
                  <div style={{ marginTop: '1.5rem', width: '100%' }}>
                    <div style={progressBarContainerStyle}>
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${uploadProgress}%` }}
                        transition={{ duration: 0.3, ease: 'easeOut' }}
                        style={progressBarStyle}
                      />
                    </div>
                    <p style={{ color: '#14B8A6', marginTop: '0.5rem', fontSize: '0.85rem', fontWeight: 500 }}>
                      מעלה ומעבד... {Math.round(uploadProgress)}%
                    </p>
                  </div>
                )}
                
                {!uploading && (
                  <p style={{ color: '#A0AEC0', fontSize: '0.8rem', marginTop: '2rem' }}>פורמטים נתמכים: MP3, WAV, M4A, AAC, WebM</p>
                )}
                
                {uploadError && !uploading && <p style={{ color: '#EF4444', marginTop: '1rem' }}>{uploadError}</p>}
                {uploadSuccess && !uploading && <p style={{ color: '#10B981', marginTop: '1rem' }}>✓ הפגישה הועלתה בהצלחה!</p>}
              </div>
            )}
            {activeTab === 'live' && (
              <div style={{ textAlign: 'center', padding: '2rem' }}>
                <MicIcon width={48} height={48} style={{ color: '#14B8A6', marginBottom: '1rem' }} />
                <p style={{ fontWeight: 600, color: '#1A202C' }}>מוכן להתחיל פגישה חיה?</p>
                <p style={{ color: '#718096', fontSize: '0.9rem', marginBottom: '2rem' }}>המערכת תתמלל את הפגישה בזמן אמת.</p>
                <button style={primaryButtonStyle}>התחל הקלטה</button>
              </div>
            )}

          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

// Styles
const backdropStyle: React.CSSProperties = {
  position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
  backgroundColor: 'rgba(17, 24, 39, 0.6)',
  display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 50
};
const getModalStyle = (isMobile: boolean): React.CSSProperties => ({
  backgroundColor: 'white', 
  padding: isMobile ? '1.5rem' : '2rem', 
  borderRadius: '12px',
  width: '90%', 
  maxWidth: '550px',
  maxHeight: '90vh',
  overflowY: 'auto',
  boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04)',
  WebkitOverflowScrolling: 'touch',
});
const tabStyle: React.CSSProperties = {
    flex: 1, border: 'none', background: 'none', padding: '0.75rem',
    borderRadius: '6px', cursor: 'pointer', fontWeight: 600, fontSize: '0.9rem',
    color: '#4A5568', display: 'flex', alignItems: 'center', justifyContent: 'center',
    transition: 'background-color 0.2s, color 0.2s'
};
const activeTabStyle: React.CSSProperties = {
    backgroundColor: '#fff', color: '#14B8A6',
    boxShadow: '0 1px 3px 0 rgba(0,0,0,0.1), 0 1px 2px 0 rgba(0,0,0,0.06)'
};
const dropzoneStyle: React.CSSProperties = {
    borderWidth: '2px',
    borderStyle: 'dashed',
    borderColor: '#CBD5E0',
    borderRadius: '8px',
    padding: '2rem',
    textAlign: 'center',
    cursor: 'pointer',
    transition: 'border-color 0.2s, background-color 0.2s',
    position: 'relative',
};

const dropzoneDraggingStyle: React.CSSProperties = {
    borderColor: '#14B8A6',
    backgroundColor: '#F0FDFA',
    animation: 'borderPulse 2s ease-in-out infinite',
};

const uploadingDropzoneStyle: React.CSSProperties = {
    borderColor: '#14B8A6',
    backgroundColor: '#F0FDFA',
    animation: 'borderPulse 2s ease-in-out infinite',
};

const progressBarContainerStyle: React.CSSProperties = {
    width: '100%',
    height: '6px',
    backgroundColor: '#E5E7EB',
    borderRadius: '9999px',
    overflow: 'hidden',
    position: 'relative',
};

const progressBarStyle: React.CSSProperties = {
    height: '100%',
    backgroundColor: '#14B8A6',
    borderRadius: '9999px',
    backgroundImage: 'linear-gradient(90deg, #14B8A6, #0D9488, #14B8A6)',
    backgroundSize: '200% 100%',
    animation: 'shimmer 2s ease-in-out infinite',
    boxShadow: '0 2px 8px rgba(20, 184, 166, 0.4)',
};
const primaryButtonStyle: React.CSSProperties = {
    width: '100%', padding: '0.75rem', border: 'none', borderRadius: '8px',
    backgroundColor: '#14B8A6', color: 'white', fontSize: '1rem',
    fontWeight: 600, cursor: 'pointer',
};

export default UploadModal;
