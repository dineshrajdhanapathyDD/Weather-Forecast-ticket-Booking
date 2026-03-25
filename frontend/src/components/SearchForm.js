import React, { useState } from 'react';
import axios from 'axios';
import { format, addDays } from 'date-fns';
import './SearchForm.css';

const SearchForm = ({ setResults, setLoading }) => {
  const today = format(new Date(), 'yyyy-MM-dd');
  const nextWeek = format(addDays(new Date(), 7), 'yyyy-MM-dd');
  const twoWeeks = format(addDays(new Date(), 14), 'yyyy-MM-dd');

  const [formData, setFormData] = useState({
    origin: '',
    destination: '',
    startDate: nextWeek,
    endDate: twoWeeks
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResults(null);

    try {
      const API_ENDPOINT = process.env.REACT_APP_API_ENDPOINT || 'https://6rx3afsola.execute-api.us-east-2.amazonaws.com/prod';
      
      const response = await axios.post(`${API_ENDPOINT}/recommend`, {
        origin: formData.origin.toUpperCase(),
        destination: formData.destination.toUpperCase(),
        travel_window: {
          start_date: formData.startDate,
          end_date: formData.endDate
        }
      });

      // Extract data from the response (Lambda returns {success: true, data: {...}})
      if (response.data.success && response.data.data) {
        setResults(response.data.data);
      } else if (response.data.error) {
        setResults({
          error: response.data.error.message || 'Failed to get recommendation'
        });
      } else {
        setResults(response.data);
      }
    } catch (error) {
      console.error('Error:', error);
      setResults({
        error: 'Failed to get recommendation. Please check your inputs and try again.'
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="search-form-container">
      <form className="search-form" onSubmit={handleSubmit}>
        <h2>🔍 Search Flight Recommendations</h2>
        
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="origin">
              ✈️ From (Airport Code)
            </label>
            <input
              type="text"
              id="origin"
              name="origin"
              value={formData.origin}
              onChange={handleChange}
              placeholder="e.g., JFK"
              maxLength="3"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="destination">
              🎯 To (Airport Code)
            </label>
            <input
              type="text"
              id="destination"
              name="destination"
              value={formData.destination}
              onChange={handleChange}
              placeholder="e.g., LAX"
              maxLength="3"
              required
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="startDate">
              📅 Departure Date
            </label>
            <input
              type="date"
              id="startDate"
              name="startDate"
              value={formData.startDate}
              onChange={handleChange}
              min={today}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="endDate">
              📅 Return Date
            </label>
            <input
              type="date"
              id="endDate"
              name="endDate"
              value={formData.endDate}
              onChange={handleChange}
              min={formData.startDate}
              required
            />
          </div>
        </div>

        <button type="submit" className="search-button">
          🌦️ Get Weather-Wise Recommendation
        </button>
      </form>

      <div className="popular-routes">
        <h3>✈️ Popular Routes</h3>
        <div className="route-buttons">
          <button type="button" onClick={() => setFormData({...formData, origin: 'JFK', destination: 'LAX'})}>
            🗽 New York → 🌴 Los Angeles
          </button>
          <button type="button" onClick={() => setFormData({...formData, origin: 'ORD', destination: 'MIA'})}>
            🌆 Chicago → 🏖️ Miami
          </button>
          <button type="button" onClick={() => setFormData({...formData, origin: 'SFO', destination: 'JFK'})}>
            🌉 San Francisco → 🗽 New York
          </button>
          <button type="button" onClick={() => setFormData({...formData, origin: 'MAA', destination: 'DEL'})}>
            🇮🇳 Chennai → 🇮🇳 Delhi
          </button>
          <button type="button" onClick={() => setFormData({...formData, origin: 'BOM', destination: 'BLR'})}>
            🇮🇳 Mumbai → 🇮🇳 Bangalore
          </button>
        </div>
      </div>
    </div>
  );
};

export default SearchForm;
