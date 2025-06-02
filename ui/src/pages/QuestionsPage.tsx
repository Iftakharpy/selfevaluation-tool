import React, { useEffect, useState, useCallback } from 'react';
import questionService from '../services/questionService';
import qcaService from '../services/qcaService'; 
import type { QuestionListItemFE, QuestionFE, QuestionCreateFE, QuestionUpdateFE } from '../types/questionTypes';
import type { QCA, QCACreate, QCAUpdate } from '../types/qcaTypes'; 
import ResourceTable from '../components/management/ResourceTable';
import type { Column } from '../components/management/ResourceTable';
import Button from '../components/forms/Button';
import Modal from '../components/modals/Modal'; // Ensure this is the updated Modal
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

  const handleOpenCreateModal = () => {
    setEditingQuestion(null); 
    setEditingQuestionQCAs([]);
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleOpenEditModal = async (questionItem: QuestionListItemFE) => {
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
        // @ts-ignore
        if (qcaDataFromForm?.id) { 
          const updatePayload: QCAUpdate = {
            answer_association_type: qcaDataFromForm.answer_association_type,
            feedbacks_based_on_score: qcaDataFromForm.feedbacks_based_on_score,
          };
          if (qcaDataFromForm.answer_association_type === undefined) {
            delete updatePayload.answer_association_type;
          }
          if (qcaDataFromForm.feedbacks_based_on_score === undefined) {
            delete updatePayload.feedbacks_based_on_score;
          }
          // @ts-ignore
          await qcaService.updateQCA(qcaDataFromForm.id, updatePayload);
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
      
      handleCloseModal();
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
        <Button onClick={handleOpenCreateModal} variant="primary" disabled={isLoadingTable || isModalLoading}>
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
        onEdit={handleOpenEditModal}
        onDelete={handleOpenDeleteModal}
        isLoading={isLoadingTable && !isModalOpen} 
      />

      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        title={editingQuestion?.id ? 'Edit Question' : 'Create New Question'}
        size="4xl"
        // The QuestionForm has its own overflow-y-auto and max-height
        // so the modal's content area doesn't need explicit overflow handling here.
        // We can pass a class to style the modal body if needed for padding, etc.
        // bodyClassName="max-h-[80vh] overflow-y-auto" // Example if QuestionForm didn't scroll
      >
        {isModalLoading && <div className="text-center p-4">Loading question data...</div>}
        {/* @ts-ignore */}
        {!isModalLoading && isModalOpen && (editingQuestion || !editingQuestion?.id) && ( 
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