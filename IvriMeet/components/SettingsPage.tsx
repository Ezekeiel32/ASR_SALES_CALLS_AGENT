import React, { useState } from 'react';
import { motion } from 'framer-motion';

const SettingsPage: React.FC = () => {
    const [activeTab, setActiveTab] = useState('profile');

  return (
    <div style={{ paddingTop: '80px', maxWidth: '800px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '2.25rem', fontWeight: 700, marginBottom: '2rem' }}>הגדרות</h1>
      
      <div style={{ display: 'flex', gap: '2rem' }}>
        {/* Settings Navigation */}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', flexBasis: '200px' }}>
          <button onClick={() => setActiveTab('profile')} style={{ ...navButtonStyle, ...(activeTab === 'profile' ? activeNavButtonStyle : {}) }}>פרופיל</button>
          <button onClick={() => setActiveTab('notifications')} style={{ ...navButtonStyle, ...(activeTab === 'notifications' ? activeNavButtonStyle : {}) }}>התראות</button>
          <button onClick={() => setActiveTab('organization')} style={{ ...navButtonStyle, ...(activeTab === 'organization' ? activeNavButtonStyle : {}) }}>ארגון</button>
          <button onClick={() => setActiveTab('billing')} style={{ ...navButtonStyle, ...(activeTab === 'billing' ? activeNavButtonStyle : {}) }}>חיוב</button>
        </nav>

        {/* Settings Content */}
        <main style={{ flex: 1 }}>
            {activeTab === 'profile' && <ProfileSettings />}
            {/* Add other settings components here */}
        </main>
      </div>
    </div>
  );
};


const ProfileSettings = () => (
    <motion.div 
        key="profile"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        style={panelStyle}
    >
        <h2 style={panelHeaderStyle}>הגדרות פרופיל</h2>
        <div style={formGroupStyle}>
            <label style={labelStyle}>שם מלא</label>
            <input type="text" defaultValue="יעל לוי" style={inputStyle} />
        </div>
        <div style={formGroupStyle}>
            <label style={labelStyle}>כתובת אימייל</label>
            <input type="email" defaultValue="yael@example.com" style={inputStyle} />
        </div>
        <div style={formGroupStyle}>
            <label style={labelStyle}>תמונת פרופיל</label>
            <div style={{display: 'flex', alignItems: 'center', gap: '1rem'}}>
                <img src={`https://i.pravatar.cc/150?u=user`} alt="Avatar" style={{width: 48, height: 48, borderRadius: '50%'}}/>
                <button style={secondaryButtonStyle}>העלה תמונה חדשה</button>
            </div>
        </div>
        <div style={{ borderTop: '1px solid #F3F4F6', paddingTop: '1.5rem', marginTop: '1.5rem', textAlign: 'left' }}>
            <button style={primaryButtonStyle}>שמור שינויים</button>
        </div>
    </motion.div>
);


// Styles
const navButtonStyle: React.CSSProperties = {
    padding: '0.75rem 1rem',
    border: 'none',
    background: 'none',
    borderRadius: '8px',
    textAlign: 'right',
    fontWeight: 600,
    fontSize: '0.9rem',
    color: '#374151',
    cursor: 'pointer'
};
const activeNavButtonStyle: React.CSSProperties = {
    backgroundColor: '#E6FFFA',
    color: '#14B8A6'
};
const panelStyle: React.CSSProperties = {
    backgroundColor: 'white',
    borderRadius: '12px',
    padding: '2rem',
    border: '1px solid #E2E8F0',
};
const panelHeaderStyle: React.CSSProperties = {
    margin: '0 0 2rem 0',
    fontSize: '1.25rem',
    fontWeight: 600,
};
const formGroupStyle: React.CSSProperties = {
    marginBottom: '1.5rem'
};
const labelStyle: React.CSSProperties = {
    display: 'block',
    fontWeight: 600,
    fontSize: '0.9rem',
    marginBottom: '0.5rem'
};
const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '0.75rem 1rem',
    border: '1px solid #D1D5DB',
    borderRadius: '8px',
    fontSize: '1rem',
    backgroundColor: '#F9FAFB'
};
const primaryButtonStyle: React.CSSProperties = { padding: '0.6rem 1.25rem', border: 'none', borderRadius: '8px', backgroundColor: '#14B8A6', color: 'white', cursor: 'pointer', fontSize: '0.9rem', fontWeight: 600 };
const secondaryButtonStyle: React.CSSProperties = { padding: '0.6rem 1.25rem', border: '1px solid #D1D5DB', borderRadius: '8px', backgroundColor: 'white', color: '#374151', cursor: 'pointer', fontSize: '0.9rem', fontWeight: 600 };

export default SettingsPage;
