import React from 'react';
import './StatsCard.css';

const StatsCard = ({ title, value, icon }) => {
  return (
    <div className="stats-card">
      <div className="stats-card-content">
        <div className="stats-card-icon">
          {icon}
        </div>
        <div className="stats-card-info">
          <h3>{title}</h3>
          <p className="stats-card-value">{value}</p>
        </div>
      </div>
    </div>
  );
};

export default StatsCard;