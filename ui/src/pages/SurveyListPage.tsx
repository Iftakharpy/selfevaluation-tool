import React, { useEffect, useState } from 'react';
import surveyService from '../services/surveyService';
import type { SurveySummaryListItemFE } from '../types/surveyTypes';
import SurveyCard from '../components/surveys/SurveyCard';
import { useNotifier } from '../contexts/NotificationContext';

const SurveyListPage: React.FC = () => {
  const [surveys, setSurveys] = useState<SurveySummaryListItemFE[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { addNotification } = useNotifier();

  useEffect(() => {
    const fetchSurveys = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await surveyService.listPublishedSurveys();
        setSurveys(data);
      } catch (err: any) {
        const errorMessage = err.response?.data?.detail || "Failed to load surveys.";
        setError(errorMessage);
        addNotification(errorMessage, 'error');
      } finally {
        setIsLoading(false);
      }
    };

    fetchSurveys();
  }, [addNotification]);

  if (isLoading) {
    return <div className="text-center py-10">Loading surveys...</div>;
  }

  if (error) {
    return <div className="text-center py-10 text-red-600">Error: {error}</div>;
  }

  return (
    <div className="container mx-auto px-4">
      <h1 className="text-3xl font-bold text-gray-800 my-6">Available Surveys</h1>
      {surveys.length === 0 ? (
        <p className="text-gray-600 text-center py-10">No surveys currently available.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {surveys.map(survey => (
            <SurveyCard key={survey.id} survey={survey} />
          ))}
        </div>
      )}
    </div>
  );
};

export default SurveyListPage;