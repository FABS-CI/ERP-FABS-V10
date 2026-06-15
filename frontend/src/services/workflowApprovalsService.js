import axios from "axios";
import { getApiBase } from '../config/api';

const API = getApiBase("/workflow-approvals");

// Workflows
export const listWorkflows = async (filters = {}) => {
  const response = await axios.get(`${API}/workflows`, { params: filters });
  return response.data;
};

export const createWorkflow = async (data) => {
  const response = await axios.post(`${API}/workflows`, data);
  return response.data;
};

// Approvals
export const createApprovalStep = async (data) => {
  const response = await axios.post(`${API}/approvals`, data);
  return response.data;
};

export const rejectWorkflow = async (workflowId, commentaire) => {
  const response = await axios.post(`${API}/rejections`, null, {
    params: { workflow_id: workflowId, commentaire },
  });
  return response.data;
};

// Signatures
export const createSignature = async (data) => {
  const response = await axios.post(`${API}/signatures`, data);
  return response.data;
};

// Audit Logs
export const listAuditLogs = async (filters = {}) => {
  const response = await axios.get(`${API}/audit-logs`, { params: filters });
  return response.data;
};
