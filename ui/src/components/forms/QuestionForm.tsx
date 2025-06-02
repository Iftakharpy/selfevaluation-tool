import React, { useState, useEffect, useCallback } from 'react';
import type { FormEvent } from 'react';
import type { QuestionFE, QuestionCreateFE, QuestionUpdateFE } from '../../types/questionTypes';
import type { Course } from '../../types/courseTypes';
import type { QCA, QCACreate, QCAUpdate, AnswerAssociationTypeEnumFE } from '../../types/qcaTypes';
import { AnswerTypeEnumFE, FeedbackComparisonEnumFE } from '../../types/surveyTypes';
import type { ScoreFeedbackItemFE } from '../../types/surveyTypes';

import Input from './Input';
import Textarea from './TextArea';
import Select from './Select';
import Button from './Button';
import { useNotifier } from '../../contexts/NotificationContext';

// API Services - assume these are available if running this component
import courseService from '../../services/courseService';
import qcaService from '../../services/qcaService';


interface QuestionFormProps {
  initialData?: QuestionFE | null; // Full question data for editing
  initialQcas?: QCA[]; // QCAs associated with this question when editing
  onSubmit: (data: QuestionCreateFE | QuestionUpdateFE, qcasToUpdate: Array<QCACreate | QCAUpdate & {id?: string}>, qcasToDelete: string[]) => Promise<void>;
  onCancel: () => void;
  isSubmitting: boolean;
  submitError?: string | null;
}

const answerTypeOptions = Object.values(AnswerTypeEnumFE).map(type => ({ value: type, label: type.replace(/_/g, ' ') }));
const comparisonOptions = Object.values(FeedbackComparisonEnumFE).map(comp => ({ value: comp, label: comp.toUpperCase() }));
const associationTypeOptions = [
    { value: 'positive', label: 'Positive Correlation' },
    { value: 'negative', label: 'Negative Correlation' },
];


