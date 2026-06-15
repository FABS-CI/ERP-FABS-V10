import axios from "axios";
import { getApiBase } from '../config/api';

const API = getApiBase("/file-storage");

// Documents
export const listDocuments = async (filters = {}) => {
  const response = await axios.get(`${API}/documents`, { params: filters });
  return response.data;
};

export const uploadDocument = async (file, typeDocument, entiteType, entiteId, description) => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await axios.post(`${API}/documents/upload`, formData, {
    params: { type_document: typeDocument, entite_type: entiteType, entite_id: entiteId, description },
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
};

export const getDocument = async (documentId) => {
  const response = await axios.get(`${API}/documents/${documentId}`);
  return response.data;
};

export const deleteDocument = async (documentId) => {
  const response = await axios.delete(`${API}/documents/${documentId}`);
  return response.data;
};

// Factures PDF
export const listFacturesPDF = async (filters = {}) => {
  const response = await axios.get(`${API}/factures-pdf`, { params: filters });
  return response.data;
};

export const createFacturePDF = async (data) => {
  const response = await axios.post(`${API}/factures-pdf`, data);
  return response.data;
};

// Storage Stats
export const getStorageStats = async () => {
  const response = await axios.get(`${API}/stats`);
  return response.data;
};
