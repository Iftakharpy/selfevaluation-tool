import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import surveyAttemptService from '../services/surveyAttemptService';
import type { SurveyAttemptListItemFE } from '../types/surveyAttemptTypes';
import { useNotifier } from '../contexts/NotificationContext';
import { useAuth } from '../contexts/AuthContext';
// OutcomeCategoryEnumFE might be used if you decide to show an overall survey outcome later
// import { OutcomeCategoryEnumFE } from '../../types/surveyTypes'; 

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

  const calculateOverallScoreDisplay = (attempt: SurveyAttemptListItemFE): string => {
    if (!attempt.is_submitted) return "In Progress";

    const totalAchievedScore = Object.values(attempt.course_scores || {}).reduce((sum, score) => sum + score, 0);
    const maxOverallScore = attempt.max_overall_survey_score;

    if (maxOverallScore === undefined || maxOverallScore === null || maxOverallScore === 0) {
      return `${totalAchievedScore.toFixed(1)} (Max score N/A)`;
    }
    const percentage = (totalAchievedScore / maxOverallScore) * 100;
    return `${percentage.toFixed(0)}% (${totalAchievedScore.toFixed(1)} / ${maxOverallScore.toFixed(1)})`;
  };
  
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
        <div className="space-y-4">
          {attempts.map((attempt) => (
            <Link 
              key={attempt.id}
              to={attempt.is_submitted ? `/results/${attempt.id}` : `/survey/take/${attempt.survey_id}`} 
              className="block p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 ease-in-out"
            >
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center">
                <div className="flex-grow min-w-0"> {/* Added min-w-0 for better truncation */}
                  <p className="text-xl font-semibold text-indigo-700 truncate pr-2"> {/* Added pr-2 for spacing */}
                    {attempt.survey_title || `Survey (ID: ...${attempt.survey_id.slice(-6)})`}
                  </p>
                  {attempt.survey_description && (
                    <p className="text-xs text-gray-500 mt-1 truncate max-w-md">
                      {attempt.survey_description}
                    </p>
                  )}
                </div>
                <div className="mt-2 sm:mt-0 ml-0 sm:ml-2 flex-shrink-0">
                  <p className={`px-2.5 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    attempt.is_submitted ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {attempt.is_submitted ? 'Submitted' : 'In Progress'}
                  </p>
                </div>
              </div>
              <div className="mt-3 border-t pt-3">
                <div className="sm:flex sm:justify-between items-baseline text-sm">
                    <div className="space-y-1 sm:space-y-0 sm:flex sm:flex-wrap sm:gap-x-6 sm:gap-y-1"> {/* Use gap for spacing */}
                        <p className="flex items-center text-gray-500">
                          <svg className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                            <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                          </svg>
                          Started: {new Date(attempt.started_at).toLocaleDateString()}
                        </p>
                        {attempt.is_submitted && attempt.submitted_at && (
                          <p className="flex items-center text-gray-500">
                             <svg className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                               <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                             </svg>
                             Submitted: {new Date(attempt.submitted_at).toLocaleDateString()}
                          </p>
                        )}
                        <p className="flex items-center text-gray-500">
                            <svg className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 2a8 8 0 100 16 8 8 0 000-16zm0 14a6 6 0 110-12 6 6 0 010 12zM9 9a1 1 0 011-1h.01a1 1 0 110 2H10a1 1 0 01-1-1zm.01-3a1 1 0 011.98 0l-.01.01a1 1 0 01-1.96 0l-.01-.01z" clipRule="evenodd" /></svg>
                            Survey ID: <span className="ml-1 font-mono text-xs">{attempt.survey_id}</span>
                        </p>
                    </div>
                    {attempt.is_submitted && (
                    <p className="mt-2 sm:mt-0 text-gray-700">
                        Overall Score: <span className="font-semibold text-indigo-600">{calculateOverallScoreDisplay(attempt)}</span>
                    </p>
                    )}
                </div>
                <div className="mt-3 text-sm text-indigo-700 font-medium text-right">
                    {attempt.is_submitted ? 'View Full Results' : 'Continue Survey'}
                    <span aria-hidden="true"> →</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};

export default MyAttemptsPage;