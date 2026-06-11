import apiClient from './axiosInstance';

/** Register a new user — returns { access_token, refresh_token } */
export const register = (name, email, password) =>
  apiClient.post('/auth/register', { name, email, password });

/** Login — returns { access_token, refresh_token } */
export const login = (email, password) =>
  apiClient.post('/auth/login', { email, password });

/** Logout — invalidates the refresh token */
export const logout = (refreshToken) =>
  apiClient.post('/auth/logout', null, {
    headers: { Authorization: `Bearer ${refreshToken}` },
  });

/** Refresh the access token */
export const refreshToken = (refreshTokenValue) =>
  apiClient.post('/auth/refresh', null, {
    headers: { Authorization: `Bearer ${refreshTokenValue}` },
  });
