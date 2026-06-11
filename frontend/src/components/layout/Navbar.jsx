/**
 * Navbar.jsx — Top navigation bar.
 * Shows different links depending on authentication state and role.
 */

import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import styles from './Navbar.module.css';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <nav className={styles.navbar}>
      <div className={styles.container}>
        <Link to="/" className={styles.brand}>EduPlatform</Link>

        <div className={styles.links}>
          {user ? (
            <>
              <Link to="/dashboard"    className={styles.link}>Dashboard</Link>
              <Link to="/progress"     className={styles.link}>Progress</Link>
              <Link to="/certificates" className={styles.link}>Certificates</Link>
              <Link to="/profile"      className={styles.link}>Profile</Link>
              {user.roles?.includes('admin') && (
                <Link to="/admin" className={styles.link}>Admin</Link>
              )}
              <button onClick={handleLogout} className={styles.btnLogout}>
                Sign Out
              </button>
            </>
          ) : (
            <>
              <Link to="/login"    className={styles.link}>Sign In</Link>
              <Link to="/register" className={styles.btnPrimary}>Get Started</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
