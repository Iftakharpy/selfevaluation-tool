// File: ui/src/pages/SurveyAttemptsOverviewPage.tsx
import React, { useEffect, useState, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import surveyService from '../services/surveyService';
import surveyAttemptService from '../services/surveyAttemptService';
import type { SurveyFE } from '../types/surveyTypes';
import type { SurveyAttemptListItemFE } from '../types/surveyAttemptTypes';
import ResourceTable from '../components/management/ResourceTable';
import type { Column } from '../components/management/ResourceTable';
import Button from '../components/forms/Button';
import { useNotifier } from '../contexts/NotificationContext';
import { useAuth } from '../contexts/AuthContext';

const SurveyAttemptsOverviewPage: React.FC = () => {
  const { surveyId } = useParams<{ surveyId: string }>();
  const navigate = useNavigate();
  const { addNotification } = useNotifier();
  const { user } = useAuth();

  const [survey, setSurvey] = useState<SurveyFE | null>(null);
  const [attempts, setAttempts] = useState<SurveyAttemptListItemFE[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSurveyAndAttempts = useCallback(async () => {
    if (!surveyId || !user) return;
    setIsLoading(true);
    setError(null);
    try {
      const surveyDetails = await surveyService.getSurveyDetail(surveyId);
      setSurvey(surveyDetails);

      if (surveyDetails.created_by !== user.id) {
        addNotification("You are not authorized to view attempts for this survey.", "error");
        navigate("/surveys/manage");
        return;
      }

      const attemptsData = await surveyAttemptService.listAttemptsForSurvey(surveyId);
      setAttempts(attemptsData);

    } catch (err: any) {
      const msg = err.response?.data?.detail || "Failed to load survey attempts details.";
      setError(msg);
      addNotification(msg, 'error');
    } finally {
      setIsLoading(false);
    }
  }, [surveyId, user, addNotification, navigate]);

  useEffect(() => {
    fetchSurveyAndAttempts();
  }, [fetchSurveyAndAttempts]);

  const columns: Column<SurveyAttemptListItemFE>[] = [
    { 
      header: 'Student', 
      accessor: (item) => item.student_display_name || `Student ID: ${item.student_id.substring(0,8)}...`,
      className: 'font-medium text-gray-900' 
    },
    { 
      header: 'Submitted At', 
      accessor: (item) => item.submitted_at ? new Date(item.submitted_at).toLocaleString() : 'Not Submitted',
    },
    {
      header: 'Overall Score (%)',
      accessor: (item) => {
        if (!item.is_submitted) return 'N/A';
        const totalActualScore = Object.values(item.course_scores).reduce((sum, score) => sum + score, 0);
        const totalMaxScore = item.max_overall_survey_score;
        if (totalMaxScore === undefined || totalMaxScore === null || totalMaxScore === 0) return 'N/A (max unknown)';
        const percentage = (totalActualScore / totalMaxScore) * 100;
        return `${percentage.toFixed(0)}% (${totalActualScore.toFixed(1)} / ${totalMaxScore.toFixed(1)})`;
      },
      className: 'text-center'
    },
    {
      header: 'Actions',
      accessor: (item) => (
        item.is_submitted ? (
          <Link to={`/results/${item.id}`}>
            <Button variant="ghost" size="sm">View Full Result</Button>
          </Link>
        ) : (
          <span className="text-xs text-gray-500">In Progress</span>
        )
      ),
      className: 'text-right'
    }
  ];

  if (isLoading) {
    return <div className="text-center py-10">Loading survey attempts...</div>;
  }

  if (error) {
    return <div className="text-center py-10 text-red-600">Error: {error}</div>;
  }

  if (!survey) {
    return <div className="text-center py-10 text-gray-600">Survey details could not be loaded.</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <Button variant="ghost" onClick={() => navigate('/surveys/manage')} className="mb-4 text-sm">
            ← Back to My Surveys
        </Button>
        <h1 className="text-3xl font-bold text-gray-800">Student Attempts for: {survey.title}</h1>
        {survey.description && <p className="text-sm text-gray-500 mt-1">{survey.description}</p>}
      </div>

      {attempts.length === 0 ? (
        <p className="text-gray-600 text-center py-10 bg-white shadow rounded-md">
          No students have submitted this survey yet.
        </p>
      ) : (
        <ResourceTable<SurveyAttemptListItemFE>
          data={attempts}
          columns={columns}
          isLoading={isLoading} 
        />
      )}
    </div>
  );
};

export default SurveyAttemptsOverviewPage;