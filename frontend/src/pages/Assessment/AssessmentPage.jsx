/**
 * AssessmentPage.jsx — Adaptive diagnostic quiz interface.
 * Starts a session on mount, presents one question at a time,
 * and navigates to /assessment/results on completion.
 */

import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getSession, startSession, submitAnswer } from '../../api/assessment';
import styles from './AssessmentPage.module.css';

const MAX_QUESTIONS = 15;
const SESSION_KEY   = 'edu_quiz_session_id';

export default function AssessmentPage() {
  const navigate = useNavigate();

  const [session,    setSession]    = useState(null);
  const [question,   setQuestion]   = useState(null);
  const [selected,   setSelected]   = useState(null);
  const [isLoading,  setIsLoading]  = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error,      setError]      = useState('');
  const didInit = useRef(false);

  /* On mount: resume existing session OR start a new one */
  useEffect(() => {
    if (didInit.current) return;
    didInit.current = true;

    const savedId = sessionStorage.getItem(SESSION_KEY);
    if (savedId) {
      getSession(savedId)
        .then(res => {
          const s = res.data.data.session;
          if (s.status === 'in_progress') {
            setSession(s);
            /* Session resumed — first question must be re-fetched via start */
          } else {
            sessionStorage.removeItem(SESSION_KEY);
            _start();
          }
        })
        .catch(() => _start());
    } else {
      _start();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const _start = () => {
    setIsLoading(true);
    startSession()
      .then(res => {
        const { session: s, question: q } = res.data.data;
        setSession(s);
        setQuestion(q);
        sessionStorage.setItem(SESSION_KEY, s.id);
      })
      .catch(err => {
        const code = err.response?.data?.error?.code;
        if (code === 'NO_GOAL') {
          setError('Please complete onboarding and select a learning goal first.');
        } else {
          setError(err.response?.data?.error?.message || 'Failed to start assessment. Please try again.');
        }
      })
      .finally(() => setIsLoading(false));
  };

  const handleSubmit = async () => {
    if (selected === null || !session || !question) return;
    setIsSubmitting(true);
    try {
      const res = await submitAnswer(session.id, question.id, selected);
      const result = res.data.data;

      if (result.status === 'completed') {
        sessionStorage.removeItem(SESSION_KEY);
        /* Store skill level for results page */
        sessionStorage.setItem('edu_skill_level', result.skill_level);
        navigate('/assessment/results');
      } else {
        setSession(result.session);
        setQuestion(result.next_question);
        setSelected(null);
      }
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to submit answer.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) return <div className={styles.center}>Preparing your assessment...</div>;

  if (error) return (
    <div className={styles.center}>
      <p className={styles.errorMsg}>{error}</p>
      <button className={styles.btnRetry} onClick={() => { setError(''); _start(); }}>
        Try Again
      </button>
    </div>
  );

  if (!question) return <div className={styles.center}>Loading question...</div>;

  const questionNum = (session?.current_question_number || 0) + 1;
  const progress    = Math.round((questionNum / MAX_QUESTIONS) * 100);

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        {/* Progress bar */}
        <div className={styles.progressRow}>
          <span className={styles.progressLabel}>
            Question {questionNum} of {MAX_QUESTIONS}
          </span>
          <span className={styles.difficultyLabel}>
            Level {session?.current_difficulty}/5
          </span>
        </div>
        <div className={styles.progressBar}>
          <div className={styles.progressFill} style={{ width: `${progress}%` }} />
        </div>

        {/* Question */}
        <p className={styles.questionText}>{question.question_text}</p>

        {/* Options */}
        <div className={styles.options}>
          {(question.options || []).map((opt, idx) => (
            <button
              key={idx}
              className={`${styles.optionBtn} ${selected === idx ? styles.optionSelected : ''}`}
              onClick={() => setSelected(idx)}
              type="button"
            >
              <span className={styles.optionLetter}>{String.fromCharCode(65 + idx)}</span>
              {opt}
            </button>
          ))}
        </div>

        {/* Submit */}
        <button
          className={styles.btnSubmit}
          onClick={handleSubmit}
          disabled={selected === null || isSubmitting}
        >
          {isSubmitting ? 'Submitting...' : 'Submit Answer'}
        </button>
      </div>
    </div>
  );
}
