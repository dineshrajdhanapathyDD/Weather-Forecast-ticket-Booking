import React from 'react';
import './ResultsDisplay.css';

const ResultsDisplay = ({ results }) => {
  if (results.error) {
    return (
      <div className="results-container error">
        <h2>❌ Error</h2>
        <p>{results.error}</p>
      </div>
    );
  }

  const { weather_risk, comfort_advisory, fare_trend, booking_recommendation, alternative_windows } = results;

  const getRiskColor = (risk) => {
    if (risk?.toLowerCase().includes('high')) return '#e74c3c';
    if (risk?.toLowerCase().includes('medium')) return '#f39c12';
    return '#27ae60';
  };

  const getTrendColor = (trend) => {
    if (trend?.toLowerCase().includes('rising')) return '#e74c3c';
    if (trend?.toLowerCase().includes('dropping')) return '#27ae60';
    return '#3498db';
  };

  const getRecommendationIcon = (rec) => {
    if (rec?.toLowerCase().includes('book now')) return '✅';
    if (rec?.toLowerCase().includes('wait')) return '⏳';
    if (rec?.toLowerCase().includes('change')) return '🔄';
    return '💡';
  };

  return (
    <div className="results-container">
      <h2>📊 Your Booking Recommendation</h2>

      <div className="result-card weather-card">
        <div className="card-header">
          <h3>🌦️ Weather Risk Summary</h3>
          <span 
            className="risk-badge" 
            style={{ backgroundColor: getRiskColor(weather_risk) }}
          >
            {weather_risk}
          </span>
        </div>
        <div className="card-content">
          <p>{comfort_advisory}</p>
        </div>
      </div>

      <div className="result-card fare-card">
        <div className="card-header">
          <h3>💰 Fare Trend Insight</h3>
          <span 
            className="trend-badge" 
            style={{ backgroundColor: getTrendColor(fare_trend) }}
          >
            {fare_trend}
          </span>
        </div>
      </div>

      <div className="result-card recommendation-card">
        <div className="card-header">
          <h3>{getRecommendationIcon(booking_recommendation)} Final Recommendation</h3>
        </div>
        <div className="card-content">
          <div className="recommendation-text">
            {booking_recommendation}
          </div>
        </div>
      </div>

      {alternative_windows && alternative_windows.length > 0 && (
        <div className="result-card alternatives-card">
          <div className="card-header">
            <h3>🔁 Alternative Travel Windows</h3>
          </div>
          <div className="card-content">
            <div className="alternatives-grid">
              {alternative_windows.map((alt, index) => (
                <div key={index} className="alternative-item">
                  <div className="alt-dates">
                    📅 {alt.start_date} to {alt.end_date}
                  </div>
                  <div className="alt-details">
                    <span style={{ color: getRiskColor(alt.weather_risk) }}>
                      🌦️ {alt.weather_risk}
                    </span>
                    <span style={{ color: getTrendColor(alt.fare_trend) }}>
                      💰 {alt.fare_trend}
                    </span>
                  </div>
                  {alt.summary && (
                    <div className="alt-summary">
                      {alt.summary}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResultsDisplay;
