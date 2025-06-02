// ui/src/pages/CourseDetailsPage.tsx
import React, { useEffect, useState, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import courseService from '../services/courseService';
import qcaService from '../services/qcaService';
import questionService from '../services/questionService';
import type { Course } from '../types/courseTypes';
// import type { QCA } from '../types/qcaTypes'; // QCA itself is not directly displayed, only its question_id is used
import type { QuestionListItemFE } from '../types/questionTypes';
import { useNotifier } from '../contexts/NotificationContext';
import Button from '../components/forms/Button';
import ResourceTable from '../components/management/ResourceTable'; // Import Column type
import type { Column } from '../components/management/ResourceTable'; // Import Column type


const CourseDetailsPage: React.FC = () => {
  const { courseId } = useParams<{ courseId: string }>();
  const navigate = useNavigate();
  const { addNotification } = useNotifier();

  const [course, setCourse] = useState<Course | null>(null);
  const [associatedQuestions, setAssociatedQuestions] = useState<QuestionListItemFE[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCourseDetailsAndQuestions = useCallback(async () => {
    if (!courseId) {
        setError("Course ID is missing.");
        setIsLoading(false);
        return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const courseData = await courseService.getCourse(courseId);
      setCourse(courseData);

      const qcas = await qcaService.listQCAs({ course_id: courseId });
      if (qcas.length > 0) {
        const questionPromises = qcas.map(qca => questionService.getQuestion(qca.question_id));
        const questionsData = await Promise.all(questionPromises);
        
        setAssociatedQuestions(questionsData.map(q => ({
          id: q.id || `temp-id-${Math.random()}`, // Fallback ID if undefined, ensure ResourceTable key works
          title: q.title,
          answer_type: q.answer_type,
          details: q.details
        })));
      } else {
        setAssociatedQuestions([]);
      }

    } catch (err: any) {
      const msg = err.response?.data?.detail || `Failed to load details for course ${courseId}.`;
      setError(msg);
      addNotification(msg, 'error');
    } finally {
      setIsLoading(false);
    }
  }, [courseId, addNotification]);

  useEffect(() => {
    fetchCourseDetailsAndQuestions();
  }, [fetchCourseDetailsAndQuestions]);

  const questionColumns: Column<QuestionListItemFE>[] = [
    { header: 'Question Title', accessor: 'title', className: 'font-medium text-gray-900' },
    { header: 'Type', accessor: 'answer_type', className: 'capitalize' },
    { header: 'Details', accessor: (item) => item.details ? (item.details.length > 70 ? `${item.details.substring(0, 67)}...` : item.details) : '-', className: 'text-sm text-gray-500 max-w-xs truncate' },
    {
      header: 'Actions',
      accessor: (question) => (
        // Link to QuestionsPage, passing question.id to pre-fill the edit form
        <Link to={`/questions/manage?edit=${question.id}`} className="text-indigo-600 hover:text-indigo-800">
          Edit Question
        </Link>
      ),
    },
  ];

  if (isLoading) {
    return <div className="text-center py-10">Loading course details...</div>;
  }

  if (error) {
    return <div className="text-center py-10 text-red-600">Error: {error}</div>;
  }

  if (!course) {
    return <div className="text-center py-10 text-gray-600">Course not found.</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <Button variant="ghost" onClick={() => navigate('/courses/manage')} className="mb-6 text-sm">
        ← Back to Courses List
      </Button>

      <div className="bg-white shadow-xl rounded-lg p-6 mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">{course.name}</h1>
        <p className="text-lg text-indigo-600 font-semibold mb-1">Code: {course.code}</p>
        {course.description && <p className="text-gray-700 mt-2">{course.description}</p>}
      </div>

      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-semibold text-gray-700">Associated Questions</h2>
        <Link to={`/questions/manage?prefillCourseId=${course.id}`}>
            <Button variant="primary" size="sm">Add New Question to This Course</Button>
        </Link>
      </div>
      
      {associatedQuestions.length > 0 ? (
        <ResourceTable<QuestionListItemFE>
          data={associatedQuestions}
          columns={questionColumns}
        />
      ) : (
        <p className="text-gray-500 bg-white p-6 rounded-md shadow text-center">
            No questions are currently associated with this course. 
            You can add questions from the "Manage Questions" page or by clicking the button above.
        </p>
      )}
    </div>
  );
};

export default CourseDetailsPage;