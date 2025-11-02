import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { TrashIcon } from './IconComponents';
import { Meeting } from '../types';

interface DeleteConfirmModalProps {
  isOpen: boolean;
  meeting: Meeting | null;
  onClose: () => void;
  onConfirm: () => void;
  isDeleting?: boolean;
}

const DeleteConfirmModal: React.FC<DeleteConfirmModalProps> = ({ 
  isOpen, 
  meeting, 
  onClose, 
  onConfirm,
  isDeleting = false
}) => {
  if (!meeting) return null;

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
            style={modalStyle}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
              <div style={iconContainerStyle}>
                <TrashIcon width={32} height={32} style={{ color: '#EF4444' }} />
              </div>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 600, marginTop: '1rem', marginBottom: '0.5rem' }}>
                מחק פגישה?
              </h2>
              <p style={{ color: '#4A5568', fontSize: '0.95rem' }}>
                האם אתה בטוח שברצונך למחוק את הפגישה
              </p>
              <p style={{ color: '#1A202C', fontSize: '1rem', fontWeight: 600, marginTop: '0.5rem' }}>
                "{meeting.title}"?
              </p>
              <p style={{ color: '#EF4444', fontSize: '0.85rem', marginTop: '1rem' }}>
                פעולה זו אינה ניתנת לביטול. כל הנתונים, התמלול והסיכום יימחקו לצמיתות.
              </p>
            </div>

            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
              <button
                onClick={onClose}
                disabled={isDeleting}
                style={cancelButtonStyle}
              >
                ביטול
              </button>
              <button
                onClick={onConfirm}
                disabled={isDeleting}
                style={confirmButtonStyle}
              >
                {isDeleting ? 'מוחק...' : 'מחק'}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

// Styles
const backdropStyle: React.CSSProperties = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: 'rgba(17, 24, 39, 0.6)',
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  zIndex: 50,
};

const modalStyle: React.CSSProperties = {
  backgroundColor: 'white',
  padding: '2rem',
  borderRadius: '12px',
  width: '90%',
  maxWidth: '450px',
  boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04)',
};

const iconContainerStyle: React.CSSProperties = {
  width: '64px',
  height: '64px',
  borderRadius: '50%',
  backgroundColor: '#FEE2E2',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  margin: '0 auto',
};

const cancelButtonStyle: React.CSSProperties = {
  padding: '0.75rem 1.5rem',
  border: '1px solid #E2E8F0',
  borderRadius: '8px',
  backgroundColor: 'white',
  color: '#4A5568',
  fontSize: '1rem',
  fontWeight: 600,
  cursor: 'pointer',
  transition: 'background-color 0.2s, border-color 0.2s',
};

const confirmButtonStyle: React.CSSProperties = {
  padding: '0.75rem 1.5rem',
  border: 'none',
  borderRadius: '8px',
  backgroundColor: '#EF4444',
  color: 'white',
  fontSize: '1rem',
  fontWeight: 600,
  cursor: 'pointer',
  transition: 'background-color 0.2s',
};

export default DeleteConfirmModal;

