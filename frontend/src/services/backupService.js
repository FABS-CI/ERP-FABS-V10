import axios from "axios";
import { getApiBase } from '../config/api';

const API = getApiBase("/backup");

// ── Config ────────────────────────────────────────────────
export const getBackupConfig = async () => {
  const res = await axios.get(`${API}/config`);
  return res.data;
};

export const updateBackupConfig = async (data) => {
  const res = await axios.put(`${API}/config`, data);
  return res.data;
};

// ── Backups ───────────────────────────────────────────────
export const createBackup = async () => {
  const res = await axios.post(`${API}/backups`);
  return res.data;
};

export const listBackups = async (filters = {}) => {
  const res = await axios.get(`${API}/backups`, { params: filters });
  return res.data;
};

export const deleteBackup = async (backupId) => {
  const res = await axios.delete(`${API}/backups/${backupId}`);
  return res.data;
};

export const restoreBackup = async (backupId) => {
  const res = await axios.post(`${API}/restore`, { backup_id: backupId });
  return res.data;
};

// ── Stats disque local ────────────────────────────────────
export const getBackupStats = async () => {
  const res = await axios.get(`${API}/stats`);
  return res.data; // { backup_count, total_size_bytes, backup_path, disk: {total_gb, used_gb, free_gb} }
};
