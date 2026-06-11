/**
 * AssessmentResultsPage.jsx — Shows skill level score after the quiz,
 * with a label and link to view the generated learning path.
 */

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import styles from './AssessmentResultsPage.module.css';

function getLabel(score) {
  if (score >= 75) return { label: 'Advanced',     color: '#16a34a' };
  if (score >= 45) return { label: 'Intermediate', color: '#d97706' };
  return               { label: 'Beginner',      color: '#2563eb' };
}

export default function AssessmentResultsPage() {
  const [skillLevel, setSkillLevel] = useState(null);

  useEffect(() => {
    const stored = sessionStorage.getItem('edu_skill_level');
    if (stored !== null) {
      setSkillLevel(parseFloat(stored));
      sessionStorage.removeItem('edu_skill_level');
    }
  }, []);

  if (skillLevel === null) {
    return (
      <div className={styles.center}>
        <p>No results found. Please complete the assessment first.</p>
        <Link to="/assessment" className={styles.btnLink}>Take Assessment</Link>
      </div>
    );
  }

  const { label, color } = getLabel(skillLevel);
  const pct = Math.round(skillLevel);

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <h1 className={styles.title}>Assessment Complete</h1>
        <p className={styles.subtitle}>Here is your current skill level based on the adaptive quiz.</p>

        {/* Score circle */}
        <div className={styles.scoreCircle} style={{ borderColor: color }}>
          <span className={styles.scoreNum} style={{ color }}>{pct}</span>
          <span className={styles.scoreUnit}>/ 100</span>
        </div>

        <div className={styles.levelBadge} style={{ background: color }}>
          {label}
        </div>

        <p className={styles.description}>
          {label === 'Advanced' &&
            'Excellent work. Your learning path will focus on advanced topics and real-world projects.'}
          {label === 'Intermediate' &&
            'Good foundation. Your path will strengthen core concepts while introducing advanced material.'}
          {label === 'Beginner' &&
            'Welcome. Your path starts with fundamentals and builds up step by step.'}
        </p>

        <div className={styles.actions}>
          <Link to="/dashboard" className={styles.btnPrimary}>
            View My Learning Path
          </Link>
          <Link to="/assessment" className={styles.btnSecondary}>
            Retake Assessment
          </Link>
        </div>
      </div>
    </div>
  );
}
