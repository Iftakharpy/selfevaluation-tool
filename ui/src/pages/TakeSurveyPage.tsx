// ui/src/pages/TakeSurveyPage.tsx
import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import surveyAttemptService from '../services/surveyAttemptService';
import surveyService from '../services/surveyService';
import type { SurveyForTakingFE, SurveyQuestionDetailFE } from '../types/surveyTypes';
import type { StudentAnswerPayloadFE } from '../types/surveyAttemptTypes';
import QuestionDisplay from '../components/questions/QuestionDisplay';
import Button from '../components/forms/Button';
import { useNotifier } from '../contexts/NotificationContext';
import { useAuth } from '../contexts/AuthContext';


interface AnswersState {
  [qcaId: string]: StudentAnswerPayloadFE;
}

const TakeSurveyPage: React.FC = () => {
  const { surveyId } = useParams<{ surveyId: string }>();
  const navigate = useNavigate();
  const { addNotification } = useNotifier();
  const { user } = useAuth();

  const [survey, setSurvey] = useState<SurveyForTakingFE | null>(null);
  const [questions, setQuestions] = useState<SurveyQuestionDetailFE[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<AnswersState>({});
  const [attemptId, setAttemptId] = useState<string | null>(null);
  
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const initialized = useRef(false);

  useEffect(() => {
    if (!surveyId || !user) return;
    if (initialized.current) return;
    initialized.current = true;

    const initializeSurvey = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const surveyDetails = await surveyService.getSurveyDetail(surveyId);
        setSurvey(surveyDetails);

        const attemptData = await surveyAttemptService.startSurveyAttempt(surveyId);
        setAttemptId(attemptData.attempt_id);
        setQuestions(attemptData.questions || []); 
        
        const initialAnswers: AnswersState = {};
        (attemptData.questions || []).forEach(q => {
            initialAnswers[q.qca_id] = {
                qca_id: q.qca_id,
                question_id: q.question_id,
                answer_value: undefined, 
            };
        });
        setAnswers(initialAnswers);

      } catch (err: any) {
        const msg = err.response?.data?.detail || "Failed to load survey or start attempt.";
        setError(msg);
        addNotification(msg, 'error');
        if (msg.includes("Published survey not found")) {
             navigate('/surveys');
        } else {
            navigate(-1); 
        }
      } finally {
        setIsLoading(false);
      }
    };
    initializeSurvey();
  }, [surveyId, user, navigate, addNotification]);

  const handleAnswerChange = useCallback((
    questionId: string, 
    qcaId: string, 
    _courseId: string, 
    answerValue: any
  ) => {
    setAnswers(prev => ({
      ...prev,
      [qcaId]: {
        qca_id: qcaId,
        question_id: questionId,
        answer_value: answerValue,
      }
    }));
  }, []);

  const goToNextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    }
  };

  const goToPreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1); // CORRECTED
    }
  };

  const handleSubmitSurvey = async () => {
    if (!attemptId) {
      addNotification("Attempt ID is missing. Cannot submit.", 'error');
      return;
    }
    if (Object.values(answers).some(ans => ans.answer_value === undefined || ans.answer_value === null || (typeof ans.answer_value === 'string' && ans.answer_value.trim() === ''))) {
      if (!window.confirm("You have unanswered questions. Are you sure you want to submit?")) {
        return;
      }
    }

    setIsSubmitting(true);
    setError(null);
    try {
      const answersToSubmit = Object.values(answers).filter(ans => ans.answer_value !== undefined);
      if (answersToSubmit.length > 0) {
        await surveyAttemptService.submitAnswers(attemptId, answersToSubmit);
      }

      const result = await surveyAttemptService.submitSurvey(attemptId);
      addNotification("Survey submitted successfully!", 'success');
      navigate(`/results/${result.id}`);
    } catch (err: any) {
      const msg = err.response?.data?.detail || "Failed to submit survey.";
      setError(msg);
      addNotification(msg, 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return <div className="text-center py-10">Loading survey...</div>;
  }

  if (error) {
    return <div className="text-center py-10 text-red-600">Error: {error}</div>;
  }

  if (!survey || questions.length === 0) {
    return <div className="text-center py-10">Survey not found or has no questions.</div>;
  }

  const currentQuestion = questions[currentQuestionIndex];
  const currentQcaId = currentQuestion?.qca_id;


  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <div className="bg-white shadow-xl rounded-lg p-6 md:p-8">
        <h1 className="text-3xl font-bold text-indigo-700 mb-2">{survey.title}</h1>
        {survey.description && <p className="text-gray-600 mb-6">{survey.description}</p>}
        
        <div className="mb-6 p-4 border border-gray-200 rounded-lg">
          <p className="text-sm text-gray-500">
            Question {currentQuestionIndex + 1} of {questions.length}
          </p>
          {currentQuestion && currentQcaId && (
            <QuestionDisplay
              question={currentQuestion}
              currentAnswer={answers[currentQcaId]?.answer_value}
              onAnswerChange={handleAnswerChange}
              isSubmitted={isSubmitting} 
            />
          )}
        </div>

        <div className="flex justify-between items-center mt-8">
          <Button
            onClick={goToPreviousQuestion}
            disabled={currentQuestionIndex === 0 || isSubmitting}
            variant="secondary"
          >
            Previous
          </Button>
          
          {currentQuestionIndex === questions.length - 1 ? (
            <Button
              onClick={handleSubmitSurvey}
              isLoading={isSubmitting}
              variant="primary"
            >
              Submit Survey
            </Button>
          ) : (
            <Button
              onClick={goToNextQuestion}
              disabled={isSubmitting}
              variant="primary"
            >
              Next
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default TakeSurveyPage;