/**
 * api/admin.js — Admin API calls (require admin role).
 */

import apiClient from './axiosInstance';

/** Get platform-wide statistics */
export const getStats = () => apiClient.get('/admin/stats');

/** Get paginated user list with optional search and role filter */
export const getUsers = (page = 1, perPage = 20, search = '', role = '') =>
  apiClient.get('/admin/users', { params: { page, per_page: perPage, search, role } });

/** Get single user detail */
export const getUser = (userId) => apiClient.get(`/admin/users/${userId}`);

/** Update a user's role */
export const updateUserRole = (userId, role) =>
  apiClient.patch(`/admin/users/${userId}/role`, { role });

/** Deactivate a user account */
export const deactivateUser = (userId) =>
  apiClient.patch(`/admin/users/${userId}/deactivate`);

/** Get LLM content versions */
export const getContentVersions = (page = 1, entityType = '') =>
  apiClient.get('/admin/content', { params: { page, entity_type: entityType } });
