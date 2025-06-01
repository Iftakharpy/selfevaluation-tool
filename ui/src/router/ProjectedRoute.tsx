import React from 'react';
import type { JSX } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: JSX.Element;
  allowedRoles?: Array<'student' | 'teacher'>;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
  const { user, isLoading, isAuthenticated } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-lg">Loading authentication status...</p>
        {/* Consider adding a spinner component here */}
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    // User is authenticated but doesn't have the required role
    // Redirect to a general page (e.g., home) or an "Unauthorized" page
    return <Navigate to="/" replace />; 
  }

  return children;
};

export default ProtectedRoute;