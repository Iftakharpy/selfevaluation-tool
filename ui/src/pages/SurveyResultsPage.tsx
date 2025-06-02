import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import surveyAttemptService from '../services/surveyAttemptService';
import type { SurveyAttemptResultFE, StudentAnswerFE } from '../types/surveyAttemptTypes';
import { useNotifier } from '../contexts/NotificationContext';
import { useAuth } from '../contexts/AuthContext';
import CourseResultCard from '../components/results/CourseResultCard';
// You might need courseService to get course names from course_ids
// import courseService from '../services/courseService';
// import type { Course } from '../types/courseTypes'; // Assuming you'll create this

import Button from '../components/forms/Button';


const SurveyResultsPage: React.FC = () => {
  const { attemptId } = useParams<{ attemptId: string }>();
  const { addNotification } = useNotifier();
  const { user, isLoading: authLoading } = useAuth();

  const [results, setResults] = useState<SurveyAttemptResultFE | null>(null);
  // const [courseDetails, setCourseDetails] = useState<Record<string, Course>>({}); // For course names
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!attemptId || authLoading) return; // Wait for auth to load
    if (!user) { // Should be caught by ProtectedRoute, but good for robustness
        setError("You must be logged in to view results.");
        setIsLoading(false);
        return;
    }

    const fetchResults = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await surveyAttemptService.getAttemptResult(attemptId);
        setResults(data);
        
        // TODO: Fetch course names if not readily available
        // This is a common pattern: API returns IDs, UI fetches details.
        // Or, backend could populate course names in the SurveyAttemptResultFE structure.
        // if (data) {
        //   const courseIds = Object.keys(data.course_scores);
        //   const coursePromises = courseIds.map(id => courseService.getCourse(id));
        //   const coursesData = await Promise.all(coursePromises);
        //   const coursesMap = coursesData.reduce((acc, course) => {
        //     acc[course.id] = course;
        //     return acc;
        //   }, {} as Record<string, Course>);
        //   setCourseDetails(coursesMap);
        // }

      } catch (err: any) {
        const errorMessage = err.response?.data?.detail || "Failed to load survey results.";
        setError(errorMessage);
        addNotification(errorMessage, 'error');
      } finally {
        setIsLoading(false);
      }
    };

    fetchResults();
  }, [attemptId, user, authLoading, addNotification]);

  if (isLoading || authLoading) {
    return <div className="text-center py-10">Loading results...</div>;
  }

  if (error) {
    return <div className="text-center py-10 text-red-600">Error: {error}</div>;
  }

  if (!results) {
    return <div className="text-center py-10">No results found for this attempt.</div>;
  }

  // Dummy function to get course name - replace with actual data
  const getCourseName = (courseId: string): string => {
    // return courseDetails[courseId]?.name || `Course ${courseId.substring(0,6)}...`;
    return `Course ${courseId.substring(0,6)}...`; // Placeholder
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="bg-white shadow-xl rounded-lg p-6 md:p-8">
        <h1 className="text-3xl font-bold text-indigo-700 mb-4">Survey Results</h1>
        <p className="text-sm text-gray-500 mb-1">Attempt ID: {results.id}</p>
        <p className="text-sm text-gray-500 mb-6">
          Submitted on: {new Date(results.submitted_at || results.started_at).toLocaleString()}
        </p>

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
              overallFeedback={results.course_feedback[courseId]}
              detailedFeedbackItems={results.detailed_feedback[courseId]}
              outcome={results.course_outcome_categorization[courseId]}
            />
          ))
        ) : (
          <p className="text-gray-600">No course-specific results available.</p>
        )}
        
        {/* Optional: Display individual answers */}
        {/* <h2 className="text-2xl font-semibold text-gray-800 my-6 border-b pb-2">
          Your Answers
        </h2>
        {results.answers && results.answers.length > 0 ? (
          <ul className="space-y-4">
            {results.answers.map((answer: StudentAnswerFE) => (
              <li key={answer.id} className="p-3 bg-gray-50 rounded-md">
                <p className="text-sm font-medium text-gray-700">Question ID: {answer.question_id}</p>
                <p className="text-sm text-gray-500">Your Answer: {JSON.stringify(answer.answer_value)}</p>
                {answer.score_achieved !== null && typeof answer.score_achieved !== 'undefined' && (
                   <p className="text-sm text-gray-500">Score: {answer.score_achieved.toFixed(1)}</p>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-600">No individual answer details available.</p>
        )} */}

        <div className="mt-8 text-center">
          <Link to="/my-attempts">
            <Button variant="secondary">Back to My Attempts</Button>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default SurveyResultsPage;