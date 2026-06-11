/**
 * LoginPage.jsx — User sign-in form.
 */

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import styles from './AuthPage.module.css';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate   = useNavigate();

  const [form,      setForm]      = useState({ email: '', password: '' });
  const [error,     setError]     = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      const user = await login(form.email, form.password);
      // Redirect based on whether onboarding is done
      navigate(user.goal_id ? '/dashboard' : '/onboarding');
    } catch (err) {
      setError(
        err.response?.data?.error?.message || 'Invalid email or password.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <h1 className={styles.title}>Sign In</h1>
        <p className={styles.subtitle}>Welcome back. Enter your credentials to continue.</p>

        {error && <div className={styles.errorBox}>{error}</div>}

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.field}>
            <label htmlFor="email" className={styles.label}>Email</label>
            <input
              id="email"
              name="email"
              type="email"
              value={form.email}
              onChange={handleChange}
              className={styles.input}
              placeholder="you@example.com"
              required
              autoComplete="email"
            />
          </div>

          <div className={styles.field}>
            <label htmlFor="password" className={styles.label}>Password</label>
            <input
              id="password"
              name="password"
              type="password"
              value={form.password}
              onChange={handleChange}
              className={styles.input}
              placeholder="Your password"
              required
              autoComplete="current-password"
            />
          </div>

          <button type="submit" disabled={isLoading} className={styles.btnSubmit}>
            {isLoading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className={styles.footer}>
          Don&apos;t have an account?{' '}
          <Link to="/register">Create one</Link>
        </p>
      </div>
    </div>
  );
}
