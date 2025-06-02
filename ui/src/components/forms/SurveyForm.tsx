// File: ui/src/components/forms/SurveyForm.tsx
import React, { useState, useEffect, useCallback } from 'react';
import type { FormEvent } from 'react';
import type { SurveyFE, SurveyCreateFE, SurveyUpdateFE, ScoreFeedbackItemFE, OutcomeThresholdItemFE } from '../../types/surveyTypes';
import { FeedbackComparisonEnumFE, OutcomeCategoryEnumFE } from '../../types/surveyTypes';
import type { Course } from '../../types/courseTypes';
import courseService from '../../services/courseService';
import Input from './Input';
import Textarea from './TextArea';
import Button from './Button';
import Select from './Select';
import { useNotifier } from '../../contexts/NotificationContext';
import Tooltip from '../common/Tooltip'; // IMPORT
import { InformationCircleIcon } from '../icons/InformationCircleIcon'; // IMPORT

interface SurveyFormProps {
  initialData?: SurveyFE | null;
  onSubmit: (data: SurveyCreateFE | SurveyUpdateFE) => Promise<void>;
  onCancel: () => void;
  isSubmitting: boolean;
  submitError?: string | null;
}

const comparisonOptions = Object.values(FeedbackComparisonEnumFE).map(comp => ({ value: comp, label: comp.toUpperCase() }));
const outcomeCategoryOptions = Object.values(OutcomeCategoryEnumFE).map(cat => ({ value: cat, label: cat.replace(/_/g, ' ') }));

