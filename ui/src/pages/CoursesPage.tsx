// ui/src/pages/CoursesPage.tsx
import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom'; // IMPORT useNavigate
import courseService from '../services/courseService';
import type { Course, CourseCreate, CourseUpdate } from '../types/courseTypes';
import ResourceTable from '../components/management/ResourceTable';
import type { Column } from '../components/management/ResourceTable';
import Button from '../components/forms/Button';
import Modal from '../components/modals/Modal';
import CourseForm from '../components/forms/CourseForm';
import ConfirmDeleteModal from '../components/modals/ConfirmDeleteModal';
import { useNotifier } from '../contexts/NotificationContext';

const CoursesPage: React.FC = () => {
  const [courses, setCourses] = useState<Course[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  
  const { addNotification } = useNotifier();
  const navigate = useNavigate(); // INITIALIZE useNavigate

  const fetchCourses = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await courseService.listCourses();
      setCourses(data);
    } catch (error: any) {
      addNotification(error.message || 'Failed to fetch courses', 'error');
    } finally {
      setIsLoading(false);
    }
  }, [addNotification]);

  useEffect(() => {
    fetchCourses();
  }, [fetchCourses]);

  const handleOpenCreateModal = () => {
    setSelectedCourse(null);
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (course: Course) => {
    setSelectedCourse(course);
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleOpenDeleteModal = (course: Course) => {
    setSelectedCourse(course);
    setIsDeleteModalOpen(true);
  };

  // ADDED: Handler for viewing course details
  const handleViewDetails = (course: Course) => {
    navigate(`/courses/details/${course.id}`);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedCourse(null);
    setFormError(null);
  };
  
  const handleCloseDeleteModal = () => {
    setIsDeleteModalOpen(false);
    setSelectedCourse(null);
  };

  const handleSubmitCourse = async (data: CourseCreate | CourseUpdate) => {
    setIsSubmitting(true);
    setFormError(null);
    try {
      if (selectedCourse && selectedCourse.id) {
        await courseService.updateCourse(selectedCourse.id, data as CourseUpdate);
        addNotification('Course updated successfully!', 'success');
      } else {
        await courseService.createCourse(data as CourseCreate);
        addNotification('Course created successfully!', 'success');
      }
      handleCloseModal();
      fetchCourses(); // Refresh list
    } catch (error: any) {
      const msg = error.response?.data?.detail || (selectedCourse ? 'Failed to update course.' : 'Failed to create course.');
      setFormError(msg);
      addNotification(msg, 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteCourse = async () => {
    if (!selectedCourse || !selectedCourse.id) return;
    setIsSubmitting(true);
    try {
      await courseService.deleteCourse(selectedCourse.id);
      addNotification('Course deleted successfully!', 'success');
      handleCloseDeleteModal();
      fetchCourses(); // Refresh list
    } catch (error: any) {
      addNotification(error.response?.data?.detail || 'Failed to delete course.', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const columns: Column<Course>[] = [
    { header: 'Name', accessor: 'name', className: 'font-medium text-gray-900' },
    { header: 'Code', accessor: 'code' },
    { header: 'Description', accessor: (item) => item.description ? (item.description.length > 70 ? `${item.description.substring(0, 67)}...` : item.description) : '-', className: 'text-sm text-gray-500 max-w-xs truncate' },
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">Manage Courses</h1>
        <Button onClick={handleOpenCreateModal} variant="primary">
          Create New Course
        </Button>
      </div>

      <ResourceTable<Course>
        data={courses}
        columns={columns}
        onEdit={handleOpenEditModal}
        onDelete={handleOpenDeleteModal}
        onView={handleViewDetails} // ADDED: Pass the onView handler
        isLoading={isLoading}
      />

      <Modal
        isOpen={isModalOpen}
        size='xl' // Adjusted size for CourseForm
        onClose={handleCloseModal}
        title={selectedCourse ? 'Edit Course' : 'Create New Course'}
      >
        <CourseForm
          initialData={selectedCourse}
          onSubmit={handleSubmitCourse}
          onCancel={handleCloseModal}
          isSubmitting={isSubmitting}
          submitError={formError}
        />
      </Modal>

      {selectedCourse && (
        <ConfirmDeleteModal
          isOpen={isDeleteModalOpen}
          onClose={handleCloseDeleteModal}
          onConfirm={handleDeleteCourse}
          itemName={`course "${selectedCourse.name}"`}
          isLoading={isSubmitting}
        />
      )}
    </div>
  );
};

export default CoursesPage;