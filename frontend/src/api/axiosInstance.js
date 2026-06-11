/**
 * axiosInstance.js — Axios client with JWT interceptors.
 *
 * Request interceptor:  Attaches Bearer access token to every request.
 * Response interceptor: On 401 TOKEN_EXPIRED → refresh → retry original.
 *                       On all 4xx/5xx → show toast notification.
 *                       On refresh failure → clear tokens + redirect to /login.
 */

import axios from 'axios';
import { toast } from 'react-toastify';
import { clearTokens, getAccessToken, getRefreshToken, setAccessToken } from '../utils/tokenHelpers';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5000/api/v1',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Request interceptor ───────────────────────────────────────────────────────
apiClient.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Response interceptor ──────────────────────────────────────────────────────
let isRefreshing  = false;
let failedQueue   = [];  // Requests queued while a refresh is in progress

const processQueue = (error, token = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) { reject(error); } else { resolve(token); }
  });
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Only intercept 401 TOKEN_EXPIRED — not other 401s (wrong password, etc.)
    const isExpired =
      error.response?.status === 401 &&
      error.response?.data?.error?.code === 'TOKEN_EXPIRED';

    if (isExpired && !originalRequest._retry) {
      // Queue concurrent requests while refresh is happening
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return apiClient(originalRequest);
        }).catch(err => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = getRefreshToken();
        if (!refreshToken) throw new Error('No refresh token');

        // Call refresh endpoint directly (no interceptor loop)
        const { data } = await axios.post(
          `${apiClient.defaults.baseURL}/auth/refresh`,
          null,
          { headers: { Authorization: `Bearer ${refreshToken}` } }
        );
        const newToken = data.data.access_token;
        setAccessToken(newToken);
        processQueue(null, newToken);
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        clearTokens();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // Show a toast for all 4xx/5xx errors (except 401 handled above)
    const shouldToast = error.response?.status && error.response.status !== 401;
    if (shouldToast) {
      const message =
        error.response?.data?.error?.message ||
        `Request failed (${error.response?.status})`;
      toast.error(message);
    }

    return Promise.reject(error);
  }
);

export default apiClient;
