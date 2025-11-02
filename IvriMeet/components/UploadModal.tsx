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

  const handleFileUpload = async (file: File) => {
    // Validate file type
    const allowedTypes = ['audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/aac', 'audio/webm'];
    if (!allowedTypes.includes(file.type)) {
      setUploadError('פורמט קובץ לא נתמך. אנא העלה קובץ MP3, WAV, M4A, AAC או WebM.');
      return;
    }

    try {
      setUploading(true);
      setUploadError(null);
      setUploadSuccess(false);

      const response = await apiClient.uploadMeeting(file);
      
      setUploadSuccess(true);
      setTimeout(() => {
        onSuccess?.();
        onClose();
        setUploadSuccess(false);
      }, 1500);
    } catch (err) {
      console.error('Upload error:', err);
      setUploadError(err instanceof Error ? err.message : 'שגיאה בהעלאת הקובץ');
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
                style={{ ...dropzoneStyle, ...(isDragging ? dropzoneDraggingStyle : {}) }}
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
                <p style={{ color: '#A0AEC0', fontSize: '0.8rem', marginTop: '2rem' }}>פורמטים נתמכים: MP3, WAV, M4A, AAC, WebM</p>
                {uploading && <p style={{ color: '#14B8A6', marginTop: '1rem' }}>מעלה ומעבד...</p>}
                {uploadError && <p style={{ color: '#EF4444', marginTop: '1rem' }}>{uploadError}</p>}
                {uploadSuccess && <p style={{ color: '#10B981', marginTop: '1rem' }}>✓ הפגישה הועלתה בהצלחה!</p>}
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
};
const dropzoneDraggingStyle: React.CSSProperties = {
    borderColor: '#14B8A6',  // Only change borderColor, keep other border properties from dropzoneStyle
    backgroundColor: '#F0FDFA'
};
const primaryButtonStyle: React.CSSProperties = {
    width: '100%', padding: '0.75rem', border: 'none', borderRadius: '8px',
    backgroundColor: '#14B8A6', color: 'white', fontSize: '1rem',
    fontWeight: 600, cursor: 'pointer',
};

export default UploadModal;
