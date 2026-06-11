/**
 * api/progress.js — Progress tracking API calls.
 */

import apiClient from './axiosInstance';

/** Mark a module as complete */
export const completeModule = (moduleId) =>
  apiClient.post(`/progress/module/${moduleId}/complete`);

/** Get per-course completion percentage and completed module IDs */
export const getCourseProgress = (courseId) =>
  apiClient.get(`/progress/course/${courseId}`);

/** Get overall progress summary for the dashboard */
export const getProgressSummary = () => apiClient.get('/progress/summary');
