/**
 * ProgressPage.jsx — Detailed progress view with streak and per-course bars.
 */

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getProgressSummary } from '../../api/progress';
import styles from './ProgressPage.module.css';

export default function ProgressPage() {
  const [summary,   setSummary]   = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getProgressSummary()
      .then(res => setSummary(res.data.data))
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) return <div className={styles.center}>Loading progress...</div>;

  return (
    <div className={styles.page}>
      <div className={styles.container}>
        <h1 className={styles.title}>Your Progress</h1>

        {/* Overview */}
        <div className={styles.overview}>
          <div className={styles.overviewCard}>
            <span className={styles.bigNum}>{Math.round(summary?.overall_completion_pct ?? 0)}%</span>
            <span className={styles.bigLabel}>Overall Completion</span>
          </div>
          <div className={styles.overviewCard}>
            <span className={styles.bigNum}>{summary?.streak_days ?? 0}</span>
            <span className={styles.bigLabel}>Day Streak</span>
          </div>
          <div className={styles.overviewCard}>
            <span className={styles.bigNum}>{summary?.certificates_earned ?? 0}</span>
            <span className={styles.bigLabel}>Certificates Earned</span>
          </div>
        </div>

        {/* Per-course progress */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>Course Progress</h2>
          {summary?.course_statuses?.length > 0 ? (
            <div className={styles.courseList}>
              {summary.course_statuses.map(c => (
                <div key={c.course_id} className={styles.courseRow}>
                  <div className={styles.courseInfo}>
                    <Link to={`/courses/${c.course_id}`} className={styles.courseLink}>
                      {c.title}
                    </Link>
                    {c.completed && <span className={styles.badge}>Completed</span>}
                  </div>
                  <div className={styles.barRow}>
                    <div className={styles.bar}>
                      <div
                        className={styles.barFill}
                        style={{ width: `${c.completion_percentage}%` }}
                      />
                    </div>
                    <span className={styles.barLabel}>
                      {Math.round(c.completion_percentage)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className={styles.empty}>No courses enrolled yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}
