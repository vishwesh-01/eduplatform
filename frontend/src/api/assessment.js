/**
 * api/assessment.js — Adaptive assessment API calls.
 */

import apiClient from './axiosInstance';

/** Start a new quiz session */
export const startSession = () => apiClient.post('/assessment/start');

/** Submit an answer and get the next question or completion signal */
export const submitAnswer = (sessionId, questionId, selectedOption) =>
  apiClient.post('/assessment/answer', {
    session_id:      sessionId,
    question_id:     questionId,
    selected_option: selectedOption,
  });

/** Retrieve session state (used to resume after reconnect) */
export const getSession = (sessionId) => apiClient.get(`/assessment/session/${sessionId}`);
