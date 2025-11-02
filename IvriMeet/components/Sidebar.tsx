import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { HomeIcon, UsersIcon, MicIcon, SettingsIcon } from './IconComponents';

interface SidebarProps {
  currentPage: string;
  onNavigate: (page: string) => void;
  isMobile?: boolean;
  isOpen?: boolean;
  onClose?: () => void;
}

const NavItem = ({ icon, label, page, currentPage, onNavigate }: any) => {
  const isActive = currentPage === page;
  const [isHovered, setIsHovered] = useState(false);
  
  return (
    <li style={{ listStyle: 'none' }}>
      <motion.button
        onClick={() => onNavigate(page)}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        style={{
          ...navButtonStyle,
          backgroundColor: isActive ? '#30c2ac' : 'transparent', // Regular green when selected (breaks through overlay), transparent otherwise
          color: isActive ? '#FFFFFF' : 'rgba(255, 255, 255, 0.85)',
          fontWeight: isActive ? 600 : 500,
          border: 'none',
          outline: isHovered ? '2px solid #c3f7e8' : 'none',
          outlineOffset: '2px',
          position: 'relative',
          zIndex: isActive ? 3 : 2, // Selected buttons above overlay
        }}
        whileTap={{ scale: 0.98 }}
      >
        <div style={{ color: 'inherit' }}>{icon}</div>
        <span style={{ marginRight: '1rem', fontWeight: 'inherit' }}>{label}</span>
      </motion.button>
    </li>
  );
};

const Sidebar: React.FC<SidebarProps> = ({ currentPage, onNavigate, isMobile = false, isOpen = false, onClose }) => {
  const { user } = useAuth();
  const sidebarStyles = isMobile 
    ? { ...sidebarStyle, ...mobileSidebarStyle, transform: isOpen ? 'translateX(0)' : 'translateX(100%)' }
    : sidebarStyle;

  return (
    <aside style={sidebarStyles}>
      <div style={overlayStyle}></div>
      <div style={{ ...contentWrapperStyle }}>
      <div style={logoContainerStyle}>
        <h1 style={logoStyle}>IvriMeet</h1>
      </div>
      <nav style={{ flex: 1 }}>
        <ul style={{ padding: 0, margin: 0 }}>
          <NavItem icon={<HomeIcon width={22} height={22}/>} label="דשבורד" page="dashboard" currentPage={currentPage} onNavigate={onNavigate} />
          <NavItem icon={<UsersIcon width={22} height={22}/>} label="דוברים" page="speakers" currentPage={currentPage} onNavigate={onNavigate} />
          <NavItem icon={<MicIcon width={22} height={22}/>} label="פגישה חיה" page="live" currentPage={currentPage} onNavigate={onNavigate} />
        </ul>
      </nav>
      <div style={userProfileStyle}>
          <div style={{ paddingBottom: '1.5rem', borderTop: '1px solid rgba(255, 255, 255, 0.15)' }}>
            <NavItem icon={<SettingsIcon width={22} height={22}/>} label="הגדרות" page="settings" currentPage={currentPage} onNavigate={onNavigate} />
        </div>
        <div style={{ display: 'flex', alignItems: 'center' }}>
              <img src={`https://i.pravatar.cc/150?u=${user?.email || 'user'}`} alt="User Avatar" style={{ width: 40, height: 40, borderRadius: '50%', marginLeft: '1rem', border: '2px solid rgba(255, 255, 255, 0.3)' }} />
            <div>
                  <p style={{ margin: 0, fontWeight: 600, fontSize: '0.9rem', color: '#FFFFFF' }}>{user?.name || user?.email || 'משתמש'}</p>
                  <p style={{ margin: 0, fontSize: '0.8rem', color: 'rgba(255, 255, 255, 0.8)' }}>{user?.email || ''}</p>
              </div>
            </div>
        </div>
      </div>
    </aside>
  );
};

// Styles
const sidebarStyle: React.CSSProperties = {
  width: '280px',
  backgroundColor: '#30c2ac', // Original green background
  color: '#FFFFFF', // White text for contrast
  display: 'flex',
  flexDirection: 'column',
  height: '100vh',
  position: 'fixed',
  right: 0,
  top: 0,
  bottom: 0,
  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
  borderLeft: '1px solid rgba(16, 71, 48, 0.3)', // Subtle darker green border
  zIndex: 100,
  boxSizing: 'border-box',
  transition: 'transform 0.3s ease-in-out',
};

const mobileSidebarStyle: React.CSSProperties = {
  width: '280px',
  maxWidth: '85vw', // Max 85% of viewport width on very small screens
  zIndex: 1000, // Above overlay
};

const overlayStyle: React.CSSProperties = {
  position: 'absolute',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: 'rgba(75, 156, 144, 0.4)', // Teal-green (#4b9c90) transparent overlay (40% opacity)
  zIndex: 1,
  pointerEvents: 'none', // Allow clicks to pass through
};

const contentWrapperStyle: React.CSSProperties = {
  position: 'relative',
  zIndex: 2, // Content above overlay
  display: 'flex',
  flexDirection: 'column',
  height: '100%',
};

const logoContainerStyle: React.CSSProperties = {
  padding: '1.5rem',
  borderBottom: '1px solid rgba(255, 255, 255, 0.15)', // Subtle white border
};

const logoStyle: React.CSSProperties = {
  margin: 0,
  fontSize: '1.75rem',
  fontWeight: 700,
  letterSpacing: '1px',
  textAlign: 'center',
  color: '#FFFFFF', // White text for readability
};

const navButtonStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  width: 'calc(100% - 2rem)',
  margin: '0.5rem 1rem',
  padding: '0.8rem 1rem',
  border: 'none',
  background: 'none',
  textAlign: 'right',
  cursor: 'pointer',
  fontSize: '1rem',
  color: 'rgba(255, 255, 255, 0.9)', // White text with slight transparency
  borderRadius: '8px',
  transition: 'background-color 0.2s ease',
};

const userProfileStyle: React.CSSProperties = {
    padding: '1.5rem',
};

export default Sidebar;
