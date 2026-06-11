/**
 * tokenHelpers.js
 * Utility functions for managing JWT tokens in localStorage.
 *
 * Keys:
 *   edu_access_token  — short-lived JWT access token (15 min)
 *   edu_refresh_token — long-lived refresh token (7 days)
 */

const ACCESS_KEY = 'edu_access_token';
const REFRESH_KEY = 'edu_refresh_token';

/** Retrieve the stored access token, or null if absent. */
export const getAccessToken = () => localStorage.getItem(ACCESS_KEY);

/** Retrieve the stored refresh token, or null if absent. */
export const getRefreshToken = () => localStorage.getItem(REFRESH_KEY);

/** Store a new access token (used after token refresh). */
export const setAccessToken = (token) => localStorage.setItem(ACCESS_KEY, token);

/** Store both access and refresh tokens (used after login/register). */
export const setTokens = (accessToken, refreshToken) => {
  localStorage.setItem(ACCESS_KEY, accessToken);
  localStorage.setItem(REFRESH_KEY, refreshToken);
};

/** Remove both tokens from localStorage (used on logout or auth failure). */
export const clearTokens = () => {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
};
