/**
 * api/courses.js — Courses, goals, and learning path API calls.
 */

import apiClient from './axiosInstance';

/** List all available learning goals */
export const getGoals = () => apiClient.get('/goals');

/** Set the authenticated learner's learning goal */
export const selectGoal = (goalId) => apiClient.post('/goals/select', { goal_id: goalId });

/** List paginated courses for the learner's goal */
export const getCourses = (page = 1, perPage = 10) =>
  apiClient.get('/courses', { params: { page, per_page: perPage } });

/** Get course detail with modules and video metadata */
export const getCourse = (courseId) => apiClient.get(`/courses/${courseId}`);

/** Get the current learner's active learning path */
export const getLearningPath = () => apiClient.get('/learning-path');

/** Get a specific learning path by ID */
export const getLearningPathById = (pathId) => apiClient.get(`/learning-path/${pathId}`);
