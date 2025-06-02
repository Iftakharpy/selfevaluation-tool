import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Button from '../components/forms/Button'; // Assuming you want to use the new Button

const HomePage: React.FC = () => {
  const { user, logoutUser } = useAuth();

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="bg-white shadow-xl rounded-lg p-8 text-center">
        <h1 className="text-4xl font-bold text-indigo-600 mb-4">
          Welcome to Self-Evaluation Tool, {user?.display_name}!
        </h1>
        <p className="text-xl text-gray-700 mb-2">
          You are logged in as a: <span className="font-semibold text-indigo-500">{user?.role}</span>
        </p>
        <p className="text-gray-600 mb-8">
          This tool is designed to help you assess your skills and readiness for various courses.
        </p>

        <div className="space-y-4 md:space-y-0 md:space-x-4 flex flex-col md:flex-row justify-center items-center">
          {user?.role === 'teacher' && (
            <Link to="/dashboard">
              <Button variant="primary" className="w-full md:w-auto">
                Go to Teacher Dashboard
              </Button>
            </Link>
          )}
          {user?.role === 'student' && (
            <Link to="/surveys">
              <Button variant="primary" className="w-full md:w-auto">
                View Available Surveys
              </Button>
            </Link>
          )}
          <Link to="/surveys"> {/* General link, useful for both or if specific role actions aren't primary */}
            <Button variant="secondary" className="w-full md:w-auto">
              Browse All Surveys
            </Button>
          </Link>
        </div>

        <div className="mt-12 border-t pt-8">
          <Button onClick={logoutUser} variant="danger" className="w-full sm:w-auto">
            Logout
          </Button>
        </div>
      </div>
    </div>
  );
};

export default HomePage;