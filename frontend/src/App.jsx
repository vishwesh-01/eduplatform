/**
 * App.jsx — Root component with React Router v6 setup.
 *
 * Route hierarchy:
 *   /                        → LandingPage (public)
 *   /login                   → LoginPage (public)
 *   /register                → RegisterPage (public)
 *   /onboarding              → OnboardingPage (protected)
 *   /assessment              → AssessmentPage (protected)
 *   /assessment/results      → AssessmentResultsPage (protected)
 *   /dashboard               → DashboardPage (protected)
 *   /courses/:courseId        → CoursePage (protected)
 *   /progress                → ProgressPage (protected)
 *   /certificates            → CertificatesPage (protected)
 *   /profile                 → ProfilePage (protected)
 *   /admin                   → AdminPage (admin only)
 */

import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { useAuth } from './hooks/useAuth';

// Page components
import LandingPage          from './pages/Landing/LandingPage';
import LoginPage            from './pages/Login/LoginPage';
import RegisterPage         from './pages/Register/RegisterPage';
import OnboardingPage       from './pages/Onboarding/OnboardingPage';
import AssessmentPage       from './pages/Assessment/AssessmentPage';
import AssessmentResultsPage from './pages/Assessment/AssessmentResultsPage';
import DashboardPage        from './pages/Dashboard/DashboardPage';
import CoursePage           from './pages/Course/CoursePage';
import ProgressPage         from './pages/Progress/ProgressPage';
import CertificatesPage     from './pages/Certificates/CertificatesPage';
import ProfilePage          from './pages/Profile/ProfilePage';
import AdminPage            from './pages/Admin/AdminPage';

// Layout
import Navbar from './components/layout/Navbar';

/**
 * ProtectedRoute — Wraps routes that require authentication.
 * Redirects unauthenticated users to /login.
 */
function ProtectedRoute({ children }) {
  const { user, isLoading } = useAuth();
  if (isLoading) return <div style={{ padding: '2rem', textAlign: 'center' }}>Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

/**
 * AdminRoute — Wraps routes that require the 'admin' role.
 * Redirects non-admin authenticated users to /dashboard.
 */
function AdminRoute({ children }) {
  const { user, isLoading } = useAuth();
  if (isLoading) return <div style={{ padding: '2rem', textAlign: 'center' }}>Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (!user.roles || !user.roles.includes('admin')) return <Navigate to="/dashboard" replace />;
  return children;
}

/**
 * AppRoutes — Defined inside AuthProvider so useAuth() is available.
 */
function AppRoutes() {
  return (
    <>
      <Navbar />
      <main style={{ minHeight: 'calc(100vh - 64px)' }}>
        <Routes>
          {/* Public routes */}
          <Route path="/"         element={<LandingPage />} />
          <Route path="/login"    element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected learner routes */}
          <Route path="/onboarding"          element={<ProtectedRoute><OnboardingPage /></ProtectedRoute>} />
          <Route path="/assessment"          element={<ProtectedRoute><AssessmentPage /></ProtectedRoute>} />
          <Route path="/assessment/results"  element={<ProtectedRoute><AssessmentResultsPage /></ProtectedRoute>} />
          <Route path="/dashboard"           element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/courses/:courseId"   element={<ProtectedRoute><CoursePage /></ProtectedRoute>} />
          <Route path="/progress"            element={<ProtectedRoute><ProgressPage /></ProtectedRoute>} />
          <Route path="/certificates"        element={<ProtectedRoute><CertificatesPage /></ProtectedRoute>} />
          <Route path="/profile"             element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />

          {/* Admin-only route */}
          <Route path="/admin" element={<AdminRoute><AdminPage /></AdminRoute>} />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
