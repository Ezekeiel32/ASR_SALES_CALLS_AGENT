import React from 'react';
import { motion } from 'framer-motion';
import { Speaker } from '../types';
import { SearchIcon, PlusIcon } from './IconComponents';

const SpeakerCard: React.FC<{ speaker: Speaker }> = ({ speaker }) => {
    return (
        <motion.div
            style={cardStyle}
            whileHover={{ y: -5, boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05)' }}
        >
            <img src={speaker.avatarUrl} alt={speaker.name} style={{ width: 64, height: 64, borderRadius: '50%', marginBottom: '1rem' }}/>
            <h3 style={{ margin: '0 0 0.25rem 0', fontWeight: 600, fontSize: '1.1rem' }}>{speaker.name}</h3>
            <p style={{ margin: 0, color: '#6B7280', fontSize: '0.9rem' }}>{speaker.label}</p>
            <div style={{ borderTop: '1px solid #F3F4F6', margin: '1rem -1.5rem', }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', fontSize: '0.85rem' }}>
                <div style={{textAlign: 'center'}}>
                    <p style={{margin: 0, color: '#6B7280'}}>פגישות</p>
                    <p style={{margin: 0, fontWeight: 600, fontSize: '1rem'}}>{speaker.meetings}</p>
                </div>
                <div style={{textAlign: 'center'}}>
                    <p style={{margin: 0, color: '#6B7280'}}>נראה לאחרונה</p>
                    <p style={{margin: 0, fontWeight: 600, fontSize: '1rem'}}>{speaker.lastSeen.toLocaleDateString('he-IL')}</p>
                </div>
            </div>
        </motion.div>
    );
};

const containerVariants = {
  hidden: { opacity: 1 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
    },
  },
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: { y: 0, opacity: 1 },
};


const SpeakersPage: React.FC<{ speakers: Speaker[] }> = ({ speakers }) => {
  return (
    <div style={{ paddingTop: '0' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2.25rem', fontWeight: 700, margin: 0 }}>ניהול דוברים</h1>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
            <SearchIcon style={{ position: 'absolute', right: '1rem', color: '#A0AEC0' }} width={20} height={20} />
            <input type="text" placeholder="חיפוש דובר..." style={{ padding: '0.6rem 2.75rem 0.6rem 1rem', border: '1px solid #E2E8F0', borderRadius: '8px', width: '250px', backgroundColor: '#fff', fontSize: '0.9rem' }} />
          </div>
          <button style={{ display: 'flex', alignItems: 'center', padding: '0.6rem 1.25rem', border: 'none', borderRadius: '8px', backgroundColor: '#14B8A6', color: 'white', cursor: 'pointer', fontSize: '0.9rem', fontWeight: 600 }}>
            <PlusIcon style={{ marginLeft: '0.5rem' }} width={20} height={20}/>
            <span>הוסף דובר</span>
          </button>
        </div>
      </div>
      
      {/* Speakers Grid */}
      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '1.5rem' }}
      >
        {speakers.map(speaker => (
          <motion.div key={speaker.id} variants={itemVariants}>
            <SpeakerCard speaker={speaker} />
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
};


const cardStyle: React.CSSProperties = {
    backgroundColor: 'white',
    borderRadius: '12px',
    padding: '1.5rem',
    border: '1px solid #E2E8F0',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    textAlign: 'center',
    transition: 'transform 0.2s, box-shadow 0.2s',
}


export default SpeakersPage;
