import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';

interface LoginModalProps {
  isOpen: boolean;
  onClose?: () => void;
}

const LoginModal: React.FC<LoginModalProps> = ({ isOpen, onClose }) => {
  const [isSignup, setIsSignup] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [organizationName, setOrganizationName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  
  const { login, register } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isSignup) {
        await register(email, password, name, organizationName);
      } else {
        await login(email, password);
      }
      // Success - token is stored, component will re-render
      onClose?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'שגיאה בהתחברות');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
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
          <h2 style={{ textAlign: 'center', fontWeight: 600, fontSize: '1.5rem', marginBottom: '1.5rem' }}>
            {isSignup ? 'הרשמה' : 'התחברות'}
          </h2>

          {/* Tabs */}
          <div style={{ display: 'flex', border: '1px solid #E2E8F0', borderRadius: '8px', padding: '0.25rem', marginBottom: '2rem' }}>
            <button
              onClick={() => {
                setIsSignup(false);
                setError(null);
              }}
              style={{
                flex: 1,
                border: 'none',
                background: isSignup ? 'none' : '#fff',
                padding: '0.75rem',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '0.9rem',
                color: isSignup ? '#4A5568' : '#14B8A6',
                boxShadow: isSignup ? 'none' : '0 1px 3px 0 rgba(0,0,0,0.1), 0 1px 2px 0 rgba(0,0,0,0.06)',
              }}
            >
              התחברות
            </button>
            <button
              onClick={() => {
                setIsSignup(true);
                setError(null);
              }}
              style={{
                flex: 1,
                border: 'none',
                background: isSignup ? '#fff' : 'none',
                padding: '0.75rem',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '0.9rem',
                color: isSignup ? '#14B8A6' : '#4A5568',
                boxShadow: isSignup ? '0 1px 3px 0 rgba(0,0,0,0.1), 0 1px 2px 0 rgba(0,0,0,0.06)' : 'none',
              }}
            >
              הרשמה
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            {isSignup && (
              <>
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: '#374151' }}>
                    שם מלא
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required={isSignup}
                    style={inputStyle}
                    placeholder="הכנס שם מלא"
                  />
                </div>
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: '#374151' }}>
                    שם הארגון
                  </label>
                  <input
                    type="text"
                    value={organizationName}
                    onChange={(e) => setOrganizationName(e.target.value)}
                    required={isSignup}
                    style={inputStyle}
                    placeholder="הכנס שם הארגון"
                  />
                </div>
              </>
            )}

            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: '#374151' }}>
                אימייל
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                style={inputStyle}
                placeholder="הכנס אימייל"
              />
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: '#374151' }}>
                סיסמה
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                style={inputStyle}
                placeholder="הכנס סיסמה"
                minLength={6}
              />
            </div>

            {error && (
              <div style={{ marginBottom: '1rem', padding: '0.75rem', backgroundColor: '#FEE2E2', borderRadius: '6px', color: '#DC2626', fontSize: '0.875rem' }}>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              style={{
                ...buttonStyle,
                opacity: loading ? 0.6 : 1,
                cursor: loading ? 'not-allowed' : 'pointer',
              }}
            >
              {loading ? 'מעבד...' : isSignup ? 'הרשמה' : 'התחברות'}
            </button>
          </form>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

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
  zIndex: 9999,
};

const modalStyle: React.CSSProperties = {
  backgroundColor: 'white',
  padding: '2rem',
  borderRadius: '12px',
  width: '90%',
  maxWidth: '450px',
  boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04)',
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '0.75rem',
  border: '1px solid #D1D5DB',
  borderRadius: '6px',
  fontSize: '1rem',
  outline: 'none',
  transition: 'border-color 0.2s',
};

const buttonStyle: React.CSSProperties = {
  width: '100%',
  padding: '0.75rem',
  border: 'none',
  borderRadius: '8px',
  backgroundColor: '#14B8A6',
  color: 'white',
  fontSize: '1rem',
  fontWeight: 600,
  cursor: 'pointer',
};

export default LoginModal;

