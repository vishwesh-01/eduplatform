/**
 * ProfilePage.jsx — View and update name and email.
 */

import { useState } from 'react';
import { toast } from 'react-toastify';
import apiClient from '../../api/axiosInstance';
import { useAuth } from '../../hooks/useAuth';
import styles from '../Login/AuthPage.module.css';

export default function ProfilePage() {
  const { user, setUser } = useAuth();

  const [form,      setForm]      = useState({ name: user?.name || '', email: user?.email || '' });
  const [isLoading, setIsLoading] = useState(false);
  const [error,     setError]     = useState('');

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      const res = await apiClient.patch('/auth/profile', form);
      setUser({ ...user, ...res.data.data.user });
      toast.success('Profile updated successfully.');
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Update failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <h1 className={styles.title}>Profile</h1>
        <p className={styles.subtitle}>Update your name or email address.</p>

        {error && <div className={styles.errorBox}>{error}</div>}

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.field}>
            <label htmlFor="name" className={styles.label}>Full Name</label>
            <input
              id="name" name="name" type="text"
              value={form.name} onChange={handleChange}
              className={styles.input} required
            />
          </div>

          <div className={styles.field}>
            <label htmlFor="email" className={styles.label}>Email</label>
            <input
              id="email" name="email" type="email"
              value={form.email} onChange={handleChange}
              className={styles.input} required
            />
          </div>

          <button type="submit" disabled={isLoading} className={styles.btnSubmit}>
            {isLoading ? 'Saving...' : 'Save Changes'}
          </button>
        </form>
      </div>
    </div>
  );
}
