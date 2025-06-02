import React, { useEffect, useState, useCallback } from 'react';
import questionService from '../services/questionService';
import qcaService from '../services/qcaService'; // Import QCA Service
import type { QuestionListItemFE, QuestionFE, QuestionCreateFE, QuestionUpdateFE } from '../types/questionTypes';
import type { QCA, QCACreate, QCAUpdate } from '../types/qcaTypes'; // Import QCA types
import ResourceTable from '../components/management/ResourceTable';
import type { Column } from '../components/management/ResourceTable';
import Button from '../components/forms/Button';
import Modal from '../components/modals/Modal';
import QuestionForm from '../components/forms/QuestionForm';
import ConfirmDeleteModal from '../components/modals/ConfirmDeleteModal';
import { useNotifier } from '../contexts/NotificationContext';

const QuestionsPage: React.FC = () => {
  const [questions, setQuestions] = useState<QuestionListItemFE[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  
  const [editingQuestion, setEditingQuestion] = useState<QuestionFE | null>(null); // Full QuestionFE for form
  const [editingQuestionQCAs, setEditingQuestionQCAs] = useState<QCA[]>([]); // QCAs for the question being edited

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  
  const { addNotification } = useNotifier();

  const fetchQuestionsAndDependencies = useCallback(async () => {
    setIsLoading(true);
    try {
      const questionsData = await questionService.listQuestions();
      setQuestions(questionsData);
    } catch (error: any) {
      addNotification(error.message || 'Failed to fetch questions', 'error');
    } finally {
      setIsLoading(false);
    }
  }, [addNotification]);

  useEffect(() => {
    fetchQuestionsAndDependencies();
  }, [fetchQuestionsAndDependencies]);

  const handleOpenCreateModal = () => {
    setEditingQuestion(null); 
    setEditingQuestionQCAs([]);
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleOpenEditModal = async (questionItem: QuestionListItemFE) => {
    setIsLoading(true); // Or a specific loading state for the form
    setFormError(null);
    try {
        const fullQuestionData = await questionService.getQuestion(questionItem.id);
        const qcasData = await qcaService.listQCAs({ question_id: questionItem.id });
        setEditingQuestion(fullQuestionData);
        setEditingQuestionQCAs(qcasData);
        setIsModalOpen(true);
    } catch (error: any) {
        addNotification(error.message || 'Failed to fetch question details for editing.', 'error');
    } finally {
        setIsLoading(false);
    }
  };

  const handleOpenDeleteModal = (questionItem: QuestionListItemFE) => {
    setEditingQuestion({ id: questionItem.id, title: questionItem.title, answer_type: questionItem.answer_type, scoring_rules: {} }); 
    setIsDeleteModalOpen(true);
  };
  
  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingQuestion(null);
    setEditingQuestionQCAs([]);
    setFormError(null);
  };
  const handleCloseDeleteModal = () => {
    setIsDeleteModalOpen(false);
    setEditingQuestion(null);
  };

  const handleSubmitQuestionAndQCAs = async (
    questionData: QuestionCreateFE | QuestionUpdateFE,
    qcasToUpdate: Array<QCACreate | (QCAUpdate & { id?: string })>,
    qcasToDelete: string[]
  ) => {
    setIsSubmitting(true);
    setFormError(null);
    let currentQuestionId = editingQuestion?.id;

    try {
      // 1. Create or Update the Question
      if (currentQuestionId) { // Update existing question
        await questionService.updateQuestion(currentQuestionId, questionData as QuestionUpdateFE);
        addNotification('Question updated successfully!', 'success');
      } else { // Create new question
        const newQuestion = await questionService.createQuestion(questionData as QuestionCreateFE);
        currentQuestionId = newQuestion.id; // Get ID for new question
        addNotification('Question created successfully!', 'success');
      }

      if (!currentQuestionId) {
        throw new Error("Failed to get question ID for QCA operations.");
      }

      // 2. Process QCAs to Delete
      for (const qcaId of qcasToDelete) {
        await qcaService.deleteQCA(qcaId);
      }
      if (qcasToDelete.length > 0) addNotification(`${qcasToDelete.length} course association(s) removed.`, 'info');

      // 3. Process QCAs to Create or Update
      for (const qca of qcasToUpdate) {
		// @ts-ignore - currentQuestionId is guaranteed to be defined here
        if (qca?.id) { // Update existing QCA
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
          const { id, question_id, ...updateData } = qca as QCAUpdate & {id: string, question_id?:string}; // question_id not needed for update payload
		  // @ts-ignore - currentQuestionId is guaranteed to be defined here		  
          await qcaService.updateQCA(qca.id, updateData);
        } else { // Create new QCA
		  // @ts-ignore - currentQuestionId is guaranteed to be defined here
          const createData: QCACreate = {
            ...qca,
            question_id: currentQuestionId, // Assign current question ID
          };
          await qcaService.createQCA(createData);
        }
      }
      if (qcasToUpdate.length > 0) addNotification(`${qcasToUpdate.length} course association(s) saved.`, 'info');
      
      handleCloseModal();
      fetchQuestionsAndDependencies(); // Refresh list
    } catch (error: any) {
      const msg = error.response?.data?.detail || (editingQuestion?.id ? 'Failed to update question/associations.' : 'Failed to create question/associations.');
      setFormError(msg);
      addNotification(msg, 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteQuestion = async () => {
    if (!editingQuestion || !editingQuestion.id) return;
    setIsSubmitting(true);
    try {
      // Backend should handle deleting associated QCAs when a question is deleted
      await questionService.deleteQuestion(editingQuestion.id);
      addNotification('Question (and its associations) deleted successfully!', 'success');
      handleCloseDeleteModal();
      fetchQuestionsAndDependencies();
    } catch (error: any) {
      addNotification(error.response?.data?.detail || 'Failed to delete question.', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const columns: Column<QuestionListItemFE>[] = [
    { header: 'Title', accessor: 'title', className: 'font-medium text-gray-900' },
    { header: 'Type', accessor: 'answer_type', className: 'capitalize' },
    { header: 'Details', accessor: (item) => item.details ? (item.details.length > 70 ? `${item.details.substring(0, 67)}...` : item.details) : '-', className: 'text-sm text-gray-500 max-w-xs truncate' },
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">Manage Questions</h1>
        <Button onClick={handleOpenCreateModal} variant="primary">
          Create New Question
        </Button>
      </div>

      <ResourceTable<QuestionListItemFE>
        data={questions}
        columns={columns}
        onEdit={handleOpenEditModal}
        onDelete={handleOpenDeleteModal}
        isLoading={isLoading && !isModalOpen} // Don't show table loading if modal is open and loading its data
      />

      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        title={editingQuestion?.id ? 'Edit Question' : 'Create New Question'}
      >
        {/* @ts-ignore - currentQuestionId is guaranteed to be defined here */}
        {(isModalOpen && (editingQuestion || !editingQuestion?.id)) && ( // Ensure form is rendered only when ready
             <QuestionForm
                initialData={editingQuestion}
                initialQcas={editingQuestionQCAs}
                onSubmit={handleSubmitQuestionAndQCAs}
                onCancel={handleCloseModal}
                isSubmitting={isSubmitting}
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
          isLoading={isSubmitting}
        />
      )}
    </div>
  );
};

export default QuestionsPage;