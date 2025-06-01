import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import surveyAttemptService from '../services/surveyAttemptService';
import type { SurveyAttemptListItemFE } from '../types/surveyAttemptTypes';
import { useNotifier } from '../contexts/NotificationContext';
import { useAuth } from '../contexts/AuthContext';
// You might need a surveyService to fetch survey titles if not included in attempt data
// import surveyService from '../services/surveyService';

const MyAttemptsPage: React.FC = () => {
  const [attempts, setAttempts] = useState<SurveyAttemptListItemFE[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { addNotification } = useNotifier();
  const { user } = useAuth();

  useEffect(() => {
    if (!user) return;

    const fetchAttempts = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await surveyAttemptService.getMyAttempts();
        // TODO: If survey titles are not part of SurveyAttemptListItemFE from backend,
        // you might need to fetch them here by iterating through `data` and calling surveyService.getSurveyDetail(attempt.survey_id)
        // This can lead to multiple API calls, so ideally backend includes titles.
        setAttempts(data);
      } catch (err: any) {
        const errorMessage = err.response?.data?.detail || "Failed to load your survey attempts.";
        setError(errorMessage);
        addNotification(errorMessage, 'error');
      } finally {
        setIsLoading(false);
      }
    };

    fetchAttempts();
  }, [user, addNotification]);

  if (isLoading) {
    return <div className="text-center py-10">Loading your attempts...</div>;
  }

  if (error) {
    return <div className="text-center py-10 text-red-600">Error: {error}</div>;
  }

  return (
    <div className="container mx-auto px-4">
      <h1 className="text-3xl font-bold text-gray-800 my-6">My Survey Attempts</h1>
      {attempts.length === 0 ? (
        <p className="text-gray-600 text-center py-10">You have not attempted any surveys yet.</p>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul role="list" className="divide-y divide-gray-200">
            {attempts.map((attempt) => (
              <li key={attempt.id}>
                <Link 
                  to={attempt.is_submitted ? `/results/${attempt.id}` : `/survey/take/${attempt.survey_id}`} 
                  className="block hover:bg-gray-50"
                >
                  <div className="px-4 py-4 sm:px-6">
                    <div className="flex items-center justify-between">
                      <p className="text-lg font-medium text-indigo-600 truncate">
                        {attempt.survey_title || `Survey ID: ${attempt.survey_id}`} {/* Display title if available */}
                      </p>
                      <div className="ml-2 flex-shrink-0 flex">
                        <p className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          attempt.is_submitted ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {attempt.is_submitted ? 'Submitted' : 'In Progress'}
                        </p>
                      </div>
                    </div>
                    <div className="mt-2 sm:flex sm:justify-between">
                      <div className="sm:flex">
                        <p className="flex items-center text-sm text-gray-500">
                          Started: {new Date(attempt.started_at).toLocaleString()}
                        </p>
                        {attempt.is_submitted && attempt.submitted_at && (
                           <p className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0 sm:ml-6">
                             Submitted: {new Date(attempt.submitted_at).toLocaleString()}
                           </p>
                        )}
                      </div>
                      <div className="mt-2 flex items-center text-sm text-indigo-600 sm:mt-0">
                        {attempt.is_submitted ? 'View Results' : 'Continue Survey'}
                        {/* Arrow Icon */}
                        <svg className="ml-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path></svg>
                      </div>
                    </div>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default MyAttemptsPage;
