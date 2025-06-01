import React, { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useNotifier } from '../contexts/NotificationContext';
import Input from '../components/forms/Input';
import Button from '../components/forms/Button';

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState(''); // email
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const { loginUser, isAuthenticated, isLoading: authIsLoading } = useAuth();
  const navigate = useNavigate();
  const { addNotification } = useNotifier();

  useEffect(() => {
    if (!authIsLoading && isAuthenticated) {
      navigate('/', { replace: true });
    }
  }, [isAuthenticated, authIsLoading, navigate]);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await loginUser({ username, password });
      addNotification('Logged in successfully!', 'success'); // Example success
      navigate('/', { replace: true });
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Login failed. Please try again.';
      setError(errorMessage); // Local form error
      addNotification(errorMessage, 'error'); // Global notification
    } finally {
      setIsSubmitting(false);
    }
  };

  if (authIsLoading || (!authIsLoading && isAuthenticated)) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <p className="text-xl text-gray-700">Loading...</p>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-xl shadow-lg">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to your account
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
              <strong className="font-bold">Error: </strong>
              <span className="block sm:inline">{error}</span>
            </div>
          )}
          
          <Input
            id="email-address"
            name="email"
            type="email"
            autoComplete="email"
            required
            placeholder="Email address"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={isSubmitting}
            label="Email address"
            labelClassName="sr-only" // Hide label visually but keep for accessibility
            inputClassName="rounded-t-md" // Adjust for stacked inputs
            containerClassName="mb-0"
          />
          <Input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={isSubmitting}
            label="Password"
            labelClassName="sr-only"
            inputClassName="rounded-b-md"
            containerClassName="mb-0 -mt-px" // Negative margin to stack borders
          />
          
          <Button
            type="submit"
            isLoading={isSubmitting}
            fullWidth
            className="mt-6"
          >
            Sign in
          </Button>
        </form>
        <div className="text-sm text-center">
          <p>
            Don't have an account?{' '}
            <Link to="/signup" className="font-medium text-indigo-600 hover:text-indigo-500">
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;