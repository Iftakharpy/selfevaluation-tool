// ui/src/App.tsx
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';

// Layouts
import MainLayout from './layouts/MainLayout';

// Router
import ProtectedRoute from './router/ProjectedRoute';

// Pages
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage'; 
import SignupPage from './pages/SignupPage'; 
import TeacherDashboardPage from './pages/TeacherDashboardPage';
import SurveyListPage from './pages/SurveyListPage';
import TakeSurveyPage from './pages/TakeSurveyPage';      
import MyAttemptsPage from './pages/MyAttemptsPage';      
import SurveyResultsPage from './pages/SurveyResultsPage';
// Import other page components as you create them
// import CoursesPage from './pages/CoursesPage';
// import QuestionsPage from './pages/QuestionsPage';


function App() {
  const { isLoading: isAuthLoading } = useAuth();

  if (isAuthLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <p className="text-xl text-gray-700">Initializing Application...</p>
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      
      <Route element={<MainLayout />}>
        <Route 
          path="/" 
          element={
            <ProtectedRoute>
              <HomePage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/surveys" 
          element={
            <ProtectedRoute>
              <SurveyListPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/my-attempts" 
          element={
            <ProtectedRoute allowedRoles={['student']}>
              <MyAttemptsPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/survey/take/:surveyId" 
          element={
            <ProtectedRoute allowedRoles={['student']}>
              <TakeSurveyPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/results/:attemptId" 
          element={
            <ProtectedRoute>
              <SurveyResultsPage />
            </ProtectedRoute>
          } 
        />
        
        {/* Teacher-specific routes */}
        <Route 
          path="/dashboard" 
          element={
            <ProtectedRoute allowedRoles={['teacher']}>
              <TeacherDashboardPage />
            </ProtectedRoute>
          } 
        />
        {/* <Route 
          path="/courses" 
          element={
            <ProtectedRoute allowedRoles={['teacher']}>
              <CoursesPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/questions" 
          element={
            <ProtectedRoute allowedRoles={['teacher']}>
              <QuestionsPage />
            </ProtectedRoute>
          } 
        /> */}
      </Route>
      
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;