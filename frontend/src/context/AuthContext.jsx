/**
 * AuthContext.jsx — Global authentication state and actions.
 *
 * Provides:
 *   user       — { id, name, email, roles, skill_level, goal_id } or null
 *   isLoading  — true while checking stored token on mount
 *   login()    — authenticates and stores tokens
 *   register() — registers new account and stores tokens
 *   logout()   — revokes refresh token and clears localStorage
 *   setUser()  — allows updating user object after profile changes
 */

import { createContext, useCallback, useEffect, useState } from 'react';
import { login as apiLogin, logout as apiLogout, register as apiRegister } from '../api/auth';
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from '../utils/tokenHelpers';

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user,      setUser]      = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  /**
   * On mount, check for a stored access token. If present, decode the payload
   * to restore the user state without a network call.
   * Falls back to clearing tokens if the token is unparseable.
   */
  useEffect(() => {
    const token = getAccessToken();
    if (token) {
      try {
        // JWT payload is base64url-encoded — decode without verification
        const payload = JSON.parse(atob(token.split('.')[1]));
        // Check token expiry
        if (payload.exp && Date.now() / 1000 > payload.exp) {
          // Token expired — clear and let the interceptor handle refresh on next request
          clearTokens();
          setUser(null);
        } else {
          // Restore minimal user state from token payload
          // Full profile will be fetched on first API call if needed
          setUser({ id: payload.sub, ...(payload.user || {}) });
        }
      } catch {
        clearTokens();
        setUser(null);
      }
    }
    setIsLoading(false);
  }, []);

  /**
   * login — Authenticate with email/password, store tokens, set user state.
   *
   * @param {string} email
   * @param {string} password
   * @returns {Promise<object>} User object on success
   * @throws {Error} On invalid credentials or network failure
   */
  const login = useCallback(async (email, password) => {
    const response = await apiLogin(email, password);
    const { access_token, refresh_token, user: userData } = response.data.data;
    setTokens(access_token, refresh_token);
    setUser(userData);
    return userData;
  }, []);

  /**
   * register — Create a new account, store tokens, set user state.
   *
   * @param {string} name
   * @param {string} email
   * @param {string} password
   * @returns {Promise<object>} User object on success
   */
  const register = useCallback(async (name, email, password) => {
    const response = await apiRegister(name, email, password);
    const { access_token, refresh_token, user: userData } = response.data.data;
    setTokens(access_token, refresh_token);
    setUser(userData);
    return userData;
  }, []);

  /**
   * logout — Revoke the refresh token on the server and clear local tokens.
   */
  const logout = useCallback(async () => {
    try {
      const refreshToken = getRefreshToken();
      if (refreshToken) await apiLogout(refreshToken);
    } catch {
      // Ignore network errors on logout — clear locally regardless
    } finally {
      clearTokens();
      setUser(null);
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}
