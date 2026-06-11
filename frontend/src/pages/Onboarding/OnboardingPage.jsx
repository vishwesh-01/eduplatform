/**
 * OnboardingPage.jsx — Let the learner choose their learning goal.
 * Fetches goals from the API and navigates to /assessment on selection.
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getGoals, selectGoal } from '../../api/courses';
import { useAuth } from '../../hooks/useAuth';
import styles from './OnboardingPage.module.css';

export default function OnboardingPage() {
  const { user, setUser } = useAuth();
  const navigate = useNavigate();

  const [goals,      setGoals]      = useState([]);
  const [selected,   setSelected]   = useState(null);
  const [isLoading,  setIsLoading]  = useState(true);
  const [isSaving,   setIsSaving]   = useState(false);
  const [error,      setError]      = useState('');

  // If user already has a goal, skip onboarding
  useEffect(() => {
    if (user?.goal_id) { navigate('/dashboard'); return; }
    getGoals()
      .then(res => setGoals(res.data.data.goals || []))
      .catch(() => setError('Failed to load learning goals. Please refresh.'))
      .finally(() => setIsLoading(false));
  }, [user, navigate]);

  const handleContinue = async () => {
    if (!selected) return;
    setIsSaving(true);
    try {
      await selectGoal(selected);
      setUser({ ...user, goal_id: selected });
      navigate('/assessment');
    } catch {
      setError('Failed to save your selection. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) return <div className={styles.center}>Loading goals...</div>;

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>What do you want to learn?</h1>
        <p className={styles.subtitle}>
          Choose your learning goal. We will use it to personalise your assessment and course recommendations.
        </p>
      </div>

      {error && <p className={styles.error}>{error}</p>}

      <div className={styles.grid}>
        {goals.map(goal => (
          <button
            key={goal.id}
            className={`${styles.goalCard} ${selected === goal.id ? styles.selected : ''}`}
            onClick={() => setSelected(goal.id)}
            type="button"
          >
            <span className={styles.goalName}>{goal.name}</span>
            {goal.description && (
              <span className={styles.goalDesc}>{goal.description}</span>
            )}
          </button>
        ))}
      </div>

      <div className={styles.actions}>
        <button
          className={styles.btnContinue}
          onClick={handleContinue}
          disabled={!selected || isSaving}
        >
          {isSaving ? 'Saving...' : 'Continue to Assessment'}
        </button>
      </div>
    </div>
  );
}
