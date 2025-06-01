import React, { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useNotifier } from '../contexts/NotificationContext';
import type { UserCreateData } from '../types/authTypes';
import Input from '../components/forms/Input';
import Select from '../components/forms/Select';
import Button from '../components/forms/Button';

const SignupPage: React.FC = () => {
  const [displayName, setDisplayName] = useState('');
  const [username, setUsername] = useState(''); // email
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState<'student' | 'teacher'>('student');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { signupUser, isAuthenticated, isLoading: authIsLoading } = useAuth();
  const { addNotification } = useNotifier();
  const navigate = useNavigate();

  useEffect(() => {
    if (!authIsLoading && isAuthenticated) {
      navigate('/', { replace: true });
    }
  }, [isAuthenticated, authIsLoading, navigate]);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    if (password.length < 6) {
        setError('Password must be at least 6 characters long.');
        return;
    }

    setIsSubmitting(true);
    const userData: UserCreateData = {
      display_name: displayName,
      username,
      password,
      role,
    };

    try {
      await signupUser(userData);
      addNotification('Account created successfully! Please log in.', 'success');
      navigate('/', { replace: true });
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Signup failed. Please try again.';
      setError(errorMessage);
      addNotification(errorMessage, 'error');
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

  const roleOptions = [
    { value: 'student', label: 'Student' },
    { value: 'teacher', label: 'Teacher' },
  ];

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-xl shadow-lg">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Create your account
          </h2>
        </div>
        <form className="mt-8 space-y-3" onSubmit={handleSubmit}> {/* Reduced space-y for tighter form */}
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
              <strong className="font-bold">Error: </strong>
              <span className="block sm:inline">{error}</span>
            </div>
          )}
          
          <Input
            label="Display Name"
            id="display-name"
            name="displayName"
            type="text"
            autoComplete="name"
            required
            placeholder="Your full name"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            disabled={isSubmitting}
          />
          <Input
            label="Email address"
            id="email-address"
            name="email"
            type="email"
            autoComplete="email"
            required
            placeholder="you@example.com"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={isSubmitting}
          />
          <Input
            label="Password"
            id="password"
            name="password"
            type="password"
            autoComplete="new-password"
            required
            placeholder="Min. 6 characters"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={isSubmitting}
          />
          <Input
            label="Confirm Password"
            id="confirm-password"
            name="confirmPassword"
            type="password"
            autoComplete="new-password"
            required
            placeholder="Re-enter password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            disabled={isSubmitting}
          />
          <Select
            label="Your Role"
            id="role"
            name="role"
            required
            options={roleOptions}
            value={role}
            onChange={(e) => setRole(e.target.value as 'student' | 'teacher')}
            disabled={isSubmitting}
          />
          
          <Button
            type="submit"
            isLoading={isSubmitting}
            fullWidth
            className="mt-5" // Added top margin
          >
            Sign up
          </Button>
        </form>
        <div className="text-sm text-center">
          <p>
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-indigo-600 hover:text-indigo-500">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default SignupPage;
