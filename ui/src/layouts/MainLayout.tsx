import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const MainLayout: React.FC = () => {
  const { user, isAuthenticated, logoutUser } = useAuth();
  return (
    <div className="min-h-screen flex flex-col">
      <nav className="bg-gray-800 text-white p-4 shadow-lg">
        <div className="container mx-auto flex justify-between items-center">
          <Link to="/" className="text-2xl font-bold hover:text-gray-300 transition-colors">
            Narsus Eval
          </Link>
          <div className="space-x-4">
            {isAuthenticated && user ? (
              <>
                <span className="hidden sm:inline">Hello, {user.display_name} ({user.role})</span>
                {user.role === 'teacher' && (
                  <Link to="/dashboard" className="hover:text-gray-300 transition-colors">Dashboard</Link>
                )}
                 <Link to="/surveys" className="hover:text-gray-300 transition-colors">Surveys</Link>
                {user.role === 'student' && (
                    <Link to="/my-attempts" className="hover:text-gray-300 transition-colors">My Attempts</Link>
                )}
                <button onClick={logoutUser} className="hover:text-gray-300 transition-colors">Logout</button>
              </>
            ) : (
              <>
                <Link to="/login" className="hover:text-gray-300 transition-colors">Login</Link>
                <Link to="/signup" className="hover:text-gray-300 transition-colors">Sign Up</Link>
              </>
            )}
          </div>
        </div>
      </nav>
      <main className="container mx-auto p-6 flex-grow">
        <Outlet /> {/* Nested routes will render here */}
      </main>
      <footer className="bg-gray-100 text-gray-600 text-center p-4 border-t">
        © {new Date().getFullYear()} Narsus Self-Evaluation Tool
      </footer>
    </div>
  );
};

export default MainLayout;