const SurveyForm: React.FC<SurveyFormProps> = ({
  initialData,
  onSubmit,
  onCancel,
  isSubmitting,
  submitError,
}) => {
  const { addNotification } = useNotifier();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [isPublished, setIsPublished] = useState(false);
  const [allAvailableCourses, setAllAvailableCourses] = useState<Course[]>([]);
  const [selectedCourseIds, setSelectedCourseIds] = useState<string[]>([]);
  const [feedbackThresholds, setFeedbackThresholds] = useState<Record<string, ScoreFeedbackItemFE[]>>({});
  const [outcomeThresholds, setOutcomeThresholds] = useState<Record<string, OutcomeThresholdItemFE[]>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});

  const resetForm = useCallback(() => {
    setTitle(initialData?.title || '');
    setDescription(initialData?.description || '');
    setIsPublished(initialData?.is_published || false);
    setSelectedCourseIds(initialData?.course_ids || []);
    setFeedbackThresholds(initialData?.course_skill_total_score_thresholds 
      ? JSON.parse(JSON.stringify(initialData.course_skill_total_score_thresholds)) 
      : {});
    setOutcomeThresholds(initialData?.course_outcome_thresholds 
      ? JSON.parse(JSON.stringify(initialData.course_outcome_thresholds)) 
      : {});
    setErrors({});
  }, [initialData]);

  useEffect(() => {
    resetForm();
  }, [resetForm]);

  useEffect(() => {
    courseService.listCourses()
      .then(setAllAvailableCourses)
      .catch(() => addNotification("Failed to load available courses for survey.", "error"));
  }, [addNotification]);

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (!title.trim()) newErrors.title = "Survey title is required.";
    if (selectedCourseIds.length === 0) newErrors.courses = "At least one course must be associated with the survey.";
    
    selectedCourseIds.forEach(courseId => {
        (feedbackThresholds[courseId] || []).forEach((rule, index) => {
            if (isNaN(rule.score_value)) newErrors[`fb_score_${courseId}_${index}`] = "Score must be a number.";
            if (!rule.feedback.trim()) newErrors[`fb_text_${courseId}_${index}`] = "Feedback text cannot be empty.";
        });
        (outcomeThresholds[courseId] || []).forEach((rule, index) => {
            if (isNaN(rule.score_value)) newErrors[`out_score_${courseId}_${index}`] = "Score must be a number.";
        });
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) {
        addNotification("Please correct the errors in the form.", "error");
        return;
    }
    const surveyData: SurveyCreateFE | SurveyUpdateFE = {
      title,
      description: description.trim() || undefined,
      is_published: isPublished,
      course_ids: selectedCourseIds,
      course_skill_total_score_thresholds: Object.fromEntries(
        Object.entries(feedbackThresholds).filter(([courseId]) => selectedCourseIds.includes(courseId))
      ),
      course_outcome_thresholds: Object.fromEntries(
        Object.entries(outcomeThresholds).filter(([courseId]) => selectedCourseIds.includes(courseId))
      ),
    };
    onSubmit(surveyData);
  };

  const handleCourseSelectionChange = (courseId: string) => {
    setSelectedCourseIds(prev => 
      prev.includes(courseId) 
        ? prev.filter(id => id !== courseId) 
        : [...prev, courseId]
    );
  };

  const addFeedbackRule = (courseId: string) => {
    setFeedbackThresholds(prev => ({
      ...prev,
      [courseId]: [...(prev[courseId] || []), { score_value: 0, comparison: FeedbackComparisonEnumFE.EQ, feedback: '' }]
    }));
  };
  const updateFeedbackRule = (courseId: string, ruleIndex: number, field: keyof ScoreFeedbackItemFE, value: any) => {
    setFeedbackThresholds(prev => {
      const courseRules = [...(prev[courseId] || [])];
      const ruleToUpdate = { ...courseRules[ruleIndex] };
      if (field === 'score_value') ruleToUpdate[field] = Number(value);
      else if (field === 'comparison') ruleToUpdate[field] = value as FeedbackComparisonEnumFE;
      else ruleToUpdate[field] = value as string;
      courseRules[ruleIndex] = ruleToUpdate;
      return { ...prev, [courseId]: courseRules };
    });
  };
  const removeFeedbackRule = (courseId: string, ruleIndex: number) => {
    setFeedbackThresholds(prev => ({
      ...prev,
      [courseId]: (prev[courseId] || []).filter((_, i) => i !== ruleIndex)
    }));
  };

  const addOutcomeRule = (courseId: string) => {
    setOutcomeThresholds(prev => ({
      ...prev,
      [courseId]: [...(prev[courseId] || []), { score_value: 0, comparison: FeedbackComparisonEnumFE.EQ, outcome: OutcomeCategoryEnumFE.UNDEFINED }]
    }));
  };
  const updateOutcomeRule = (courseId: string, ruleIndex: number, field: keyof OutcomeThresholdItemFE, value: any) => {
    setOutcomeThresholds(prev => {
      const courseRules = [...(prev[courseId] || [])];
      const ruleToUpdate = { ...courseRules[ruleIndex] };
       if (field === 'score_value') ruleToUpdate[field] = Number(value);
       else if (field === 'comparison') ruleToUpdate[field] = value as FeedbackComparisonEnumFE;
       else ruleToUpdate[field] = value as OutcomeCategoryEnumFE;
      courseRules[ruleIndex] = ruleToUpdate;
      return { ...prev, [courseId]: courseRules };
    });
  };
  const removeOutcomeRule = (courseId: string, ruleIndex: number) => {
    setOutcomeThresholds(prev => ({
      ...prev,
      [courseId]: (prev[courseId] || []).filter((_, i) => i !== ruleIndex)
    }));
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-h-[80vh] overflow-y-auto p-1 pr-3">
      {submitError && (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-3 mb-4" role="alert">
          <p className="font-bold">Submission Error</p>
          <p>{submitError}</p>
        </div>
      )}
      {errors.form && <p className="text-xs text-red-600">{errors.form}</p>}

      <Input label="Survey Title" id="survey-title" value={title} onChange={(e) => setTitle(e.target.value)} error={errors.title} disabled={isSubmitting} required />
      <Textarea label="Description (Optional)" id="survey-description" value={description} onChange={(e) => setDescription(e.target.value)} rows={3} disabled={isSubmitting} />
      
      <div className="flex items-center space-x-2">
        <input
          type="checkbox"
          id="survey-published"
          checked={isPublished}
          onChange={(e) => setIsPublished(e.target.checked)}
          disabled={isSubmitting}
          className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
        />
        <label htmlFor="survey-published" className="text-sm text-gray-700 flex items-center">
          Publish this survey
          <Tooltip text="If checked, students will be able to see and take this survey. Uncheck to keep it as a draft.">
            <InformationCircleIcon className="h-4 w-4 text-gray-400 hover:text-gray-600 ml-1 cursor-pointer" />
          </Tooltip>
        </label>
      </div>
      {errors.is_published && <p className="text-xs text-red-600">{errors.is_published}</p>}

      <fieldset className="border p-4 rounded-md">
        <legend className="text-md font-medium text-gray-700 px-1 flex items-center">
          Associated Courses
          <Tooltip text="Select the courses this survey will assess. At least one course is required. Max scores for each course are calculated based on the questions linked to them via QCAs (Question-Course Associations created in the Question Management page).">
            <InformationCircleIcon className="h-5 w-5 text-gray-400 hover:text-gray-600 ml-1 cursor-pointer" />
          </Tooltip>
        </legend>
        {errors.courses && <p className="text-xs text-red-600 mb-2">{errors.courses}</p>}
        {allAvailableCourses.length === 0 && <p className="text-sm text-gray-500">Loading courses or no courses available to associate.</p>}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 max-h-48 overflow-y-auto mt-2">
          {allAvailableCourses.map(course => (
            <div key={course.id} className="flex items-center p-2 border rounded-md bg-gray-50 hover:bg-gray-100">
              <input
                type="checkbox"
                id={`course-${course.id}`}
                checked={selectedCourseIds.includes(course.id)}
                onChange={() => handleCourseSelectionChange(course.id)}
                disabled={isSubmitting}
                className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
              />
              <label htmlFor={`course-${course.id}`} className="ml-2 text-sm text-gray-800 truncate" title={`${course.name} (${course.code})`}>
                {course.name} ({course.code})
              </label>
            </div>
          ))}
        </div>
      </fieldset>

      {selectedCourseIds.length > 0 && (
        <fieldset className="border p-4 rounded-md mt-4">
          <legend className="text-md font-medium text-gray-700 px-1 flex items-center">
            Course-Specific Thresholds
            <Tooltip text="Define feedback and outcome categories based on the student's total score for each associated course. The total score for a course is the sum of scores from questions linked to it.">
              <InformationCircleIcon className="h-5 w-5 text-gray-400 hover:text-gray-600 ml-1 cursor-pointer" />
            </Tooltip>
          </legend>
          
          {selectedCourseIds.map(courseId => {
            const course = allAvailableCourses.find(c => c.id === courseId);
            if (!course) return null;

            return (
              <div key={courseId} className="my-4 p-3 border rounded-lg bg-slate-50">
                <h4 className="text-lg font-semibold text-indigo-700 mb-2">{course.name} ({course.code})</h4>
                
                <div className="mb-4 pl-2 border-l-2 border-blue-300">
                  <h5 className="text-sm font-medium text-gray-600 mb-1 flex items-center">
                    Feedback Rules (for this course)
                    <Tooltip text="Feedback displayed to the student based on their total score for this specific course.">
                      <InformationCircleIcon className="h-4 w-4 text-gray-400 hover:text-gray-600 ml-1 cursor-pointer" />
                    </Tooltip>
                  </h5>
                  {(feedbackThresholds[courseId] || []).map((fbRule, ruleIdx) => (
                    <div key={`fb-${courseId}-${ruleIdx}`} className="grid grid-cols-1 md:grid-cols-7 gap-2 items-end p-2 border rounded bg-white my-1">
                      {/* @ts-ignore */}
                      <Input error={errors[`fb_score_${courseId}_${ruleIdx}`]} label={<span className="flex items-center">Score <Tooltip text="The score value to compare against."><InformationCircleIcon className="h-3 w-3 ml-1"/></Tooltip></span>} type="number" step="any" value={fbRule.score_value} onChange={e => updateFeedbackRule(courseId, ruleIdx, 'score_value', e.target.value)} containerClassName="mb-0 col-span-2 md:col-span-1" labelClassName="text-xs" disabled={isSubmitting}/>
                       {/* @ts-ignore */}
                      <Select label={<span className="flex items-center">Compare <Tooltip text="How the student's score for this course relates to the 'Score Value'."><InformationCircleIcon className="h-3 w-3 ml-1"/></Tooltip></span>} options={comparisonOptions} value={fbRule.comparison} onChange={e => updateFeedbackRule(courseId, ruleIdx, 'comparison', e.target.value)} containerClassName="mb-0 col-span-2 md:col-span-1" labelClassName="text-xs" disabled={isSubmitting}/>
                       {/* @ts-ignore */}
                      <Textarea error={errors[`fb_text_${courseId}_${ruleIdx}`]} label={<span className="flex items-center">Feedback Text <Tooltip text="The feedback message to show if this rule matches."><InformationCircleIcon className="h-3 w-3 ml-1"/></Tooltip></span>} value={fbRule.feedback} onChange={e => updateFeedbackRule(courseId, ruleIdx, 'feedback', e.target.value)} rows={1} containerClassName="mb-0 col-span-5 md:col-span-3" labelClassName="text-xs" disabled={isSubmitting}/>
                      <Button type="button" variant="danger" size="xs" onClick={() => removeFeedbackRule(courseId, ruleIdx)} className="col-span-1 self-center mb-0 md:mt-4" disabled={isSubmitting}>Del</Button>
                    </div>
                  ))}
                  <Button type="button" variant="ghost" size="xs" onClick={() => addFeedbackRule(courseId)} className="mt-1" disabled={isSubmitting}>+ Add Feedback Rule</Button>
                </div>

                 <div className="pl-2 border-l-2 border-green-300">
                  <h5 className="text-sm font-medium text-gray-600 mb-1 flex items-center">
                    Outcome Rules (for this course)
                    <Tooltip text="Categorizes the student's performance for this course (e.g., 'Recommended to Take', 'Eligible for eRPL').">
                      <InformationCircleIcon className="h-4 w-4 text-gray-400 hover:text-gray-600 ml-1 cursor-pointer" />
                    </Tooltip>
                  </h5>
                  {(outcomeThresholds[courseId] || []).map((outRule, ruleIdx) => (
                    <div key={`out-${courseId}-${ruleIdx}`} className="grid grid-cols-1 md:grid-cols-7 gap-2 items-end p-2 border rounded bg-white my-1">
                       {/* @ts-ignore */}
                       <Input error={errors[`out_score_${courseId}_${ruleIdx}`]} label={<span className="flex items-center">Score <Tooltip text="The score value to compare against."><InformationCircleIcon className="h-3 w-3 ml-1"/></Tooltip></span>} type="number" step="any" value={outRule.score_value} onChange={e => updateOutcomeRule(courseId, ruleIdx, 'score_value', e.target.value)} containerClassName="mb-0 col-span-2 md:col-span-1" labelClassName="text-xs" disabled={isSubmitting}/>
                        {/* @ts-ignore */}
                       <Select label={<span className="flex items-center">Compare <Tooltip text="How the student's score for this course relates to the 'Score Value'."><InformationCircleIcon className="h-3 w-3 ml-1"/></Tooltip></span>} options={comparisonOptions} value={outRule.comparison} onChange={e => updateOutcomeRule(courseId, ruleIdx, 'comparison', e.target.value)} containerClassName="mb-0 col-span-2 md:col-span-1" labelClassName="text-xs" disabled={isSubmitting}/>
                        {/* @ts-ignore */}
                       <Select label={<span className="flex items-center">Outcome <Tooltip text="The outcome category if this rule matches."><InformationCircleIcon className="h-3 w-3 ml-1"/></Tooltip></span>} options={outcomeCategoryOptions} value={outRule.outcome} onChange={e => updateOutcomeRule(courseId, ruleIdx, 'outcome', e.target.value)} containerClassName="mb-0 col-span-5 md:col-span-3" labelClassName="text-xs" disabled={isSubmitting}/>
                      <Button type="button" variant="danger" size="xs" onClick={() => removeOutcomeRule(courseId, ruleIdx)} className="col-span-1 self-center mb-0 md:mt-4" disabled={isSubmitting}>Del</Button>
                    </div>
                  ))}
                  <Button type="button" variant="ghost" size="xs" onClick={() => addOutcomeRule(courseId)} className="mt-1" disabled={isSubmitting}>+ Add Outcome Rule</Button>
                </div>
              </div>
            );
          })}
        </fieldset>
      )}

      <div className="flex justify-end space-x-3 pt-4 border-t mt-6">
        <Button type="button" variant="ghost" onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button type="submit" variant="primary" isLoading={isSubmitting}>
          {initialData?.id ? 'Update Survey' : 'Create Survey'}
        </Button>
      </div>
    </form>
  );
};

export default SurveyForm;