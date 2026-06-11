/**
 * LandingPage.jsx — Public marketing homepage.
 * Shows hero, feature cards, and CTAs.
 */

import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import styles from './LandingPage.module.css';

const FEATURES = [
  {
    title:       'Adaptive Assessment',
    description: 'Start with a diagnostic quiz that adapts to your skill level in real time.',
  },
  {
    title:       'Personalised Learning Path',
    description: 'AI generates a course roadmap tailored to your goal and current ability.',
  },
  {
    title:       'Video-First Content',
    description: 'Every module is paired with the most relevant YouTube tutorial for that topic.',
  },
  {
    title:       'Progress Tracking',
    description: 'Visual dashboards show exactly how far you have come and what is next.',
  },
  {
    title:       'Verified Certificates',
    description: 'Download a PDF certificate with a unique verification code when you complete a course.',
  },
  {
    title:       'Role-Based Access',
    description: 'Admins can manage learners and view AI-generated content versions.',
  },
];

export default function LandingPage() {
  const { user } = useAuth();

  return (
    <div className={styles.page}>
      {/* Hero */}
      <section className={styles.hero}>
        <div className={styles.heroContent}>
          <h1 className={styles.heroTitle}>
            Learn Smarter.<br />
            Track Progress.<br />
            Earn Certificates.
          </h1>
          <p className={styles.heroSubtitle}>
            An AI-powered education platform that adapts to your skill level and
            generates a personalised learning path — so you always know what to
            study next.
          </p>
          <div className={styles.heroCta}>
            {user ? (
              <Link to="/dashboard" className={styles.btnPrimary}>Go to Dashboard</Link>
            ) : (
              <>
                <Link to="/register" className={styles.btnPrimary}>Start Learning</Link>
                <Link to="/login"    className={styles.btnSecondary}>Sign In</Link>
              </>
            )}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className={styles.features}>
        <div className={styles.container}>
          <h2 className={styles.sectionTitle}>Everything you need to level up</h2>
          <div className={styles.grid}>
            {FEATURES.map((f) => (
              <div key={f.title} className={styles.card}>
                <h3 className={styles.cardTitle}>{f.title}</h3>
                <p className={styles.cardDesc}>{f.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Banner */}
      {!user && (
        <section className={styles.ctaBanner}>
          <div className={styles.container}>
            <h2>Ready to get started?</h2>
            <p>Create a free account and take your first diagnostic assessment in under two minutes.</p>
            <Link to="/register" className={styles.btnWhite}>Create Free Account</Link>
          </div>
        </section>
      )}
    </div>
  );
}
