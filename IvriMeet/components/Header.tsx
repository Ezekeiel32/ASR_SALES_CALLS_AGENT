import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import { SearchIcon, BellIcon, ChevronDownIcon, LogoutIcon, SettingsIcon, PlusIcon } from './IconComponents';

interface HeaderProps {
  onNewMeetingClick: () => void;
  onMenuClick?: () => void;
  isMobile?: boolean;
}

const Header: React.FC<HeaderProps> = ({ onNewMeetingClick, onMenuClick, isMobile = false }) => {
  const { user, logout } = useAuth();
  const [isDropdownOpen, setDropdownOpen] = useState(false);
  
  const handleLogout = () => {
    logout();
    setDropdownOpen(false);
  };

  return (
    <header style={isMobile ? mobileHeaderStyle : headerStyle}>
      {/* Mobile Menu Button */}
      {isMobile && onMenuClick && (
        <motion.button
          onClick={onMenuClick}
          style={menuButtonStyle}
          whileTap={{ scale: 0.95 }}
          aria-label="Open menu"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="3" y1="12" x2="21" y2="12"/>
            <line x1="3" y1="6" x2="21" y2="6"/>
            <line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
        </motion.button>
      )}
      
      {/* Search Bar - Hidden on mobile or made compact */}
      {!isMobile && (
        <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
          <SearchIcon style={{ position: 'absolute', right: '1rem', color: '#A0AEC0' }} width={20} height={20} />
          <input type="text" placeholder="חיפוש פגישות, דוברים ועוד..." style={searchInputStyle} />
        </div>
      )}

      {/* Header Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: isMobile ? '0.5rem' : '1rem' }}>
        <motion.button 
          onClick={onNewMeetingClick} 
          style={isMobile ? mobileNewMeetingButtonStyle : newMeetingButtonStyle}
          whileHover={{ backgroundColor: '#0D9488' }}
          whileTap={{ scale: 0.98 }}
        >
          {isMobile ? (
            <PlusIcon width={24} height={24}/>
          ) : (
            <>
              <PlusIcon style={{ marginLeft: '0.5rem' }} width={20} height={20}/>
              <span>פגישה חדשה</span>
            </>
          )}
        </motion.button>
        
        {!isMobile && (
          <motion.button whileTap={{scale: 0.9}} style={iconButtonStyle}>
              <BellIcon width={24} height={24} />
          </motion.button>
        )}
        
        {/* User Dropdown - Compact on mobile */}
        <div style={{ position: 'relative' }}>
          <div style={isMobile ? mobileUserMenuContainerStyle : userMenuContainerStyle} onClick={() => setDropdownOpen(!isDropdownOpen)}>
            <img src={`https://i.pravatar.cc/150?u=${user?.email || 'user'}`} alt="User Avatar" style={{ width: isMobile ? 36 : 40, height: isMobile ? 36 : 40, borderRadius: '50%' }} />
            {!isMobile && user && (
              <div style={{ marginRight: '0.75rem', textAlign: 'right' }}>
                  <p style={{ margin: 0, fontWeight: 600, fontSize: '0.9rem' }}>{user.name || user.email}</p>
                  <p style={{ margin: 0, fontSize: '0.8rem', color: '#718096' }}>{user.email}</p>
              </div>
            )}
            {!isMobile && (
              <ChevronDownIcon style={{ marginRight: 'auto', color: '#718096', transition: 'transform 0.2s', transform: isDropdownOpen ? 'rotate(180deg)' : 'rotate(0deg)' }} width={20} height={20} />
            )}
          </div>

          <AnimatePresence>
            {isDropdownOpen && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
                style={dropdownStyle}
              >
                <button style={dropdownItemStyle} onClick={() => { setDropdownOpen(false); }}><SettingsIcon width={18} height={18} style={{marginLeft: '0.5rem'}}/> הגדרות</button>
                <button style={dropdownItemStyle} onClick={handleLogout}><LogoutIcon width={18} height={18} style={{marginLeft: '0.5rem'}}/> התנתקות</button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </header>
  );
};

// Styles
const headerStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: '1rem 2.5rem',
  backgroundColor: '#FFFFFF',
  borderBottom: '1px solid #E2E8F0',
  width: 'calc(100% - 280px)', // Account for sidebar width
  position: 'fixed',
  top: 0,
  right: '280px', // Sidebar width
  zIndex: 10,
  boxSizing: 'border-box'
};

const mobileHeaderStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: '0.75rem 1rem',
  backgroundColor: '#FFFFFF',
  borderBottom: '1px solid #E2E8F0',
  width: '100%',
  position: 'fixed',
  top: 0,
  right: 0,
  left: 0,
  zIndex: 100,
  boxSizing: 'border-box',
  height: '70px'
};

const menuButtonStyle: React.CSSProperties = {
  background: 'none',
  border: 'none',
  cursor: 'pointer',
  color: '#1A202C',
  padding: '0.5rem',
  borderRadius: '8px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  minWidth: '44px',
  minHeight: '44px',
  marginLeft: '0.5rem'
};

const searchInputStyle: React.CSSProperties = {
  padding: '0.6rem 2.75rem 0.6rem 1rem',
  border: '1px solid #E2E8F0',
  borderRadius: '8px',
  width: '100%',
  maxWidth: '350px',
  backgroundColor: '#F7FAFC',
  fontSize: '0.9rem',
  transition: 'box-shadow 0.2s, border-color 0.2s',
  boxSizing: 'border-box'
};

const newMeetingButtonStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  padding: '0.6rem 1.25rem',
  border: 'none',
  borderRadius: '8px',
  backgroundColor: '#14B8A6', // Teal
  color: 'white',
  cursor: 'pointer',
  fontSize: '0.9rem',
  fontWeight: 600,
  transition: 'background-color 0.2s, transform 0.1s',
};

const iconButtonStyle: React.CSSProperties = {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    color: '#4A5568',
    padding: '0.5rem',
    borderRadius: '50%',
};

const userMenuContainerStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    cursor: 'pointer',
    padding: '0.25rem',
    borderRadius: '8px',
};

const mobileUserMenuContainerStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    cursor: 'pointer',
    padding: '0.25rem',
    borderRadius: '8px',
    minWidth: '44px',
    minHeight: '44px',
    justifyContent: 'center'
};

const mobileNewMeetingButtonStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '0.6rem',
  border: 'none',
  borderRadius: '8px',
  backgroundColor: '#14B8A6',
  color: 'white',
  cursor: 'pointer',
  fontSize: '0.9rem',
  fontWeight: 600,
  transition: 'background-color 0.2s, transform 0.1s',
  minWidth: '44px',
  minHeight: '44px'
};

const dropdownStyle: React.CSSProperties = {
  position: 'absolute',
  top: '120%',
  left: 0,
  backgroundColor: 'white',
  borderRadius: '8px',
  boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05)',
  border: '1px solid #E2E8F0',
  width: '200px',
  zIndex: 20,
  padding: '0.5rem 0',
};

const dropdownItemStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  width: '100%',
  padding: '0.75rem 1rem',
  border: 'none',
  background: 'none',
  textAlign: 'right',
  fontSize: '0.9rem',
  cursor: 'pointer',
};


export default Header;
