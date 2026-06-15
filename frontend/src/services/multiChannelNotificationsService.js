import axios from "axios";
import { getApiBase } from '../config/api';

const API = getApiBase("/multi-channel-notifications");

// SMS
export const sendSMS = async (data) => {
  const response = await axios.post(`${API}/sms`, data);
  return response.data;
};

// WhatsApp
export const sendWhatsApp = async (data) => {
  const response = await axios.post(`${API}/whatsapp`, data);
  return response.data;
};

// Email
export const sendEmail = async (data) => {
  const response = await axios.post(`${API}/email`, data);
  return response.data;
};

// Batch
export const sendBatchNotifications = async (data) => {
  const response = await axios.post(`${API}/batch`, data);
  return response.data;
};

// Logs
export const listNotificationLogs = async (filters = {}) => {
  const response = await axios.get(`${API}/logs`, { params: filters });
  return response.data;
};

// Configuration Check
export const checkConfiguration = async () => {
  const response = await axios.get(`${API}/config-check`);
  return response.data;
};
