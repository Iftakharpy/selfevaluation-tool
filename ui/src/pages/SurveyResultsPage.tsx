// File: ui/src/pages/SurveyResultsPage.tsx
import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom'; // Added useNavigate
import surveyAttemptService from '../services/surveyAttemptService';
import surveyService from '../services/surveyService'; // To fetch survey details for names
import type { SurveyAttemptResultFE } from '../types/surveyAttemptTypes';
import type { SurveyFE } from '../types/surveyTypes'; // To get survey title and course names
import type { Course } from '../types/courseTypes'; // For course names
import { useNotifier } from '../contexts/NotificationContext';
import { useAuth } from '../contexts/AuthContext';
import CourseResultCard from '../components/results/CourseResultCard';
import Button from '../components/forms/Button';

const SurveyResultsPage: React.FC = () => {
  const { attemptId } = useParams<{ attemptId: string }>();
  const navigate = useNavigate(); // For navigation
  const { addNotification } = useNotifier();
  const { user, isLoading: authLoading } = useAuth();

  const [results, setResults] = useState<SurveyAttemptResultFE | null>(null);
  const [surveyDetails, setSurveyDetails] = useState<SurveyFE | null>(null);
  const [courseNameMap, setCourseNameMap] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!attemptId || authLoading) return;
    if (!user) {
        setError("You must be logged in to view results.");
        setIsLoading(false);
        return;
    }

    const fetchResultsAndDetails = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const attemptData = await surveyAttemptService.getAttemptResult(attemptId);
        setResults(attemptData);

        if (attemptData) {
          const surveyData = await surveyService.getSurveyDetail(attemptData.survey_id);
          setSurveyDetails(surveyData);
          
          // Create a map of course IDs to names for easier lookup
          if (surveyData.course_ids && surveyData.course_ids.length > 0) {
            // Ideally, course details (name, code) would be part of SurveyFE if fetched with questions,
            // or we'd fetch them. For simplicity if not directly available, we'll make a call.
            // This assumes SurveyFE.questions might contain course_id which is less direct.
            // A better approach might be to iterate surveyData.course_ids and fetch each.
            // For now, let's assume we might need to fetch all courses and filter.
            const allCourses = await courseService.listCourses();
            const cNameMap: Record<string, string> = {};
            surveyData.course_ids.forEach(cId => {
                const foundCourse = allCourses.find(rc => rc.id === cId);
                cNameMap[cId] = foundCourse?.name || `Course ${cId.substring(0,6)}`;
            });
            setCourseNameMap(cNameMap);
          }
        }

      } catch (err: any) {
        const errorMessage = err.response?.data?.detail || "Failed to load survey results or related details.";
        setError(errorMessage);
        addNotification(errorMessage, 'error');
      } finally {
        setIsLoading(false);
      }
    };

    fetchResultsAndDetails();
  }, [attemptId, user, authLoading, addNotification]);

  const overallActualScore = results 
    ? Object.values(results.course_scores).reduce((sum, score) => sum + score, 0) 
    : 0;
  
  const overallMaxScore = results?.max_overall_survey_score;
  
  const overallPercentageScore = (overallMaxScore !== undefined && overallMaxScore !== null && overallMaxScore > 0)
    ? (overallActualScore / overallMaxScore) * 100
    : null;

  if (isLoading || authLoading) {
    return <div className="text-center py-10">Loading results...</div>;
  }

  if (error) {
    return <div className="text-center py-10 text-red-600">Error: {error}</div>;
  }

  if (!results) {
    return <div className="text-center py-10">No results found for this attempt.</div>;
  }
  
  const getCourseName = (courseId: string): string => {
    return courseNameMap[courseId] || `Course ID: ${courseId.substring(0,6)}...`;
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="bg-white shadow-xl rounded-lg p-6 md:p-8">
        <h1 className="text-3xl font-bold text-indigo-700 mb-1">
           Results for "{surveyDetails?.title || 'Survey'}"
        </h1>
         {results.student_display_name && user?.role === 'teacher' && (
            <p className="text-md text-gray-600 mb-1">Student: {results.student_display_name}</p>
        )}
        <p className="text-sm text-gray-500 mb-1">Attempt ID: {results.id}</p>
        <p className="text-sm text-gray-500 mb-6">
          Submitted on: {new Date(results.submitted_at || results.started_at).toLocaleString()}
        </p>

        <div className="bg-gray-100 p-4 rounded-lg mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Overall Survey Performance</h2>
          <div className="flex items-baseline space-x-2">
            <span className="text-gray-700 font-medium">Total Score:</span>
            <span className="text-3xl font-bold text-indigo-600">{overallActualScore.toFixed(1)}</span>
            {(overallMaxScore !== undefined && overallMaxScore !== null) && <span className="text-md text-gray-500"> / {overallMaxScore.toFixed(1)}</span>}
            {overallPercentageScore !== null && (
              <span className="text-2xl font-bold text-green-600 bg-green-100 px-3 py-1 rounded-md">
                ({overallPercentageScore.toFixed(0)}%)
              </span>
            )}
          </div>
        </div>

        {results.overall_survey_feedback && (
          <div className="bg-blue-50 border-l-4 border-blue-500 text-blue-700 p-4 mb-6" role="alert">
            <p className="font-bold">Overall Survey Feedback</p>
            <p>{results.overall_survey_feedback}</p>
          </div>
        )}

        <h2 className="text-2xl font-semibold text-gray-800 my-6 border-b pb-2">
          Results by Course
        </h2>
        {Object.keys(results.course_scores).length > 0 ? (
          Object.entries(results.course_scores).map(([courseId, score]) => (
            <CourseResultCard
              key={courseId}
              courseName={getCourseName(courseId)}
              score={score}
              maxScore={results.max_scores_per_course?.[courseId]}
              overallFeedback={results.course_feedback[courseId]}
              detailedFeedbackItems={results.detailed_feedback[courseId]}
              outcome={results.course_outcome_categorization[courseId]}
            />
          ))
        ) : (
          <p className="text-gray-600">No course-specific results available.</p>
        )}
        
        <div className="mt-8 text-center">
          <Button 
            variant="secondary" 
            onClick={() => {
              if (user?.role === 'teacher') {
                navigate(`/surveys/${results.survey_id}/attempts-overview`);
              } else {
                navigate("/my-attempts");
              }
            }}
          >
            {user?.role === 'teacher' ? "Back to Survey Attempts" : "Back to My Attempts"}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default SurveyResultsPage;