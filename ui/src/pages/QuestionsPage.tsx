// ui/src/pages/QuestionsPage.tsx
import React, { useEffect, useState, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom'; // IMPORT useLocation & useNavigate
import questionService from '../services/questionService';
import qcaService from '../services/qcaService'; 
import type { QuestionListItemFE, QuestionFE, QuestionCreateFE, QuestionUpdateFE } from '../types/questionTypes';
import type { QCA, QCACreate, QCAUpdate, AnswerAssociationTypeEnumFE } from '../types/qcaTypes'; // Ensure AnswerAssociationTypeEnumFE is imported
import ResourceTable from '../components/management/ResourceTable';
import type { Column } from '../components/management/ResourceTable';
import Button from '../components/forms/Button';
import Modal from '../components/modals/Modal';
import QuestionForm from '../components/forms/QuestionForm';
import ConfirmDeleteModal from '../components/modals/ConfirmDeleteModal';
import { useNotifier } from '../contexts/NotificationContext';
import Input from '../components/forms/Input'; 

const QuestionsPage: React.FC = () => {
  const [questions, setQuestions] = useState<QuestionListItemFE[]>([]);
  const [isLoadingTable, setIsLoadingTable] = useState(true); 
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  
  const [editingQuestion, setEditingQuestion] = useState<QuestionFE | null>(null); 
  const [editingQuestionQCAs, setEditingQuestionQCAs] = useState<QCA[]>([]); 

  const [isSubmittingForm, setIsSubmittingForm] = useState(false); 
  const [isModalLoading, setIsModalLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null); 
  const [searchTerm, setSearchTerm] = useState(''); 
  
  const { addNotification } = useNotifier();
  const location = useLocation(); // For query params
  const navigate = useNavigate(); // For clearing query params


  const fetchQuestionsAndDependencies = useCallback(async () => {
    setIsLoadingTable(true);
    try {
      const questionsData = await questionService.listQuestions();
      setQuestions(questionsData);
    } catch (error: any) {
      addNotification(error.message || 'Failed to fetch questions', 'error');
    } finally {
      setIsLoadingTable(false);
    }
  }, [addNotification]);

  useEffect(() => {
    fetchQuestionsAndDependencies();
  }, [fetchQuestionsAndDependencies]);

  // EFFECT TO HANDLE QUERY PARAMS FOR EDITING OR PRE-FILLING
  useEffect(() => {
    const queryParams = new URLSearchParams(location.search);
    const editQuestionId = queryParams.get('edit');
    const prefillCourseIdForNewQuestion = queryParams.get('prefillCourseId');

    if (editQuestionId) {
      const questionToEdit = questions.find(q => q.id === editQuestionId);
      if (questionToEdit) {
        handleOpenEditModal(questionToEdit, true); // Pass a flag to prevent clearing query params immediately
      } else if (!isLoadingTable) { 
        // If questions are loaded and still not found, it's an invalid ID
        addNotification(`Question with ID ${editQuestionId} not found for editing.`, 'warning');
        navigate('/questions/manage', { replace: true }); // Clear query params
      }
    } else if (prefillCourseIdForNewQuestion && !isModalOpen && !editingQuestion) { // Only open if not already in a modal
        handleOpenCreateModal(prefillCourseIdForNewQuestion, true); // Pass flag
    }
  }, [location.search, questions, isLoadingTable]); // Rerun when search params or questions list change

  const handleOpenCreateModal = (prefillCourseId?: string | null, calledFromEffect = false) => {
    setEditingQuestion(null); 
    const initialQcasForCreate = prefillCourseId
    // @ts-ignore
      ? [{ course_id: prefillCourseId, question_id: '', answer_association_type: 'positive' as AnswerAssociationTypeEnumFE, feedbacks_based_on_score: [] } as QCA] // Cast to QCA for initialQcas prop
      : [];
    setEditingQuestionQCAs(initialQcasForCreate);
    setFormError(null);
    setIsModalOpen(true);
    if (!calledFromEffect) { // Clear query params if opened by button click
        navigate('/questions/manage', { replace: true });
    }
  };

  const handleOpenEditModal = async (questionItem: QuestionListItemFE, calledFromEffect = false) => {
    setIsModalLoading(true); 
    setFormError(null);
    setEditingQuestion(null); 
    try {
        const fullQuestionData = await questionService.getQuestion(questionItem.id);
        const qcasData = await qcaService.listQCAs({ question_id: questionItem.id });
        setEditingQuestion(fullQuestionData);
        setEditingQuestionQCAs(qcasData);
        setIsModalOpen(true);
    } catch (error: any) {
        addNotification(error.message || 'Failed to fetch question details for editing.', 'error');
        setIsModalOpen(false); 
    } finally {
        setIsModalLoading(false); 
        if (!calledFromEffect) { // Clear query params if opened by button click
            navigate('/questions/manage', { replace: true });
        }
    }
  };

  const handleOpenDeleteModal = (questionItem: QuestionListItemFE) => {
    const qToDelete: QuestionFE = { 
        id: questionItem.id, 
        title: questionItem.title, 
        answer_type: questionItem.answer_type, 
        details: questionItem.details,
        answer_options: {}, 
        scoring_rules: {} 
    };
    setEditingQuestion(qToDelete); 
    setIsDeleteModalOpen(true);
  };
  
  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingQuestion(null);
    setEditingQuestionQCAs([]);
    setFormError(null);
    // Clear query params when modal is closed, regardless of how it was opened
    navigate('/questions/manage', { replace: true }); 
  };

  const handleCloseDeleteModal = () => {
    setIsDeleteModalOpen(false);
    setEditingQuestion(null);
  };

  const handleSubmitQuestionAndQCAs = async (
    questionData: QuestionCreateFE | QuestionUpdateFE,
    qcasToUpdateOrCrate: Array<QCACreate | (QCAUpdate & { id?: string })>,
    qcasToDelete: string[]
  ) => {
    setIsSubmittingForm(true);
    setFormError(null);
    let currentQuestionId = editingQuestion?.id;

    try {
      if (currentQuestionId) { 
        await questionService.updateQuestion(currentQuestionId, questionData as QuestionUpdateFE);
        addNotification('Question updated successfully!', 'success');
      } else { 
        const newQuestion = await questionService.createQuestion(questionData as QuestionCreateFE);
        currentQuestionId = newQuestion.id; 
        addNotification('Question created successfully!', 'success');
      }

      if (!currentQuestionId) {
        throw new Error("Failed to get question ID for QCA operations.");
      }

      for (const qcaId of qcasToDelete) {
        await qcaService.deleteQCA(qcaId);
      }
      if (qcasToDelete.length > 0) addNotification(`${qcasToDelete.length} course association(s) removed.`, 'info');

      for (const qcaDataFromForm of qcasToUpdateOrCrate) {
        const qcaIsExisting = 'id' in qcaDataFromForm && qcaDataFromForm.id;
        if (qcaIsExisting) { 
          const updatePayload: QCAUpdate = {
            answer_association_type: qcaDataFromForm.answer_association_type,
            feedbacks_based_on_score: qcaDataFromForm.feedbacks_based_on_score,
          };
          await qcaService.updateQCA(qcaDataFromForm.id as string, updatePayload);
        } else { 
          const createPayload: QCACreate = {
            question_id: currentQuestionId, 
            // @ts-ignore
            course_id: qcaDataFromForm.course_id, 
            // @ts-ignore
            answer_association_type: qcaDataFromForm.answer_association_type,
            feedbacks_based_on_score: qcaDataFromForm.feedbacks_based_on_score,
          };
          await qcaService.createQCA(createPayload);
        }
      }
      if (qcasToUpdateOrCrate.length > 0) addNotification(`${qcasToUpdateOrCrate.length} course association(s) saved.`, 'info');
      
      handleCloseModal(); // This will also clear query params
      fetchQuestionsAndDependencies(); 
    } catch (error: any) {
      let friendlyErrorMessage = "An unexpected error occurred during submission.";
      if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          friendlyErrorMessage = error.response.data.detail
            .map((err: any) => {
                const loc = err.loc && err.loc.length > 1 ? err.loc.slice(1).join(' -> ') : 'General';
                return `${loc}: ${err.msg}`;
            })
            .join('; ');
        } 
        else if (typeof error.response.data.detail === 'string') {
          friendlyErrorMessage = error.response.data.detail;
        }
      } else if (error.message) {
        friendlyErrorMessage = error.message;
      }
      
      setFormError(friendlyErrorMessage); 
      addNotification(friendlyErrorMessage, 'error'); 
    } finally {
      setIsSubmittingForm(false);
    }
  };

  const handleDeleteQuestion = async () => {
    if (!editingQuestion || !editingQuestion.id) return;
    setIsSubmittingForm(true);
    try {
      await questionService.deleteQuestion(editingQuestion.id);
      addNotification('Question (and its associations) deleted successfully!', 'success');
      handleCloseDeleteModal();
      fetchQuestionsAndDependencies();
    } catch (error: any) {
      addNotification(error.response?.data?.detail || 'Failed to delete question.', 'error');
    } finally {
      setIsSubmittingForm(false);
    }
  };

  const filteredQuestions = questions.filter(question =>
    question.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (question.details && question.details.toLowerCase().includes(searchTerm.toLowerCase())) ||
    question.answer_type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const columns: Column<QuestionListItemFE>[] = [
    { header: 'Title', accessor: 'title', className: 'font-medium text-gray-900' },
    { header: 'Type', accessor: 'answer_type', className: 'capitalize' },
    { header: 'Details', accessor: (item) => item.details ? (item.details.length > 70 ? `${item.details.substring(0, 67)}...` : item.details) : '-', className: 'text-sm text-gray-500 max-w-xs truncate' },
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">Manage Questions</h1>
        <Button onClick={() => handleOpenCreateModal()} variant="primary" disabled={isLoadingTable || isModalLoading}>
          Create New Question
        </Button>
      </div>

      <div className="mb-4">
        <Input
          id="question-search"
          type="text"
          placeholder="Search by title, details, or type..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          containerClassName="max-w-md"
        />
      </div>

      <ResourceTable<QuestionListItemFE>
        data={filteredQuestions}
        columns={columns}
        onEdit={(item) => handleOpenEditModal(item)} // Use custom onEdit to clear query params properly
        onDelete={handleOpenDeleteModal}
        isLoading={isLoadingTable && !isModalOpen} 
      />

      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        title={editingQuestion?.id ? 'Edit Question' : 'Create New Question'}
        size="4xl" 
      >
        {isModalLoading && <div className="text-center p-4">Loading question data...</div>}
        {!isModalLoading && isModalOpen && (
             <QuestionForm
                initialData={editingQuestion}
                initialQcas={editingQuestionQCAs}
                onSubmit={handleSubmitQuestionAndQCAs}
                onCancel={handleCloseModal}
                isSubmitting={isSubmittingForm}
                submitError={formError} 
            />
        )}
      </Modal>

      {editingQuestion && (
        <ConfirmDeleteModal
          isOpen={isDeleteModalOpen}
          onClose={handleCloseDeleteModal}
          onConfirm={handleDeleteQuestion}
          itemName={`question "${editingQuestion.title}"`}
          isLoading={isSubmittingForm}
        />
      )}
    </div>
  );
};

export default QuestionsPage;