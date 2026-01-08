import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Subscription APIs
export const parseBookMyShowURL = async (url) => {
  const response = await api.post('/subscriptions/parse-url', null, {
    params: { url }
  });
  return response.data;
};

export const createSubscription = async (subscriptionData) => {
  const response = await api.post('/subscriptions/create', subscriptionData);
  return response.data;
};

export const getUserSubscriptions = async (email) => {
  const response = await api.get(`/subscriptions/user/${email}`);
  return response.data;
};

export const deleteSubscription = async (subscriptionId) => {
  const response = await api.delete(`/subscriptions/${subscriptionId}`);
  return response.data;
};

// Theater APIs
export const searchTheaters = async (params = {}) => {
  const response = await api.get('/theaters/search', { params });
  return response.data;
};

export const getTheater = async (theaterId) => {
  const response = await api.get(`/theaters/${theaterId}`);
  return response.data;
};

// Movie APIs
export const getMoviesByTheater = async (theaterId, showDate = null) => {
  const params = showDate ? { show_date: showDate } : {};
  const response = await api.get(`/movies/theater/${theaterId}`, { params });
  return response.data;
};

export const searchMovies = async (params = {}) => {
  const response = await api.get('/movies/search', { params });
  return response.data;
};

// Test APIs
export const testScraping = async (bmsUrl) => {
  const response = await api.post('/subscriptions/test-scraping', null, {
    params: { bms_url: bmsUrl }
  });
  return response.data;
};

export default api;
