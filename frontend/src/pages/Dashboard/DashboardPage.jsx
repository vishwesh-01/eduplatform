/**
 * DashboardPage.jsx — Main learner dashboard.
 * Shows stats, quiz score chart, course status chart, and enrolled courses.
 */

import { ArcElement, CategoryScale, Chart as ChartJS, Legend, LinearScale, LineElement, PointElement, Tooltip } from 'chart.js';
import { useEffect, useState } from 'react';
import { Doughnut, Line } from 'react-chartjs-2';
import { Link } from 'react-router-dom';
import { getProgressSummary } from '../../api/progress';
import { useAuth } from '../../hooks/useAuth';
import styles from './DashboardPage.module.css';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, ArcElement, Tooltip, Legend);

export default function DashboardPage() {
  const { user } = useAuth();
  const [summary,   setSummary]   = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getProgressSummary()
      .then(res => setSummary(res.data.data))
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) return <div className={styles.center}>Loading dashboard...</div>;

  const quizLabels = summary?.quiz_history?.map(q => q.date) ?? [];
  const quizScores = summary?.quiz_history?.map(q => q.score) ?? [];

  const completed   = summary?.course_statuses?.filter(c => c.completed).length ?? 0;
  const inProgress  = (summary?.total_enrolled ?? 0) - completed;

  return (
    <div className={styles.page}>
      <div className={styles.container}>
        <h1 className={styles.heading}>
          Welcome back{user?.name ? `, ${user.name}` : ''}.
        </h1>

        {/* Stat cards */}
        <div className={styles.statsGrid}>
          <StatCard label="Skill Level"        value={summary?.skill_level ?? 'Not assessed'} unit={summary?.skill_level != null ? '/100' : ''} />
          <StatCard label="Courses Enrolled"   value={summary?.total_enrolled ?? 0} />
          <StatCard label="Certificates"       value={summary?.certificates_earned ?? 0} />
          <StatCard label="Day Streak"         value={summary?.streak_days ?? 0} unit=" days" />
        </div>

        {/* Charts */}
        <div className={styles.chartsRow}>
          <div className={styles.chartCard}>
            <h2 className={styles.chartTitle}>Quiz Score History</h2>
            {quizLabels.length > 0 ? (
              <Line
                data={{
                  labels: quizLabels,
                  datasets: [{
                    label: 'Score (%)',
                    data: quizScores,
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37,99,235,0.08)',
                    tension: 0.4,
                    pointRadius: 4,
                  }],
                }}
                options={{ responsive: true, plugins: { legend: { display: false } }, scales: { y: { min: 0, max: 100 } } }}
              />
            ) : (
              <p className={styles.empty}>Complete an assessment to see your score history.</p>
            )}
          </div>

          <div className={styles.chartCard}>
            <h2 className={styles.chartTitle}>Course Status</h2>
            {summary?.total_enrolled > 0 ? (
              <Doughnut
                data={{
                  labels: ['Completed', 'In Progress'],
                  datasets: [{ data: [completed, inProgress], backgroundColor: ['#16a34a', '#2563eb'] }],
                }}
                options={{ responsive: true, plugins: { legend: { position: 'bottom' } } }}
              />
            ) : (
              <p className={styles.empty}>No courses enrolled yet.</p>
            )}
          </div>
        </div>

        {/* Course list */}
        <div className={styles.section}>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>Your Courses</h2>
            {summary?.skill_level != null && (
              <Link to="/assessment" className={styles.linkBtn}>Retake Assessment</Link>
            )}
          </div>

          {summary?.course_statuses?.length > 0 ? (
            <div className={styles.courseGrid}>
              {summary.course_statuses.map(c => (
                <Link key={c.course_id} to={`/courses/${c.course_id}`} className={styles.courseCard}>
                  <h3 className={styles.courseTitle}>{c.title}</h3>
                  <div className={styles.progressBar}>
                    <div
                      className={styles.progressFill}
                      style={{ width: `${c.completion_percentage}%` }}
                    />
                  </div>
                  <span className={styles.progressText}>{Math.round(c.completion_percentage)}% complete</span>
                  {c.completed && <span className={styles.completedBadge}>Completed</span>}
                </Link>
              ))}
            </div>
          ) : (
            <div className={styles.emptyState}>
              <p>You have not enrolled in any courses yet.</p>
              {summary?.skill_level == null && (
                <Link to="/assessment" className={styles.btnCta}>Take the Assessment</Link>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, unit = '' }) {
  return (
    <div className={styles.statCard}>
      <span className={styles.statValue}>{value}{unit}</span>
      <span className={styles.statLabel}>{label}</span>
    </div>
  );
}