const QuestionForm: React.FC<QuestionFormProps> = ({
  initialData,
  initialQcas = [],
  onSubmit,
  onCancel,
  isSubmitting,
  submitError,
}) => {
  const { addNotification } = useNotifier();

  // Core Question Fields
  const [title, setTitle] = useState('');
  const [details, setDetails] = useState('');
  const [answerType, setAnswerType] = useState<AnswerTypeEnumFE>(AnswerTypeEnumFE.MULTIPLE_CHOICE);
  
  // Dynamic fields for answer_options & scoring_rules
  const [options, setOptions] = useState<Array<{key: string, value: string}>>([{key: 'a', value: ''}]); // For MC/MS
  const [rangeMin, setRangeMin] = useState<number>(0);
  const [rangeMax, setRangeMax] = useState<number>(10);
  const [rangeStep, setRangeStep] = useState<number>(1);
  const [inputMaxLength, setInputMaxLength] = useState<number | undefined>(undefined);

  const [correctKey, setCorrectKey] = useState<string>(''); // For MC
  const [correctKeys, setCorrectKeys] = useState<string[]>([]); // For MS
  const [optionScores, setOptionScores] = useState<Record<string, number>>({}); // For MC/MS with specific scores

  const [expectedAnswers, setExpectedAnswers] = useState<Array<{text: string; score: number; case_sensitive: boolean}>>([{text: '', score: 1, case_sensitive: false}]); // For Input
  
  const [targetValue, setTargetValue] = useState<number>(5); // For Range
  const [scoreAtTarget, setScoreAtTarget] = useState<number>(10);
  const [scorePerDeviation, setScorePerDeviation] = useState<number>(-1);

  const [defaultFeedbacks, setDefaultFeedbacks] = useState<ScoreFeedbackItemFE[]>([]);
  
  // QCA Management
  const [allCourses, setAllCourses] = useState<Course[]>([]);
  const [associatedQCAs, setAssociatedQCAs] = useState<Array<QCACreate & { id?: string, courseName?: string }>>([]);
  const [qcasToDelete, setQcasToDelete] = useState<string[]>([]);


  const [errors, setErrors] = useState<Record<string, string>>({});

  const parseAndSetInitialData = useCallback(() => {
    setTitle(initialData?.title || '');
    setDetails(initialData?.details || '');
    const currentAnswerType = initialData?.answer_type || AnswerTypeEnumFE.MULTIPLE_CHOICE;
    setAnswerType(currentAnswerType);

    // Reset dynamic fields before setting
    setOptions([{key: 'a', value: ''}]);
    setRangeMin(0); setRangeMax(10); setRangeStep(1);
    setInputMaxLength(undefined);
    setCorrectKey(''); setCorrectKeys([]); setOptionScores({});
    setExpectedAnswers([{text: '', score: 1, case_sensitive: false}]);
    setTargetValue(5); setScoreAtTarget(10); setScorePerDeviation(-1);


    if (initialData?.answer_options) {
        if (currentAnswerType === AnswerTypeEnumFE.MULTIPLE_CHOICE || currentAnswerType === AnswerTypeEnumFE.MULTIPLE_SELECT) {
            setOptions(Object.entries(initialData.answer_options).map(([k, v]) => ({key: k, value: String(v)})));
        } else if (currentAnswerType === AnswerTypeEnumFE.RANGE) {
            setRangeMin(initialData.answer_options.min ?? 0);
            setRangeMax(initialData.answer_options.max ?? 10);
            setRangeStep(initialData.answer_options.step ?? 1);
        } else if (currentAnswerType === AnswerTypeEnumFE.INPUT) {
            setInputMaxLength(initialData.answer_options.max_length);
        }
    }

    if (initialData?.scoring_rules) {
        if (currentAnswerType === AnswerTypeEnumFE.MULTIPLE_CHOICE) {
            setCorrectKey(initialData.scoring_rules.correct_option_key || '');
            setOptionScores(initialData.scoring_rules.option_scores || {});
        } else if (currentAnswerType === AnswerTypeEnumFE.MULTIPLE_SELECT) {
            setCorrectKeys(initialData.scoring_rules.correct_option_keys || []);
            setOptionScores(initialData.scoring_rules.option_scores || {});
        } else if (currentAnswerType === AnswerTypeEnumFE.INPUT) {
            setExpectedAnswers(initialData.scoring_rules.expected_answers || [{text: '', score: 1, case_sensitive: false}]);
        } else if (currentAnswerType === AnswerTypeEnumFE.RANGE) {
            setTargetValue(initialData.scoring_rules.target_value ?? 5);
            setScoreAtTarget(initialData.scoring_rules.score_at_target ?? 10);
            setScorePerDeviation(initialData.scoring_rules.score_per_deviation_unit ?? -1);
        }
    }
    
    setDefaultFeedbacks(initialData?.default_feedbacks_on_score || []);
    
    // QCA
    const populatedInitialQcas = initialQcas.map(qca => ({
        ...qca,
        courseName: allCourses.find(c => c.id === qca.course_id)?.name || 'Unknown Course'
    }));
    setAssociatedQCAs(populatedInitialQcas);
    setQcasToDelete([]);

    setErrors({});
  }, [initialData, initialQcas, allCourses]);


  useEffect(() => {
    parseAndSetInitialData();
  }, [parseAndSetInitialData]);

  useEffect(() => { // Fetch courses for QCA selection
    courseService.listCourses()
      .then(setAllCourses)
      .catch(() => addNotification("Failed to load courses for QCA management.", "error"));
  }, [addNotification]);


  const validate = (): boolean => {
    // ... (Basic validation for title, etc.)
    return true; // Placeholder for more robust validation
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    let answer_options: Record<string, any> | null = null;
    let scoring_rules: Record<string, any> = {};

    switch(answerType) {
        case AnswerTypeEnumFE.MULTIPLE_CHOICE:
        case AnswerTypeEnumFE.MULTIPLE_SELECT:
            answer_options = options.reduce((acc, opt) => { acc[opt.key] = opt.value; return acc; }, {} as Record<string, string>);
            scoring_rules.option_scores = optionScores; // If using specific scores
            if(answerType === AnswerTypeEnumFE.MULTIPLE_CHOICE && correctKey) scoring_rules.correct_option_key = correctKey;
            if(answerType === AnswerTypeEnumFE.MULTIPLE_SELECT && correctKeys.length > 0) scoring_rules.correct_option_keys = correctKeys;
            break;
        case AnswerTypeEnumFE.INPUT:
            answer_options = inputMaxLength ? { max_length: inputMaxLength } : null;
            scoring_rules.expected_answers = expectedAnswers.filter(ea => ea.text.trim() !== '');
            break;
        case AnswerTypeEnumFE.RANGE:
            answer_options = { min: rangeMin, max: rangeMax, step: rangeStep };
            scoring_rules = { target_value: targetValue, score_at_target: scoreAtTarget, score_per_deviation_unit: scorePerDeviation };
            break;
    }

    const questionData: QuestionCreateFE | QuestionUpdateFE = {
      title,
      details: details.trim() || undefined,
      answer_type: answerType,
      answer_options,
      scoring_rules,
      default_feedbacks_on_score: defaultFeedbacks.length > 0 ? defaultFeedbacks : undefined,
    };

    const qcasToSubmit = associatedQCAs.map(({ courseName, ...qca }) => qca); // Remove courseName before submitting

    onSubmit(questionData, qcasToSubmit, qcasToDelete);
  };
  
  // ... (Feedback Management functions: addFeedbackItem, updateFeedbackItem, removeFeedbackItem - from previous correct version) ...
  const addFeedbackItem = () => setDefaultFeedbacks([...defaultFeedbacks, { score_value: 0, comparison: FeedbackComparisonEnumFE.EQ, feedback: '' }]);
  const updateFeedbackItem = (index: number, field: keyof ScoreFeedbackItemFE, value: string | number | FeedbackComparisonEnumFE) => {
    const newFeedbacks = [...defaultFeedbacks];
    const item = newFeedbacks[index];
    if (field === 'score_value') item[field] = Number(value);
    else if (field === 'comparison') item[field] = value as FeedbackComparisonEnumFE;
    else if (field === 'feedback') item[field] = value as string;
    setDefaultFeedbacks(newFeedbacks);
  };
  const removeFeedbackItem = (index: number) => setDefaultFeedbacks(defaultFeedbacks.filter((_, i) => i !== index));


  // === Answer Options/Rules specific handlers ===
  const handleOptionChange = (index: number, field: 'key' | 'value', value: string) => {
    const newOptions = [...options];
    newOptions[index][field] = value;
    setOptions(newOptions);
  };
  const addOption = () => setOptions([...options, {key: String.fromCharCode(97 + options.length), value: ''}]);
  const removeOption = (index: number) => {
    const keyToRemove = options[index].key;
    setOptions(options.filter((_, i) => i !== index));
    // Also remove from correctKey/correctKeys/optionScores if present
    if(correctKey === keyToRemove) setCorrectKey('');
    setCorrectKeys(prev => prev.filter(k => k !== keyToRemove));
    setOptionScores(prev => { const newScores = {...prev}; delete newScores[keyToRemove]; return newScores; });
  };

  const handleCorrectKeyChange = (key: string) => {
    if(answerType === AnswerTypeEnumFE.MULTIPLE_CHOICE) setCorrectKey(key);
    else if(answerType === AnswerTypeEnumFE.MULTIPLE_SELECT) {
        setCorrectKeys(prev => prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key]);
    }
  };
  const handleOptionScoreChange = (key: string, score: string) => {
    setOptionScores(prev => ({...prev, [key]: parseFloat(score) || 0}));
  };

  const handleExpectedAnswerChange = (index: number, field: keyof typeof expectedAnswers[0], value: string | number | boolean) => {
    const newAnswers = [...expectedAnswers];
    // @ts-expect-error - dynamic field assignment
    newAnswers[index][field] = field === 'score' ? Number(value) : value;
    setExpectedAnswers(newAnswers);
  };
  const addExpectedAnswer = () => setExpectedAnswers([...expectedAnswers, {text: '', score: 1, case_sensitive: false}]);
  const removeExpectedAnswer = (index: number) => setExpectedAnswers(expectedAnswers.filter((_, i) => i !== index));

  // === QCA Management Handlers ===
  const handleAddQCA = () => {
    // Add an empty QCA row for the user to fill
    setAssociatedQCAs(prev => [...prev, {
        course_id: '', 
        question_id: initialData?.id || '', // Will be set on submit if new question
        answer_association_type: 'positive' as AnswerAssociationTypeEnumFE, // Default
        feedbacks_based_on_score: [],
        courseName: 'Select Course'
    }]);
  };
  const handleQCAChange = (index: number, field: keyof (QCACreate & {courseName?: string}), value: string | ScoreFeedbackItemFE[]) => {
    const newQCAs = [...associatedQCAs];
    if (field === 'course_id') {
        // @ts-expect-error - dynamic field assignment
        newQCAs[index][field] = value;
        newQCAs[index].courseName = allCourses.find(c => c.id === value)?.name || 'Unknown Course';
    } else if (field === 'feedbacks_based_on_score') {
        newQCAs[index][field] = value as ScoreFeedbackItemFE[];
    }
     else {
        // @ts-expect-error - dynamic field assignment
        newQCAs[index][field] = value;
    }
    setAssociatedQCAs(newQCAs);
  };
  const handleRemoveQCA = (index: number) => {
    const qcaToRemove = associatedQCAs[index];
    if (qcaToRemove.id) { // If it's an existing QCA, mark for deletion
        setQcasToDelete(prev => [...prev, qcaToRemove.id!]);
    }
    setAssociatedQCAs(prev => prev.filter((_, i) => i !== index));
  };
  // Nested Feedback Management for QCA
    const addQcaFeedbackItem = (qcaIndex: number) => {
        const newQCAs = [...associatedQCAs];
        const qca = newQCAs[qcaIndex];
        qca.feedbacks_based_on_score = [...(qca.feedbacks_based_on_score || []), { score_value: 0, comparison: FeedbackComparisonEnumFE.EQ, feedback: '' }];
        setAssociatedQCAs(newQCAs);
    };
    const updateQcaFeedbackItem = (qcaIndex: number, fbIndex: number, field: keyof ScoreFeedbackItemFE, value: any) => {
        const newQCAs = [...associatedQCAs];
        const qca = newQCAs[qcaIndex];
        const feedbackItem = (qca.feedbacks_based_on_score || [])[fbIndex];
        if (feedbackItem) {
            if (field === 'score_value') feedbackItem[field] = Number(value);
            else if (field === 'comparison') feedbackItem[field] = value as FeedbackComparisonEnumFE;
            else if (field === 'feedback') feedbackItem[field] = value as string;
            setAssociatedQCAs(newQCAs);
        }
    };
    const removeQcaFeedbackItem = (qcaIndex: number, fbIndex: number) => {
        const newQCAs = [...associatedQCAs];
        const qca = newQCAs[qcaIndex];
        qca.feedbacks_based_on_score = (qca.feedbacks_based_on_score || []).filter((_, i) => i !== fbIndex);
        setAssociatedQCAs(newQCAs);
    };


  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-h-[75vh] overflow-y-auto p-2">
      {submitError && (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-3 mb-4" role="alert">
          <p className="font-bold">Submission Error</p>
          <p>{submitError}</p>
        </div>
      )}
       {errors.form && <p className="text-xs text-red-600">{errors.form}</p>}

      <Input label="Question Title" id="question-title" value={title} onChange={(e) => setTitle(e.target.value)} error={errors.title} disabled={isSubmitting} required />
      <Textarea label="Details (Optional)" id="question-details" value={details} onChange={(e) => setDetails(e.target.value)} rows={3} disabled={isSubmitting} />
      <Select label="Answer Type" id="question-answerType" options={answerTypeOptions} value={answerType} onChange={(e) => setAnswerType(e.target.value as AnswerTypeEnumFE)} error={errors.answerType} disabled={isSubmitting} required />
      
      {/* --- DYNAMIC OPTIONS UI --- */}
      <fieldset className="border p-4 rounded-md">
        <legend className="text-md font-medium text-gray-700 px-1">Answer Options & Scoring</legend>
        {(answerType === AnswerTypeEnumFE.MULTIPLE_CHOICE || answerType === AnswerTypeEnumFE.MULTIPLE_SELECT) && (
            <div className="space-y-3 mt-2">
                {options.map((opt, index) => (
                    <div key={index} className="flex items-center space-x-2 p-2 border rounded bg-gray-50">
                        <Input labelClassName="sr-only" label={`Option ${index+1} Key`} placeholder="Key (e.g. a)" value={opt.key} onChange={e => handleOptionChange(index, 'key', e.target.value)} containerClassName="mb-0 flex-shrink w-20" disabled={isSubmitting}/>
                        <Input labelClassName="sr-only" label={`Option ${index+1} Value`} placeholder="Option Text" value={opt.value} onChange={e => handleOptionChange(index, 'value', e.target.value)} containerClassName="mb-0 flex-grow" disabled={isSubmitting}/>
                        {answerType === AnswerTypeEnumFE.MULTIPLE_CHOICE && (
                            <input type="radio" name="correctKey" value={opt.key} checked={correctKey === opt.key} onChange={() => handleCorrectKeyChange(opt.key)} className="form-radio h-5 w-5 text-indigo-600" disabled={isSubmitting}/>
                        )}
                        {answerType === AnswerTypeEnumFE.MULTIPLE_SELECT && (
                             <input type="checkbox" value={opt.key} checked={correctKeys.includes(opt.key)} onChange={() => handleCorrectKeyChange(opt.key)} className="form-checkbox h-5 w-5 text-indigo-600 rounded" disabled={isSubmitting}/>
                        )}
                        <Input labelClassName="sr-only" label={`Score for ${opt.key}`} type="number" step="any" placeholder="Score" value={optionScores[opt.key] || ''} onChange={e => handleOptionScoreChange(opt.key, e.target.value)} containerClassName="mb-0 w-24" disabled={isSubmitting}/>
                        <Button type="button" variant="danger" size="xs" onClick={() => removeOption(index)} disabled={isSubmitting}>X</Button>
                    </div>
                ))}
                <Button type="button" variant="secondary" size="sm" onClick={addOption} disabled={isSubmitting}>Add Option</Button>
            </div>
        )}
        {answerType === AnswerTypeEnumFE.INPUT && (
            <div className="space-y-3 mt-2">
                <Input type="number" label="Max Length (Optional)" value={inputMaxLength || ''} onChange={e => setInputMaxLength(parseInt(e.target.value) || undefined)} disabled={isSubmitting} />
                <h5 className="text-sm font-medium mt-2">Expected Answers:</h5>
                {expectedAnswers.map((ea, index) => (
                    <div key={index} className="flex items-end space-x-2 p-2 border rounded bg-gray-50">
                        <Textarea labelClassName="sr-only" label="Expected Text" placeholder="Expected Text" value={ea.text} onChange={e => handleExpectedAnswerChange(index, 'text', e.target.value)} rows={1} containerClassName="mb-0 flex-grow" disabled={isSubmitting}/>
                        <Input labelClassName="sr-only" label="Score" type="number" step="any" placeholder="Score" value={ea.score} onChange={e => handleExpectedAnswerChange(index, 'score', e.target.value)} containerClassName="mb-0 w-24" disabled={isSubmitting}/>
                        <label className="flex items-center space-x-1 text-sm">
                            <input type="checkbox" checked={ea.case_sensitive} onChange={e => handleExpectedAnswerChange(index, 'case_sensitive', e.target.checked)} className="form-checkbox h-4 w-4 text-indigo-600 rounded" disabled={isSubmitting}/>
                            <span>Case Sensitive</span>
                        </label>
                        <Button type="button" variant="danger" size="xs" onClick={() => removeExpectedAnswer(index)} disabled={isSubmitting}>X</Button>
                    </div>
                ))}
                <Button type="button" variant="secondary" size="sm" onClick={addExpectedAnswer} disabled={isSubmitting}>Add Expected Answer</Button>
            </div>
        )}
        {answerType === AnswerTypeEnumFE.RANGE && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-2">
                <Input type="number" label="Min Value" value={rangeMin} onChange={e => setRangeMin(parseFloat(e.target.value))} disabled={isSubmitting}/>
                <Input type="number" label="Max Value" value={rangeMax} onChange={e => setRangeMax(parseFloat(e.target.value))} disabled={isSubmitting}/>
                <Input type="number" label="Step" value={rangeStep} onChange={e => setRangeStep(parseFloat(e.target.value))} disabled={isSubmitting}/>
                <Input type="number" label="Target Value (for scoring)" value={targetValue} onChange={e => setTargetValue(parseFloat(e.target.value))} disabled={isSubmitting}/>
                <Input type="number" label="Score at Target" step="any" value={scoreAtTarget} onChange={e => setScoreAtTarget(parseFloat(e.target.value))} disabled={isSubmitting}/>
                <Input type="number" label="Score Change per Deviation Unit" step="any" value={scorePerDeviation} onChange={e => setScorePerDeviation(parseFloat(e.target.value))} disabled={isSubmitting}/>
            </div>
        )}
      </fieldset>

      {/* Default Feedbacks (copied from previous version, assuming it's correct) */}
      <fieldset className="border p-4 rounded-md mt-4">
        <legend className="text-md font-medium text-gray-700 px-1">Default Feedback Rules (based on question score)</legend>
        {defaultFeedbacks.map((fb, index) => (
          <div key={index} className="p-3 border rounded-md space-y-2 bg-gray-50 my-2">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 items-end">
              <Input label={`Score Value ${index + 1}`} type="number" step="any" value={fb.score_value} onChange={(e) => updateFeedbackItem(index, 'score_value', e.target.value)} error={errors[`feedback_score_${index}`]} disabled={isSubmitting} containerClassName="mb-0" />
              <Select label="Comparison" options={comparisonOptions} value={fb.comparison} onChange={(e) => updateFeedbackItem(index, 'comparison', e.target.value as FeedbackComparisonEnumFE)} disabled={isSubmitting} containerClassName="mb-0" />
              <Button type="button" variant="danger" size="xs" onClick={() => removeFeedbackItem(index)} disabled={isSubmitting} className="self-end mb-0">Remove</Button>
            </div>
            <Textarea label={`Feedback Text ${index + 1}`} value={fb.feedback} onChange={(e) => updateFeedbackItem(index, 'feedback', e.target.value)} rows={2} error={errors[`feedback_text_${index}`]} disabled={isSubmitting} containerClassName="mb-0" />
          </div>
        ))}
        <Button type="button" variant="secondary" size="sm" onClick={addFeedbackItem} disabled={isSubmitting}>Add Default Feedback Rule</Button>
      </fieldset>

      {/* QCA Management Section */}
      <fieldset className="border p-4 rounded-md mt-4">
        <legend className="text-md font-medium text-gray-700 px-1">Course Associations (QCA)</legend>
        {associatedQCAs.map((qca, qcaIndex) => (
            <div key={qca.id || `new-${qcaIndex}`} className="p-3 border rounded-md space-y-3 bg-gray-50 my-2">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-center">
                    <Select
                        label={`Associated Course ${qcaIndex+1}`}
                        options={allCourses.map(c => ({ value: c.id, label: `${c.name} (${c.code})` }))}
                        value={qca.course_id}
                        onChange={e => handleQCAChange(qcaIndex, 'course_id', e.target.value)}
                        disabled={isSubmitting || !!qca.id} // Disable changing course for existing QCAs from this form for simplicity
                        placeholder="Select a course"
                        containerClassName="mb-0"
                    />
                     <Select
                        label="Answer Association Type"
                        options={associationTypeOptions}
                        value={qca.answer_association_type}
                        onChange={e => handleQCAChange(qcaIndex, 'answer_association_type', e.target.value as AnswerAssociationTypeEnumFE)}
                        disabled={isSubmitting}
                        containerClassName="mb-0"
                    />
                    <Button type="button" variant="danger" size="xs" onClick={() => handleRemoveQCA(qcaIndex)} disabled={isSubmitting} className="self-center mt-4 md:mt-0">Remove Association</Button>
                </div>
                {/* Per-QCA Feedbacks */}
                <div className="ml-4 border-l-2 pl-3 space-y-2">
                    <h5 className="text-sm font-medium text-gray-600">Course-Specific Feedback for "{qca.courseName || 'Selected Course'}"</h5>
                    {(qca.feedbacks_based_on_score || []).map((fb, fbIndex) => (
                        <div key={fbIndex} className="p-2 border rounded bg-white space-y-2">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 items-end">
                                <Input label="Score Value" type="number" step="any" value={fb.score_value} onChange={e => updateQcaFeedbackItem(qcaIndex, fbIndex, 'score_value', e.target.value)} disabled={isSubmitting} containerClassName="mb-0"/>
                                <Select label="Comparison" options={comparisonOptions} value={fb.comparison} onChange={e => updateQcaFeedbackItem(qcaIndex, fbIndex, 'comparison', e.target.value as FeedbackComparisonEnumFE)} disabled={isSubmitting} containerClassName="mb-0"/>
                                <Button type="button" variant="danger" size="xs" onClick={() => removeQcaFeedbackItem(qcaIndex, fbIndex)} disabled={isSubmitting} className="self-end mb-0">Remove</Button>
                            </div>
                            <Textarea label="Feedback Text" value={fb.feedback} onChange={e => updateQcaFeedbackItem(qcaIndex, fbIndex, 'feedback', e.target.value)} rows={1} disabled={isSubmitting} containerClassName="mb-0"/>
                        </div>
                    ))}
                    <Button type="button" variant="ghost" size="xs" onClick={() => addQcaFeedbackItem(qcaIndex)} disabled={isSubmitting || !qca.course_id}>Add Specific Feedback</Button>
                </div>
            </div>
        ))}
        <Button type="button" variant="secondary" size="sm" onClick={handleAddQCA} disabled={isSubmitting}>Associate with Another Course</Button>
      </fieldset>


      <div className="flex justify-end space-x-3 pt-4 border-t mt-6">
        <Button type="button" variant="ghost" onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button type="submit" variant="primary" isLoading={isSubmitting}>
          {initialData?.id ? 'Update Question & Associations' : 'Create Question & Associations'}
        </Button>
      </div>
    </form>
  );
};

export default QuestionForm;