import React, { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import type { Course, CourseCreate, CourseUpdate } from '../../types/courseTypes';
import Input from './Input';
import Textarea from './TextArea'; // Corrected casing to match your file structure
import Button from './Button';

interface CourseFormProps {
  initialData?: Course | null; // For editing
  onSubmit: (data: CourseCreate | CourseUpdate) => Promise<void>;
  onCancel: () => void;
  isSubmitting: boolean;
  submitError?: string | null;
}

const CourseForm: React.FC<CourseFormProps> = ({
  initialData,
  onSubmit,
  onCancel,
  isSubmitting,
  submitError,
}) => {
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [description, setDescription] = useState('');
  const [errors, setErrors] = useState<{ name?: string; code?: string; description?: string }>({});

  useEffect(() => {
    if (initialData) {
      setName(initialData.name);
      setCode(initialData.code);
      setDescription(initialData.description || '');
    } else {
      setName('');
      setCode('');
      setDescription('');
    }
  }, [initialData]);

  const validate = (): boolean => {
    const newErrors: { name?: string; code?: string } = {};
    if (!name.trim()) newErrors.name = "Course name is required.";
    else if (name.trim().length < 3) newErrors.name = "Course name must be at least 3 characters.";
    
    if (!code.trim()) newErrors.code = "Course code is required.";
    else if (code.trim().length < 2) newErrors.code = "Course code must be at least 2 characters.";

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    const courseData: CourseCreate | CourseUpdate = {
      name,
      code,
      description: description.trim() || undefined, // Send undefined if empty
    };
    onSubmit(courseData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {submitError && (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-3 mb-4" role="alert">
          <p className="font-bold">Submission Error</p>
          <p>{submitError}</p>
        </div>
      )}
      <Input
        label="Course Name"
        id="course-name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        error={errors.name}
        disabled={isSubmitting}
        required
        maxLength={100}
      />
      <Input
        label="Course Code"
        id="course-code"
        value={code}
        onChange={(e) => setCode(e.target.value)}
        error={errors.code}
        disabled={isSubmitting}
        required
        maxLength={20}
      />
      <Textarea
        label="Description (Optional)"
        id="course-description"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        rows={4}
        disabled={isSubmitting}
        maxLength={500}
      />
      <div className="flex justify-end space-x-3 pt-2">
        <Button type="button" variant="ghost" onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button type="submit" variant="primary" isLoading={isSubmitting}>
          {initialData ? 'Update Course' : 'Create Course'}
        </Button>
      </div>
    </form>
  );
};

export default CourseForm;
