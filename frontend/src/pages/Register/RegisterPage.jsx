/**
 * RegisterPage.jsx — New user registration form.
 * Validates password client-side before submitting.
 */

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import styles from '../Login/AuthPage.module.css';

const PASSWORD_REGEX = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [form,      setForm]      = useState({ name: '', email: '', password: '' });
  const [errors,    setErrors]    = useState({});
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setErrors({ ...errors, [e.target.name]: '' });
  };

  const validate = () => {
    const errs = {};
    if (!form.name.trim() || form.name.trim().length < 2)
      errs.name = 'Name must be at least 2 characters.';
    if (!form.email.includes('@'))
      errs.email = 'Enter a valid email address.';
    if (!PASSWORD_REGEX.test(form.password))
      errs.password = 'Password needs 8+ characters, one uppercase, one lowercase, and one digit.';
    return errs;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }

    setIsLoading(true);
    try {
      await register(form.name.trim(), form.email, form.password);
      navigate('/onboarding');
    } catch (err) {
      const msg = err.response?.data?.error?.message || 'Registration failed. Please try again.';
      setErrors({ general: msg });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <h1 className={styles.title}>Create Account</h1>
        <p className={styles.subtitle}>Join the platform and start your personalised learning journey.</p>

        {errors.general && <div className={styles.errorBox}>{errors.general}</div>}

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.field}>
            <label htmlFor="name" className={styles.label}>Full Name</label>
            <input
              id="name" name="name" type="text"
              value={form.name} onChange={handleChange}
              className={styles.input} placeholder="Jane Smith" required
            />
            {errors.name && <span className={styles.errorBox} style={{ padding: '0.4rem 0.75rem' }}>{errors.name}</span>}
          </div>

          <div className={styles.field}>
            <label htmlFor="email" className={styles.label}>Email</label>
            <input
              id="email" name="email" type="email"
              value={form.email} onChange={handleChange}
              className={styles.input} placeholder="you@example.com" required
              autoComplete="email"
            />
            {errors.email && <span className={styles.errorBox} style={{ padding: '0.4rem 0.75rem' }}>{errors.email}</span>}
          </div>

          <div className={styles.field}>
            <label htmlFor="password" className={styles.label}>Password</label>
            <input
              id="password" name="password" type="password"
              value={form.password} onChange={handleChange}
              className={styles.input} placeholder="Min 8 chars, upper, lower, digit" required
              autoComplete="new-password"
            />
            <span className={styles.hint}>At least 8 characters with one uppercase, one lowercase, and one digit.</span>
            {errors.password && <span className={styles.errorBox} style={{ padding: '0.4rem 0.75rem' }}>{errors.password}</span>}
          </div>

          <button type="submit" disabled={isLoading} className={styles.btnSubmit}>
            {isLoading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <p className={styles.footer}>
          Already have an account?{' '}
          <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
