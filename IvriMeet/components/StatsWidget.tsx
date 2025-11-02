import React from 'react';
import { motion } from 'framer-motion';

interface StatsWidgetProps {
  icon: React.ReactNode;
  title: string;
  value: string;
}

const StatsWidget: React.FC<StatsWidgetProps> = ({ icon, title, value }) => {
  return (
    <motion.div
      style={widgetStyle}
      whileHover={{ scale: 1.05, boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05)' }}
      transition={{ type: 'spring', stiffness: 300 }}
    >
      <div style={iconContainerStyle}>
        {icon}
      </div>
      <div style={{textAlign: 'right'}}>
        <h3 style={titleStyle}>{title}</h3>
        <p style={valueStyle}>{value}</p>
      </div>
    </motion.div>
  );
};

// Styles
const widgetStyle: React.CSSProperties = {
  backgroundColor: 'white',
  padding: '1.5rem',
  borderRadius: '12px',
  boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06)',
  border: '1px solid #E2E8F0',
  display: 'flex',
  alignItems: 'center',
  gap: '1rem',
};

const iconContainerStyle: React.CSSProperties = {
    backgroundColor: '#E6FFFA', // Light Teal
    color: '#14B8A6', // Teal
    borderRadius: '50%',
    width: '50px',
    height: '50px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
};

const titleStyle: React.CSSProperties = {
  margin: '0 0 0.25rem 0',
  color: '#4A5568',
  fontSize: '0.9rem',
  fontWeight: 500,
};

const valueStyle: React.CSSProperties = {
  margin: 0,
  fontSize: '2rem',
  fontWeight: 700,
  color: '#1A202C',
};

export default StatsWidget;
