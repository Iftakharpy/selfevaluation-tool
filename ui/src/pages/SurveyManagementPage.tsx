// File: ui/src/pages/SurveyManagementPage.tsx
import React, { useEffect, useState, useCallback } from 'react';
import surveyService from '../services/surveyService';
import type { SurveySummaryListItemFE, SurveyFE, SurveyCreateFE, SurveyUpdateFE } from '../types/surveyTypes';
import ResourceTable from '../components/management/ResourceTable';
import type { Column } from '../components/management/ResourceTable';
import Button from '../components/forms/Button';
import Modal from '../components/modals/Modal';
import ConfirmDeleteModal from '../components/modals/ConfirmDeleteModal';
import { useNotifier } from '../contexts/NotificationContext';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom'; 
import SurveyForm from '../components/forms/SurveyForm'; 

const SurveyManagementPage: React.FC = () => {
  const [mySurveys, setMySurveys] = useState<SurveySummaryListItemFE[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  
  const [editingSurvey, setEditingSurvey] = useState<SurveyFE | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  
  const { addNotification } = useNotifier();
  const { user } = useAuth();
  const navigate = useNavigate();


  const fetchMySurveys = useCallback(async () => {
    if (!user) return;
    setIsLoading(true);
    try {
      // Assuming listAllSurveysForTeacher returns surveys created by the current teacher
      // or all surveys if general teacher access is intended.
      // The current logic filters client-side if needed, or relies on backend filtering.
      const allSurveys = await surveyService.listAllSurveysForTeacher();
      // If backend doesn't filter by created_by, you might need to filter here:
      // const filteredSurveys = allSurveys.filter(survey => survey.created_by === user.id);
      // setMySurveys(filteredSurveys);
      setMySurveys(allSurveys.filter(survey => survey.created_by === user.id)); // Ensure only my surveys are shown
    } catch (error: any) {
      addNotification(error.message || 'Failed to fetch surveys', 'error');
    } finally {
      setIsLoading(false);
    }
  }, [addNotification, user]);

  useEffect(() => {
    fetchMySurveys();
  }, [fetchMySurveys]);

  const handleOpenCreateModal = () => {
    setEditingSurvey(null); 
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleOpenEditModal = async (surveyItem: SurveySummaryListItemFE) => {
    setIsLoading(true); 
    setFormError(null);
    try {
        const fullSurveyData = await surveyService.getSurveyDetail(surveyItem.id);
        setEditingSurvey(fullSurveyData);
        setIsModalOpen(true);
    } catch (error: any) {
        addNotification(error.message || 'Failed to fetch survey details for editing.', 'error');
    } finally {
        // Only set loading to false specific to modal data, not table loading
        // If you have a separate state for modal loading, use that.
        // For now, assuming this doesn't interfere with table's isLoading
    }
  };

  const handleOpenDeleteModal = (surveyItem: SurveySummaryListItemFE) => {
    // We only need id and title for the confirmation modal for SurveyFE type
    const surveyForDelete: SurveyFE = { 
        ...surveyItem, 
        questions: [], // Add default/empty for fields not in SurveySummaryListItemFE
        course_skill_total_score_thresholds: {},
        course_outcome_thresholds: {}
    };
    setEditingSurvey(surveyForDelete); 
    setIsDeleteModalOpen(true);
  };
  
  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingSurvey(null);
    setFormError(null);
  };
  
  const handleCloseDeleteModal = () => {
    setIsDeleteModalOpen(false);
    setEditingSurvey(null);
  };

  const handleSubmitSurvey = async (data: SurveyCreateFE | SurveyUpdateFE) => {
    setIsSubmitting(true);
    setFormError(null);
    try {
      if (editingSurvey && editingSurvey.id) {
        await surveyService.updateSurvey(editingSurvey.id, data as SurveyUpdateFE);
        addNotification('Survey updated successfully!', 'success');
      } else {
        await surveyService.createSurvey(data as SurveyCreateFE);
        addNotification('Survey created successfully!', 'success');
      }
      handleCloseModal();
      fetchMySurveys(); 
    } catch (error: any) {
      const msg = error.response?.data?.detail || (editingSurvey ? 'Failed to update survey.' : 'Failed to create survey.');
      setFormError(msg); 
      addNotification(msg, 'error'); 
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteSurvey = async () => {
    if (!editingSurvey || !editingSurvey.id) return;
    setIsSubmitting(true);
    try {
      await surveyService.deleteSurvey(editingSurvey.id);
      addNotification('Survey deleted successfully!', 'success');
      handleCloseDeleteModal();
      fetchMySurveys();
    } catch (error: any) {
      addNotification(error.response?.data?.detail || 'Failed to delete survey.', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleTogglePublish = async (survey: SurveySummaryListItemFE) => {
    setIsSubmitting(true);
    try {
      const updateData: SurveyUpdateFE = { is_published: !survey.is_published };
      await surveyService.updateSurvey(survey.id, updateData);
      addNotification(`Survey ${!survey.is_published ? 'published' : 'unpublished'} successfully!`, 'success');
      fetchMySurveys();
    } catch (error: any) {
      addNotification(error.response?.data?.detail || 'Failed to toggle publish status.', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCopyLink = (surveyId: string) => {
    const link = `${window.location.origin}/survey/take/${surveyId}`;
    navigator.clipboard.writeText(link)
      .then(() => {
        addNotification('Survey link copied to clipboard!', 'success');
      })
      .catch(err => {
        console.error('Failed to copy link: ', err);
        addNotification('Failed to copy link. Please copy manually.', 'error');
      });
  };

  const columns: Column<SurveySummaryListItemFE>[] = [
    { header: 'Title', accessor: 'title', className: 'font-medium text-gray-900' },
    { 
      header: 'Description', 
      accessor: (item) => item.description ? (item.description.length > 50 ? `${item.description.substring(0, 47)}...` : item.description) : '-', 
      className: 'text-sm text-gray-500 max-w-sm truncate' 
    },
    { header: 'Courses', accessor: (item) => item.course_ids.length, className: 'text-center' },
    { 
      header: 'Status', 
      accessor: (item) => (
        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
          item.is_published ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
        }`}>
          {item.is_published ? 'Published' : 'Draft'}
        </span>
      )
    },
    { header: 'Last Updated', accessor: (item) => new Date(item.updated_at).toLocaleDateString() },
    { 
      header: 'Manage',
      accessor: (item) => (
        <div className="space-x-1 whitespace-nowrap">
          <Button size="xs" variant="ghost" onClick={() => handleOpenEditModal(item)} disabled={isSubmitting || isLoading}>Edit</Button>
          <Button size="xs" variant="ghost" onClick={() => handleTogglePublish(item)} disabled={isSubmitting || isLoading}>
            {item.is_published ? 'Unpublish' : 'Publish'}
          </Button>
          <Button size="xs" variant="ghost" onClick={() => navigate(`/surveys/${item.id}/attempts-overview`)} disabled={isSubmitting || isLoading}>
            Attempts
          </Button>
          {/* ADDED COPY LINK BUTTON */}
          <Button size="xs" variant="ghost" onClick={() => handleCopyLink(item.id)} disabled={isLoading}>
            Copy Link
          </Button>
          <Button size="xs" variant="danger" onClick={() => handleOpenDeleteModal(item)} disabled={isSubmitting || isLoading}>Delete</Button>
        </div>
      )
    }
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">Manage Your Surveys</h1>
        <Button onClick={handleOpenCreateModal} variant="primary" disabled={isLoading}>
          Create New Survey
        </Button>
      </div>

      <ResourceTable<SurveySummaryListItemFE>
        data={mySurveys}
        columns={columns}
        isLoading={isLoading}
        // onEdit, onDelete are handled by the custom accessor column now
      />

      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        title={editingSurvey ? 'Edit Survey' : 'Create New Survey'}
      >
        {isModalOpen && ( 
            <SurveyForm
              initialData={editingSurvey}
              onSubmit={handleSubmitSurvey}
              onCancel={handleCloseModal}
              isSubmitting={isSubmitting}
              submitError={formError}
            />
        )}
      </Modal>

      {editingSurvey && (
        <ConfirmDeleteModal
          isOpen={isDeleteModalOpen}
          onClose={handleCloseDeleteModal}
          onConfirm={handleDeleteSurvey}
          itemName={`survey "${editingSurvey.title}"`}
          isLoading={isSubmitting}
        />
      )}
    </div>
  );
};

export default SurveyManagementPage;