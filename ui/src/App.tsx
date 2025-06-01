// ui/src/App.tsx
import { Routes, Route, Navigate, Outlet, Link } from 'react-router-dom';
import type { JSX } from 'react';
import { useAuth } from './contexts/AuthContext';

// Placeholder Pages (create these files in src/pages/ with basic content)
const HomePage = () => {
  const { user, logoutUser } = useAuth();
  return (
    <div>
      <h1 className="text-3xl font-bold">Welcome to Narsus, {user?.display_name}!</h1>
      <p>Your role: {user?.role}</p>
      {user?.role === 'teacher' && <Link to="/dashboard" className="text-blue-500 hover:underline">Teacher Dashboard</Link>}
      <button onClick={logoutUser} className="mt-4 p-2 bg-red-500 text-white rounded">Logout</button>
    </div>
  );
};
const LoginPage = () => <h2>Login Page</h2>; // We'll implement the form later
const SignupPage = () => <h2>Signup Page</h2>; // We'll implement the form later
const TeacherDashboardPage = () => <h2>Teacher Dashboard</h2>;
const SurveyListPage = () => <h2>Survey List</h2>;


// Basic Layout Component (can be moved to src/layouts/MainLayout.tsx)
const MainLayout = () => {
  const { user, isAuthenticated, logoutUser } = useAuth();
  return (
    <div className="min-h-screen flex flex-col">
      <nav className="bg-gray-800 text-white p-4">
        <div className="container mx-auto flex justify-between items-center">
          <Link to="/" className="text-xl font-bold">Narsus Eval</Link>
          <div>
            {isAuthenticated && user ? (
              <>
                <span className="mr-4">Hello, {user.display_name} ({user.role})</span>
                {user.role === 'teacher' && <Link to="/dashboard" className="mr-4 hover:text-gray-300">Dashboard</Link>}
                <Link to="/surveys" className="mr-4 hover:text-gray-300">Surveys</Link>
                <button onClick={logoutUser} className="hover:text-gray-300">Logout</button>
              </>
            ) : (
              <>
                <Link to="/login" className="mr-4 hover:text-gray-300">Login</Link>
                <Link to="/signup" className="hover:text-gray-300">Sign Up</Link>
              </>
            )}
          </div>
        </div>
      </nav>
      <main className="container mx-auto p-4 flex-grow">
        <Outlet /> {/* Nested routes will render here */}
      </main>
      <footer className="bg-gray-200 text-center p-4">
        © {new Date().getFullYear()} Narsus Self-Evaluation Tool
      </footer>
    </div>
  );
};


// Protected Route Component (can be moved to src/router/ProtectedRoute.tsx)
interface ProtectedRouteProps {
  children: JSX.Element;
  allowedRoles?: Array<'student' | 'teacher'>;
}
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
  const { user, isLoading, isAuthenticated } = useAuth();

  if (isLoading) {
    return <div className="flex items-center justify-center min-h-screen"><p>Loading authentication...</p></div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    // User is authenticated but doesn't have the required role
    // Redirect to a general page or an "Unauthorized" page
    return <Navigate to="/" replace />; 
  }

  return children;
};


function App() {
  const { isLoading: isAuthLoading } = useAuth();

  if (isAuthLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-xl">Initializing Application...</p>
        {/* You can add a more sophisticated loader/spinner here */}
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      
      <Route element={<MainLayout />}>
        <Route path="/" element={
          <ProtectedRoute>
            <HomePage />
          </ProtectedRoute>
        } />
        <Route path="/surveys" element={
          <ProtectedRoute>
            <SurveyListPage />
          </ProtectedRoute>
        } />
        {/* Example Teacher-only route */}
        <Route path="/dashboard" element={
          <ProtectedRoute allowedRoles={['teacher']}>
            <TeacherDashboardPage />
          </ProtectedRoute>
        } />
        {/* Add more routes here */}
      </Route>
      
      {/* Fallback for unknown routes */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;