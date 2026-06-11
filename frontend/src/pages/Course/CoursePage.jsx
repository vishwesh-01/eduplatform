/**
 * CoursePage.jsx — Course detail with YouTube video player and module checklist.
 */

import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getCourse } from '../../api/courses';
import { completeModule } from '../../api/progress';
import styles from './CoursePage.module.css';

export default function CoursePage() {
  const { courseId } = useParams();

  const [course,       setCourse]       = useState(null);
  const [activeModule, setActiveModule] = useState(null);
  const [completed,    setCompleted]    = useState(new Set());
  const [isLoading,    setIsLoading]    = useState(true);
  const [error,        setError]        = useState('');

  useEffect(() => {
    getCourse(courseId)
      .then(res => {
        const c = res.data.data.course;
        setCourse(c);
        if (c.modules?.length) setActiveModule(c.modules[0]);
      })
      .catch(() => setError('Failed to load course. Please try again.'))
      .finally(() => setIsLoading(false));
  }, [courseId]);

  const handleModuleComplete = async (module) => {
    if (completed.has(module.id)) return;
    try {
      await completeModule(module.id);
      setCompleted(prev => new Set([...prev, module.id]));
    } catch {
      /* silently ignore — user can retry */
    }
  };

  if (isLoading) return <div className={styles.center}>Loading course...</div>;
  if (error)     return <div className={styles.center}>{error}</div>;
  if (!course)   return null;

  const totalModules    = course.modules?.length ?? 0;
  const completedCount  = completed.size;
  const progressPct     = totalModules > 0 ? Math.round((completedCount / totalModules) * 100) : 0;

  return (
    <div className={styles.page}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerInner}>
          <h1 className={styles.title}>{course.title}</h1>
          {course.instructor && (
            <p className={styles.instructor}>{course.instructor}</p>
          )}
          <div className={styles.progressRow}>
            <div className={styles.progressBar}>
              <div className={styles.progressFill} style={{ width: `${progressPct}%` }} />
            </div>
            <span className={styles.progressText}>{progressPct}% complete</span>
          </div>
        </div>
      </div>

      {/* Main layout */}
      <div className={styles.layout}>
        {/* Video player */}
        <div className={styles.videoSection}>
          {activeModule ? (
            <>
              <h2 className={styles.moduleTitle}>{activeModule.title}</h2>
              {activeModule.video_id ? (
                <div className={styles.videoWrapper}>
                  <iframe
                    src={`https://www.youtube.com/embed/${activeModule.video_id}`}
                    title={activeModule.video_title || activeModule.title}
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                    className={styles.iframe}
                  />
                </div>
              ) : (
                <div className={styles.videoUnavailable}>
                  Video currently unavailable
                </div>
              )}
              <button
                className={`${styles.btnComplete} ${completed.has(activeModule.id) ? styles.btnDone : ''}`}
                onClick={() => handleModuleComplete(activeModule)}
                disabled={completed.has(activeModule.id)}
              >
                {completed.has(activeModule.id) ? 'Module Completed' : 'Mark as Complete'}
              </button>
            </>
          ) : (
            <p className={styles.center}>Select a module to begin.</p>
          )}
        </div>

        {/* Module list */}
        <aside className={styles.sidebar}>
          <h3 className={styles.sidebarTitle}>Modules ({totalModules})</h3>
          <ul className={styles.moduleList}>
            {course.modules?.map((mod, idx) => (
              <li
                key={mod.id}
                className={`${styles.moduleItem}
                  ${activeModule?.id === mod.id ? styles.active : ''}
                  ${completed.has(mod.id) ? styles.done : ''}`}
                onClick={() => setActiveModule(mod)}
              >
                <span className={styles.moduleNum}>{idx + 1}</span>
                <span className={styles.moduleName}>{mod.title}</span>
                {completed.has(mod.id) && <span className={styles.checkmark}>&#10003;</span>}
              </li>
            ))}
          </ul>
        </aside>
      </div>
    </div>
  );
}
