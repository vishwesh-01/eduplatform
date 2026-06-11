/**
 * AdminPage.jsx — Admin dashboard with Stats, Users, and Content tabs.
 */

import { useEffect, useState } from 'react';
import { deactivateUser, getContentVersions, getStats, getUsers, updateUserRole } from '../../api/admin';
import styles from './AdminPage.module.css';

export default function AdminPage() {
  const [tab, setTab] = useState('stats');

  return (
    <div className={styles.page}>
      <div className={styles.container}>
        <h1 className={styles.title}>Admin Dashboard</h1>

        <div className={styles.tabs}>
          {['stats', 'users', 'content'].map(t => (
            <button
              key={t}
              className={`${styles.tab} ${tab === t ? styles.activeTab : ''}`}
              onClick={() => setTab(t)}
            >
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>

        {tab === 'stats'   && <StatsTab />}
        {tab === 'users'   && <UsersTab />}
        {tab === 'content' && <ContentTab />}
      </div>
    </div>
  );
}

/* ── Stats Tab ─────────────────────────────────────────────────────────────── */
function StatsTab() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    getStats().then(res => setStats(res.data.data)).catch(() => {});
  }, []);

  if (!stats) return <div className={styles.loading}>Loading statistics...</div>;

  const items = [
    { label: 'Total Users',       value: stats.total_users },
    { label: 'Active (30 days)',  value: stats.active_users },
    { label: 'Total Courses',     value: stats.total_courses },
    { label: 'Certificates Issued', value: stats.total_certificates },
    { label: 'Avg Skill Level',   value: `${stats.avg_skill_level}/100` },
  ];

  return (
    <div className={styles.statsGrid}>
      {items.map(item => (
        <div key={item.label} className={styles.statCard}>
          <span className={styles.statValue}>{item.value}</span>
          <span className={styles.statLabel}>{item.label}</span>
        </div>
      ))}
    </div>
  );
}

/* ── Users Tab ─────────────────────────────────────────────────────────────── */
function UsersTab() {
  const [users,   setUsers]   = useState([]);
  const [search,  setSearch]  = useState('');
  const [page,    setPage]    = useState(1);
  const [total,   setTotal]   = useState(0);
  const [loading, setLoading] = useState(true);
  const PER_PAGE = 20;

  const load = (p = 1, s = search) => {
    setLoading(true);
    getUsers(p, PER_PAGE, s)
      .then(res => {
        const d = res.data.data;
        setUsers(d.users || []);
        setTotal(d.total || 0);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    load(1, search);
  };

  const handleRoleToggle = async (userId, currentRoles) => {
    const newRole = currentRoles.includes('admin') ? 'student' : 'admin';
    if (!window.confirm(`Change role to '${newRole}'?`)) return;
    try {
      await updateUserRole(userId, newRole);
      load(page);
    } catch { alert('Failed to update role.'); }
  };

  const handleDeactivate = async (userId) => {
    if (!window.confirm('Deactivate this user? They will no longer be able to sign in.')) return;
    try {
      await deactivateUser(userId);
      load(page);
    } catch { alert('Failed to deactivate user.'); }
  };

  return (
    <div>
      <form onSubmit={handleSearch} className={styles.searchRow}>
        <input
          type="text" placeholder="Search by name or email..."
          value={search} onChange={e => setSearch(e.target.value)}
          className={styles.searchInput}
        />
        <button type="submit" className={styles.btnSearch}>Search</button>
      </form>

      {loading ? (
        <div className={styles.loading}>Loading users...</div>
      ) : (
        <>
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Name</th><th>Email</th><th>Role</th>
                  <th>Skill</th><th>Status</th><th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id}>
                    <td>{u.name}</td>
                    <td>{u.email}</td>
                    <td><span className={styles.roleBadge}>{u.roles?.join(', ')}</span></td>
                    <td>{u.skill_level ?? '-'}</td>
                    <td>
                      <span className={u.is_active ? styles.active : styles.inactive}>
                        {u.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className={styles.actions}>
                      <button
                        className={styles.btnAction}
                        onClick={() => handleRoleToggle(u.id, u.roles || [])}
                      >
                        {u.roles?.includes('admin') ? 'Make Student' : 'Make Admin'}
                      </button>
                      {u.is_active && (
                        <button
                          className={`${styles.btnAction} ${styles.btnDanger}`}
                          onClick={() => handleDeactivate(u.id)}
                        >
                          Deactivate
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className={styles.pagination}>
            <button
              disabled={page === 1}
              onClick={() => { setPage(p => p - 1); load(page - 1); }}
              className={styles.btnPage}
            >
              Previous
            </button>
            <span className={styles.pageInfo}>
              Page {page} — {total} total users
            </span>
            <button
              disabled={page * PER_PAGE >= total}
              onClick={() => { setPage(p => p + 1); load(page + 1); }}
              className={styles.btnPage}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}

/* ── Content Tab ───────────────────────────────────────────────────────────── */
function ContentTab() {
  const [versions, setVersions] = useState([]);
  const [filter,   setFilter]   = useState('');
  const [loading,  setLoading]  = useState(true);
  const [expanded, setExpanded] = useState(null);

  const load = () => {
    setLoading(true);
    getContentVersions(1, filter)
      .then(res => setVersions(res.data.data.versions || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div>
      <div className={styles.filterRow}>
        <input
          type="text" placeholder="Filter by entity type (e.g. learning_path)..."
          value={filter} onChange={e => setFilter(e.target.value)}
          className={styles.searchInput}
        />
        <button onClick={load} className={styles.btnSearch}>Filter</button>
      </div>

      {loading ? (
        <div className={styles.loading}>Loading content versions...</div>
      ) : versions.length === 0 ? (
        <p className={styles.empty}>No content versions found.</p>
      ) : (
        <div className={styles.versionList}>
          {versions.map(v => (
            <div key={v.id} className={styles.versionCard}>
              <div className={styles.versionHeader} onClick={() => setExpanded(expanded === v.id ? null : v.id)}>
                <span className={styles.entityType}>{v.entity_type}</span>
                <span className={styles.versionNum}>v{v.version_number}</span>
                <span className={styles.versionDate}>{new Date(v.created_at).toLocaleString()}</span>
                <span className={`${styles.contentBadge} ${v.has_content ? styles.success : styles.fail}`}>
                  {v.has_content ? 'Success' : 'Failed'}
                </span>
                <span className={styles.expandBtn}>{expanded === v.id ? '▲' : '▼'}</span>
              </div>
              {expanded === v.id && (
                <div className={styles.versionBody}>
                  <p className={styles.promptLabel}>Prompt (first 200 chars):</p>
                  <pre className={styles.pre}>{v.prompt_used}</pre>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
