import axios from "axios";
import { getApiBase } from '../config/api';

const API = getApiBase("/notifications");

// Notifications
export const listNotifications = async (filters = {}) => {
  const response = await axios.get(`${API}`, { params: filters });
  return response.data;
};

export const listUnreadNotifications = async () => {
  const response = await axios.get(`${API}/non-lues`);
  return response.data;
};

export const countUnread = async () => {
  const response = await axios.get(`${API}/count`);
  return response.data;
};

export const markAsRead = async (notificationId) => {
  const response = await axios.patch(`${API}/${notificationId}/lire`);
  return response.data;
};

export const markAllAsRead = async () => {
  const response = await axios.patch(`${API}/tout-lire`);
  return response.data;
};

export const deleteNotification = async (notificationId) => {
  const response = await axios.delete(`${API}/${notificationId}`);
  return response.data;
};

// Préférences
export const getPreferences = async () => {
  const response = await axios.get(`${API}/preferences`);
  return response.data;
};

export const updatePreferences = async (data) => {
  const response = await axios.put(`${API}/preferences`, data);
  return response.data;
};

// Email Templates (Admin)
export const listEmailTemplates = async () => {
  const response = await axios.get(`${API}/templates`);
  return response.data;
};

export const createEmailTemplate = async (data) => {
  const response = await axios.post(`${API}/templates`, data);
  return response.data;
};

export const updateEmailTemplate = async (templateId, data) => {
  const response = await axios.put(`${API}/templates/${templateId}`, data);
  return response.data;
};

export const deleteEmailTemplate = async (templateId) => {
  const response = await axios.delete(`${API}/templates/${templateId}`);
  return response.data;
};

// Email Logs (Admin)
export const listEmailLogs = async (filters = {}) => {
  const response = await axios.get(`${API}/logs`, { params: filters });
  return response.data;
};

// Test
export const sendTestNotification = async () => {
  const response = await axios.post(`${API}/test`);
  return response.data;
};
