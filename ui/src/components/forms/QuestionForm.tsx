// File: ui/src/components/forms/QuestionForm.tsx
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

import courseService from '../../services/courseService';
// qcaService import removed as it's not directly used for submission here but within QuestionPage
// import qcaService from '../../services/qcaService';


interface QuestionFormProps {
  initialData?: QuestionFE | null; 
  initialQcas?: QCA[]; 
  onSubmit: (data: QuestionCreateFE | QuestionUpdateFE, qcasToUpdate: Array<QCACreate | QCAUpdate & {id?: string}>, qcasToDelete: string[]) => Promise<void>;
  onCancel: () => void;
  isSubmitting: boolean;
  submitError?: string | null;
}

const answerTypeOptions = Object.values(AnswerTypeEnumFE).map(type => ({ value: type, label: type.replace(/_/g, ' ') }));
const comparisonOptions = Object.values(FeedbackComparisonEnumFE).map(comp => ({ value: comp, label: comp.toUpperCase() }));
const associationTypeOptions = [
    { value: 'positive' as AnswerAssociationTypeEnumFE, label: 'Positive Correlation' },
    { value: 'negative' as AnswerAssociationTypeEnumFE, label: 'Negative Correlation' },
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

  const [title, setTitle] = useState('');
  const [details, setDetails] = useState('');
  const [answerType, setAnswerType] = useState<AnswerTypeEnumFE>(AnswerTypeEnumFE.MULTIPLE_CHOICE);
  
  const [options, setOptions] = useState<Array<{key: string, value: string}>>([{key: 'a', value: ''}]);
  const [rangeMin, setRangeMin] = useState<number>(0);
  const [rangeMax, setRangeMax] = useState<number>(10);
  const [rangeStep, setRangeStep] = useState<number>(1);
  const [inputMaxLength, setInputMaxLength] = useState<number | undefined>(undefined);

  const [correctKey, setCorrectKey] = useState<string>('');
  const [correctKeys, setCorrectKeys] = useState<string[]>([]);
  const [optionScores, setOptionScores] = useState<Record<string, number>>({});

  const [expectedAnswers, setExpectedAnswers] = useState<Array<{text: string; score: number; case_sensitive: boolean}>>([{text: '', score: 10, case_sensitive: false}]); // Default score to 10
  
  const [targetValue, setTargetValue] = useState<number>(5);
  const [scoreAtTarget, setScoreAtTarget] = useState<number>(10); // Default to 10
  const [scorePerDeviation, setScorePerDeviation] = useState<number>(-1);

  const [defaultFeedbacks, setDefaultFeedbacks] = useState<ScoreFeedbackItemFE[]>([]);
  
  const [allCourses, setAllCourses] = useState<Course[]>([]);
  const [associatedQCAs, setAssociatedQCAs] = useState<Array<QCACreate & { id?: string, courseName?: string }>>([]);
  const [qcasToDelete, setQcasToDelete] = useState<string[]>([]);

  const [errors, setErrors] = useState<Record<string, string>>({});

  const parseAndSetInitialData = useCallback(() => {
    setTitle(initialData?.title || '');
    setDetails(initialData?.details || '');
    const currentAnswerType = initialData?.answer_type || AnswerTypeEnumFE.MULTIPLE_CHOICE;
    setAnswerType(currentAnswerType);

    setOptions(initialData?.answer_options && (currentAnswerType === AnswerTypeEnumFE.MULTIPLE_CHOICE || currentAnswerType === AnswerTypeEnumFE.MULTIPLE_SELECT)
        ? Object.entries(initialData.answer_options).map(([k, v]) => ({key: k, value: String(v)}))
        : [{key: 'a', value: ''}]
    );
    setRangeMin(initialData?.answer_options?.min as number ?? 0);
    setRangeMax(initialData?.answer_options?.max as number ?? 10);
    setRangeStep(initialData?.answer_options?.step as number ?? 1);
    setInputMaxLength(initialData?.answer_options?.max_length as number | undefined);

    setCorrectKey(initialData?.scoring_rules?.correct_option_key || '');
    setCorrectKeys(initialData?.scoring_rules?.correct_option_keys || []);
    setOptionScores(initialData?.scoring_rules?.option_scores || {});
    
    setExpectedAnswers(initialData?.scoring_rules?.expected_answers && initialData.scoring_rules.expected_answers.length > 0
        ? initialData.scoring_rules.expected_answers 
        : [{text: '', score: 10, case_sensitive: false}]
    );
    setTargetValue(initialData?.scoring_rules?.target_value ?? 5);
    setScoreAtTarget(initialData?.scoring_rules?.score_at_target ?? 10);
    setScorePerDeviation(initialData?.scoring_rules?.score_per_deviation_unit ?? -1);
    
    setDefaultFeedbacks(initialData?.default_feedbacks_on_score || []);
    
    const populatedInitialQcas = initialQcas.map(qca => ({
        ...qca,
        // Ensure all fields of QCACreate are present
        question_id: qca.question_id || initialData?.id || '', // Fallback for question_id
        answer_association_type: qca.answer_association_type || 'positive' as AnswerAssociationTypeEnumFE,
        feedbacks_based_on_score: qca.feedbacks_based_on_score || [],
        courseName: allCourses.find(c => c.id === qca.course_id)?.name || 'Unknown Course'
    }));
    setAssociatedQCAs(populatedInitialQcas);
    setQcasToDelete([]);
    setErrors({});
  }, [initialData, initialQcas, allCourses]);


  useEffect(() => {
    parseAndSetInitialData();
  }, [parseAndSetInitialData]);

  useEffect(() => { 
    courseService.listCourses()
      .then(setAllCourses)
      .catch(() => addNotification("Failed to load courses for QCA management.", "error"));
  }, [addNotification]);

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (!title.trim()) newErrors.title = "Question title is required.";
    
    // Add more specific validations based on answer type
    if (answerType === AnswerTypeEnumFE.MULTIPLE_CHOICE && !correctKey && Object.keys(optionScores).length === 0) {
        newErrors.scoring = "For Multiple Choice, either a 'correct option' or 'specific scores per option' must be defined.";
    }
    if (answerType === AnswerTypeEnumFE.MULTIPLE_SELECT && correctKeys.length === 0 && Object.keys(optionScores).length === 0) {
        newErrors.scoring = "For Multiple Select, either 'correct options' or 'specific scores per option' must be defined.";
    }
    if (answerType === AnswerTypeEnumFE.INPUT && expectedAnswers.every(ea => !ea.text.trim())) {
        newErrors.scoring = "For Input type, at least one expected answer text must be provided if defining expected answers.";
    }
    if (answerType === AnswerTypeEnumFE.RANGE && (rangeMin >= rangeMax)) {
        newErrors.range = "For Range type, Min value must be less than Max value.";
    }

    // Validate default feedbacks
    defaultFeedbacks.forEach((fb, index) => {
        if(isNaN(fb.score_value)) newErrors[`df_score_${index}`] = "Score value must be a number.";
        if(!fb.feedback.trim()) newErrors[`df_text_${index}`] = "Feedback text cannot be empty.";
    });

    // Validate QCA feedbacks
    associatedQCAs.forEach((qca, qcaIndex) => {
        if(!qca.course_id) newErrors[`qca_course_${qcaIndex}`] = "A course must be selected for each association.";
        (qca.feedbacks_based_on_score || []).forEach((fb, fbIndex) => {
            if(isNaN(fb.score_value)) newErrors[`qca_fb_score_${qcaIndex}_${fbIndex}`] = "Score value must be a number.";
            if(!fb.feedback.trim()) newErrors[`qca_fb_text_${qcaIndex}_${fbIndex}`] = "Feedback text cannot be empty.";
        });
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) {
        addNotification("Please correct the errors in the form before submitting.", "error");
        return;
    }

    let calculated_answer_options: Record<string, any> | null = null;
    let calculated_scoring_rules: Record<string, any> = {};

    switch(answerType) {
        case AnswerTypeEnumFE.MULTIPLE_CHOICE:
        case AnswerTypeEnumFE.MULTIPLE_SELECT:
            calculated_answer_options = options.reduce((acc, opt) => { 
                if(opt.key.trim() && opt.value.trim()) acc[opt.key.trim()] = opt.value.trim(); 
                return acc; 
            }, {} as Record<string, string>);
            if(Object.keys(calculated_answer_options).length === 0) calculated_answer_options = null; // Don't send empty options

            if(Object.keys(optionScores).length > 0) calculated_scoring_rules.option_scores = optionScores;
            if(answerType === AnswerTypeEnumFE.MULTIPLE_CHOICE && correctKey.trim()) calculated_scoring_rules.correct_option_key = correctKey.trim();
            // Ensure score_if_correct is present if correct_option_key is used and no option_scores
            if (calculated_scoring_rules.correct_option_key && !calculated_scoring_rules.option_scores) {
                calculated_scoring_rules.score_if_correct = 10; // Default to 10 if using simple correct/incorrect
                calculated_scoring_rules.score_if_incorrect = 0;
            }
            if(answerType === AnswerTypeEnumFE.MULTIPLE_SELECT && correctKeys.length > 0) calculated_scoring_rules.correct_option_keys = correctKeys;
             // Ensure score_per_correct is present if correct_option_keys is used and no option_scores
            if (calculated_scoring_rules.correct_option_keys && !calculated_scoring_rules.option_scores) {
                calculated_scoring_rules.score_per_correct = Math.floor(10 / correctKeys.length) || 1; // Distribute 10 or default to 1
                calculated_scoring_rules.penalty_per_incorrect = 0; // Default penalty
            }
            break;
        case AnswerTypeEnumFE.INPUT:
            calculated_answer_options = inputMaxLength ? { max_length: inputMaxLength } : null;
            calculated_scoring_rules.expected_answers = expectedAnswers.filter(ea => ea.text.trim() !== '');
            // Ensure default_incorrect_score is set if expected_answers are used
            if (calculated_scoring_rules.expected_answers.length > 0 && calculated_scoring_rules.default_incorrect_score === undefined) {
                calculated_scoring_rules.default_incorrect_score = 0;
            }
            break;
        case AnswerTypeEnumFE.RANGE:
            calculated_answer_options = { min: rangeMin, max: rangeMax, step: rangeStep };
            calculated_scoring_rules = { target_value: targetValue, score_at_target: scoreAtTarget, score_per_deviation_unit: scorePerDeviation };
            break;
    }

    const questionData: QuestionCreateFE | QuestionUpdateFE = {
      title: title.trim(),
      details: details.trim() || undefined,
      answer_type: answerType,
      answer_options: calculated_answer_options,
      scoring_rules: calculated_scoring_rules,
      default_feedbacks_on_score: defaultFeedbacks.filter(fb => fb.feedback.trim()).length > 0 ? defaultFeedbacks.filter(fb => fb.feedback.trim()) : undefined,
    };

    const qcasToSubmit = associatedQCAs
        .filter(qca => qca.course_id) // Only submit QCAs with a selected course
        .map(({ courseName, ...qca }) => ({
            ...qca,
            feedbacks_based_on_score: (qca.feedbacks_based_on_score || []).filter(fb => fb.feedback.trim())
        }));

    onSubmit(questionData, qcasToSubmit, qcasToDelete);
  };
  
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

  const handleOptionChange = (index: number, field: 'key' | 'value', value: string) => {
    const newOptions = [...options];
    newOptions[index][field] = value;
    setOptions(newOptions);
  };
  const addOption = () => {
    // Generate next letter key (a, b, c, ...)
    const nextKey = options.length > 0 ? String.fromCharCode(options[options.length - 1].key.charCodeAt(0) + 1) : 'a';
    setOptions([...options, {key: nextKey, value: ''}]);
  };
  const removeOption = (index: number) => {
    const keyToRemove = options[index].key;
    setOptions(options.filter((_, i) => i !== index));
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
  const handleOptionScoreChange = (key: string, scoreStr: string) => {
    const score = parseFloat(scoreStr);
    if (!isNaN(score)) {
        setOptionScores(prev => ({...prev, [key]: Math.max(0, Math.min(10, score)) })); // Clamp between 0-10
    } else if (scoreStr === '') {
        setOptionScores(prev => { const newScores = {...prev}; delete newScores[key]; return newScores; });
    }
  };

  const handleExpectedAnswerChange = (index: number, field: keyof typeof expectedAnswers[0], value: string | number | boolean) => {
    const newAnswers = [...expectedAnswers];
    if (field === 'score') {
        // @ts-expect-error
        newAnswers[index][field] = Math.max(0, Math.min(10, Number(value))); // Clamp score
    } else {
        // @ts-expect-error
        newAnswers[index][field] = value;
    }
    setExpectedAnswers(newAnswers);
  };
  const addExpectedAnswer = () => setExpectedAnswers([...expectedAnswers, {text: '', score: 10, case_sensitive: false}]);
  const removeExpectedAnswer = (index: number) => setExpectedAnswers(expectedAnswers.filter((_, i) => i !== index));

  const handleAddQCA = () => {
    setAssociatedQCAs(prev => [...prev, {
        course_id: '', 
        question_id: initialData?.id || '', 
        answer_association_type: 'positive' as AnswerAssociationTypeEnumFE,
        feedbacks_based_on_score: [],
        courseName: 'Select Course'
    }]);
  };
  const handleQCAChange = (index: number, field: keyof (QCACreate & {courseName?: string, id?:string}), value: string | ScoreFeedbackItemFE[] | AnswerAssociationTypeEnumFE) => {
    const newQCAs = [...associatedQCAs];
    const qcaItem = { ...newQCAs[index] }; // Work on a copy

    if (field === 'course_id') {
        qcaItem.course_id = value as string;
        qcaItem.courseName = allCourses.find(c => c.id === value)?.name || 'Unknown Course';
    } else if (field === 'feedbacks_based_on_score') {
        qcaItem.feedbacks_based_on_score = value as ScoreFeedbackItemFE[];
    } else if (field === 'answer_association_type') {
        qcaItem.answer_association_type = value as AnswerAssociationTypeEnumFE;
    }
    newQCAs[index] = qcaItem;
    setAssociatedQCAs(newQCAs);
  };
  const handleRemoveQCA = (index: number) => {
    const qcaToRemove = associatedQCAs[index];
    if (qcaToRemove.id) { 
        setQcasToDelete(prev => [...prev, qcaToRemove.id!]);
    }
    setAssociatedQCAs(prev => prev.filter((_, i) => i !== index));
  };
    const addQcaFeedbackItem = (qcaIndex: number) => {
        const newQCAs = [...associatedQCAs];
        const qca = { ...newQCAs[qcaIndex] };
        qca.feedbacks_based_on_score = [...(qca.feedbacks_based_on_score || []), { score_value: 0, comparison: FeedbackComparisonEnumFE.EQ, feedback: '' }];
        newQCAs[qcaIndex] = qca;
        setAssociatedQCAs(newQCAs);
    };
    const updateQcaFeedbackItem = (qcaIndex: number, fbIndex: number, field: keyof ScoreFeedbackItemFE, value: any) => {
        const newQCAs = [...associatedQCAs];
        const qca = { ...newQCAs[qcaIndex] };
        const feedbackItem = { ...(qca.feedbacks_based_on_score || [])[fbIndex] };
        if (feedbackItem) {
            if (field === 'score_value') feedbackItem[field] = Number(value);
            else if (field === 'comparison') feedbackItem[field] = value as FeedbackComparisonEnumFE;
            else if (field === 'feedback') feedbackItem[field] = value as string;
            
            const updatedFeedbacks = [...(qca.feedbacks_based_on_score || [])];
            updatedFeedbacks[fbIndex] = feedbackItem;
            qca.feedbacks_based_on_score = updatedFeedbacks;
            newQCAs[qcaIndex] = qca;
            setAssociatedQCAs(newQCAs);
        }
    };
    const removeQcaFeedbackItem = (qcaIndex: number, fbIndex: number) => {
        const newQCAs = [...associatedQCAs];
        const qca = { ...newQCAs[qcaIndex] };
        qca.feedbacks_based_on_score = (qca.feedbacks_based_on_score || []).filter((_, i) => i !== fbIndex);
        newQCAs[qcaIndex] = qca;
        setAssociatedQCAs(newQCAs);
    };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-h-[75vh] overflow-y-auto p-2 pr-4"> {/* Added pr-4 for scrollbar */}
      {submitError && (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-3 mb-4" role="alert">
          <p className="font-bold">Submission Error</p>
          <p>{submitError}</p>
        </div>
      )}
       {Object.keys(errors).length > 0 && !errors.form && (
        <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-3 mb-4" role="alert">
            <p className="font-bold">Please review the form</p>
            <p>Some fields have errors or require attention.</p>
        </div>
       )}
       {errors.form && <p className="text-sm text-red-600 bg-red-100 p-2 rounded">{errors.form}</p>}


      <Input label="Question Title" id="question-title" value={title} onChange={(e) => setTitle(e.target.value)} error={errors.title} disabled={isSubmitting} required />
      <Textarea label="Details (Optional)" id="question-details" value={details} onChange={(e) => setDetails(e.target.value)} rows={3} disabled={isSubmitting} />
      <Select label="Answer Type" id="question-answerType" options={answerTypeOptions} value={answerType} 
        onChange={(e) => {
            setAnswerType(e.target.value as AnswerTypeEnumFE);
            // Reset specific fields when type changes to avoid invalid states
            setCorrectKey(''); setCorrectKeys([]); setOptionScores({});
            setExpectedAnswers([{text: '', score: 10, case_sensitive: false}]);
            setErrors(prev => ({...prev, scoring: undefined})); // Clear general scoring error
        }} 
        error={errors.answerType} disabled={isSubmitting} required />
      
      <fieldset className="border p-4 rounded-md">
        <legend className="text-md font-medium text-gray-700 px-1">Answer Options & Scoring</legend>
        <p className="text-xs text-gray-500 mb-2 italic">Define rules so each question scores between 0-10. Max 10 points per question.</p>
        {errors.scoring && <p className="text-xs text-red-600 mb-2">{errors.scoring}</p>}

        {(answerType === AnswerTypeEnumFE.MULTIPLE_CHOICE || answerType === AnswerTypeEnumFE.MULTIPLE_SELECT) && (
            <div className="space-y-3 mt-2">
                {options.map((opt, index) => (
                    <div key={index} className="flex items-center space-x-2 p-2 border rounded bg-gray-50">
                        <Input labelClassName="sr-only" label={`Option ${index+1} Key`} placeholder="Key (e.g. a)" value={opt.key} onChange={e => handleOptionChange(index, 'key', e.target.value)} containerClassName="mb-0 flex-shrink w-20" error={errors[`opt_key_${index}`]} disabled={isSubmitting}/>
                        <Input labelClassName="sr-only" label={`Option ${index+1} Value`} placeholder="Option Text" value={opt.value} onChange={e => handleOptionChange(index, 'value', e.target.value)} containerClassName="mb-0 flex-grow" error={errors[`opt_val_${index}`]} disabled={isSubmitting}/>
                        {answerType === AnswerTypeEnumFE.MULTIPLE_CHOICE && (
                            <input title="Mark as correct" type="radio" name="correctKey" value={opt.key} checked={correctKey === opt.key} onChange={() => handleCorrectKeyChange(opt.key)} className="form-radio h-5 w-5 text-indigo-600" disabled={isSubmitting}/>
                        )}
                        {answerType === AnswerTypeEnumFE.MULTIPLE_SELECT && (
                             <input title="Mark as correct" type="checkbox" value={opt.key} checked={correctKeys.includes(opt.key)} onChange={() => handleCorrectKeyChange(opt.key)} className="form-checkbox h-5 w-5 text-indigo-600 rounded" disabled={isSubmitting}/>
                        )}
                        <Input labelClassName="sr-only" label={`Score for ${opt.key}`} type="number" step="any" placeholder="Score (0-10)" value={optionScores[opt.key] ?? ''} onChange={e => handleOptionScoreChange(opt.key, e.target.value)} containerClassName="mb-0 w-28" error={errors[`opt_score_${opt.key}`]} disabled={isSubmitting}/>
                        <Button type="button" variant="danger" size="xs" onClick={() => removeOption(index)} disabled={isSubmitting || options.length <=1 }>X</Button>
                    </div>
                ))}
                <Button type="button" variant="secondary" size="sm" onClick={addOption} disabled={isSubmitting}>Add Option</Button>
            </div>
        )}
        {answerType === AnswerTypeEnumFE.INPUT && (
            <div className="space-y-3 mt-2">
                <Input type="number" label="Max Length (Optional)" value={inputMaxLength || ''} onChange={e => setInputMaxLength(parseInt(e.target.value) || undefined)} disabled={isSubmitting} />
                <h5 className="text-sm font-medium mt-2">Expected Answers & Scores (0-10):</h5>
                {expectedAnswers.map((ea, index) => (
                    <div key={index} className="flex items-end space-x-2 p-2 border rounded bg-gray-50">
                        <Textarea labelClassName="sr-only" label="Expected Text" placeholder="Expected Text" value={ea.text} onChange={e => handleExpectedAnswerChange(index, 'text', e.target.value)} rows={1} containerClassName="mb-0 flex-grow" error={errors[`exp_ans_text_${index}`]} disabled={isSubmitting}/>
                        <Input labelClassName="sr-only" label="Score" type="number" step="any" placeholder="Score (0-10)" value={ea.score} onChange={e => handleExpectedAnswerChange(index, 'score', e.target.value)} containerClassName="mb-0 w-28" error={errors[`exp_ans_score_${index}`]} disabled={isSubmitting}/>
                        <label className="flex items-center space-x-1 text-sm">
                            <input type="checkbox" checked={ea.case_sensitive} onChange={e => handleExpectedAnswerChange(index, 'case_sensitive', e.target.checked)} className="form-checkbox h-4 w-4 text-indigo-600 rounded" disabled={isSubmitting}/>
                            <span>Case Sensitive</span>
                        </label>
                        <Button type="button" variant="danger" size="xs" onClick={() => removeExpectedAnswer(index)} disabled={isSubmitting || expectedAnswers.length <= 1}>X</Button>
                    </div>
                ))}
                <Button type="button" variant="secondary" size="sm" onClick={addExpectedAnswer} disabled={isSubmitting}>Add Expected Answer</Button>
            </div>
        )}
        {answerType === AnswerTypeEnumFE.RANGE && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-2">
                <Input type="number" label="Min Value" value={rangeMin} onChange={e => setRangeMin(parseFloat(e.target.value))} error={errors.range_min} disabled={isSubmitting}/>
                <Input type="number" label="Max Value" value={rangeMax} onChange={e => setRangeMax(parseFloat(e.target.value))} error={errors.range_max || errors.range} disabled={isSubmitting}/>
                <Input type="number" label="Step" value={rangeStep} onChange={e => setRangeStep(parseFloat(e.target.value))} error={errors.range_step} disabled={isSubmitting}/>
                <Input type="number" label="Target Value (for scoring)" value={targetValue} onChange={e => setTargetValue(parseFloat(e.target.value))} error={errors.range_target} disabled={isSubmitting}/>
                <Input type="number" label="Score at Target (0-10)" step="any" max="10" value={scoreAtTarget} onChange={e => setScoreAtTarget(Math.max(0, Math.min(10, parseFloat(e.target.value))))} error={errors.range_score_target} disabled={isSubmitting}/>
                <Input type="number" label="Score Change per Deviation" step="any" value={scorePerDeviation} onChange={e => setScorePerDeviation(parseFloat(e.target.value))} error={errors.range_score_dev} disabled={isSubmitting}/>
            </div>
        )}
      </fieldset>

      <fieldset className="border p-4 rounded-md mt-4">
        <legend className="text-md font-medium text-gray-700 px-1">Default Feedback Rules (based on question score 0-10)</legend>
        {defaultFeedbacks.map((fb, index) => (
          <div key={index} className="p-3 border rounded-md space-y-2 bg-gray-50 my-2">
            <div className="grid grid-cols-1 md:grid-cols-7 gap-2 items-end">
              <Input label="If Score Is" type="number" step="any" value={fb.score_value} onChange={(e) => updateFeedbackItem(index, 'score_value', e.target.value)} error={errors[`df_score_${index}`]} disabled={isSubmitting} containerClassName="mb-0 col-span-2 md:col-span-1" labelClassName="text-xs" />
              <Select label="Comparison" options={comparisonOptions} value={fb.comparison} onChange={(e) => updateFeedbackItem(index, 'comparison', e.target.value as FeedbackComparisonEnumFE)} disabled={isSubmitting} containerClassName="mb-0 col-span-2 md:col-span-1" labelClassName="text-xs" />
              <Textarea label="Feedback Text" value={fb.feedback} onChange={(e) => updateFeedbackItem(index, 'feedback', e.target.value)} rows={1} error={errors[`df_text_${index}`]} disabled={isSubmitting} containerClassName="mb-0 col-span-full md:col-span-3" labelClassName="text-xs" />
              <Button type="button" variant="danger" size="xs" onClick={() => removeFeedbackItem(index)} disabled={isSubmitting} className="col-span-1 self-center mb-0 md:mt-4">Remove</Button>
            </div>
          </div>
        ))}
        <Button type="button" variant="secondary" size="sm" onClick={addFeedbackItem} disabled={isSubmitting}>Add Default Feedback Rule</Button>
      </fieldset>

      <fieldset className="border p-4 rounded-md mt-4">
        <legend className="text-md font-medium text-gray-700 px-1">Course Associations & Specific Feedback</legend>
        {associatedQCAs.map((qca, qcaIndex) => (
            <div key={qca.id || `new-${qcaIndex}`} className="p-3 border rounded-md space-y-3 bg-gray-50 my-2">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-center">
                    <Select
                        label={`Course ${qcaIndex+1}`}
                        options={allCourses.map(c => ({ value: c.id, label: `${c.name} (${c.code})` }))}
                        value={qca.course_id}
                        onChange={e => handleQCAChange(qcaIndex, 'course_id', e.target.value as string)}
                        disabled={isSubmitting || !!qca.id} 
                        placeholder="Select a course"
                        containerClassName="mb-0"
                        error={errors[`qca_course_${qcaIndex}`]}
                    />
                     <Select
                        label="Answer Correlation"
                        options={associationTypeOptions}
                        value={qca.answer_association_type}
                        onChange={e => handleQCAChange(qcaIndex, 'answer_association_type', e.target.value as AnswerAssociationTypeEnumFE)}
                        disabled={isSubmitting}
                        containerClassName="mb-0"
                    />
                    <Button type="button" variant="danger" size="xs" onClick={() => handleRemoveQCA(qcaIndex)} disabled={isSubmitting} className="self-center mt-4 md:mt-0">Remove Association</Button>
                </div>
                <div className="ml-4 border-l-2 pl-3 space-y-2">
                    <h5 className="text-sm font-medium text-gray-600">Course-Specific Feedback for "{qca.courseName || 'Selected Course'}" (score 0-10)</h5>
                    {(qca.feedbacks_based_on_score || []).map((fb, fbIndex) => (
                        <div key={fbIndex} className="p-2 border rounded bg-white space-y-1 my-1">
                            <div className="grid grid-cols-1 md:grid-cols-7 gap-2 items-end">
                                <Input label="If Score Is" type="number" step="any" value={fb.score_value} onChange={e => updateQcaFeedbackItem(qcaIndex, fbIndex, 'score_value', e.target.value)} error={errors[`qca_fb_score_${qcaIndex}_${fbIndex}`]} disabled={isSubmitting} containerClassName="mb-0 col-span-2 md:col-span-1" labelClassName="text-xs"/>
                                <Select label="Comparison" options={comparisonOptions} value={fb.comparison} onChange={e => updateQcaFeedbackItem(qcaIndex, fbIndex, 'comparison', e.target.value as FeedbackComparisonEnumFE)} disabled={isSubmitting} containerClassName="mb-0 col-span-2 md:col-span-1" labelClassName="text-xs"/>
                                <Textarea label="Feedback Text" value={fb.feedback} onChange={e => updateQcaFeedbackItem(qcaIndex, fbIndex, 'feedback', e.target.value)} rows={1} error={errors[`qca_fb_text_${qcaIndex}_${fbIndex}`]} disabled={isSubmitting} containerClassName="mb-0 col-span-full md:col-span-3" labelClassName="text-xs"/>
                                <Button type="button" variant="danger" size="xs" onClick={() => removeQcaFeedbackItem(qcaIndex, fbIndex)} disabled={isSubmitting} className="col-span-1 self-center mb-0 md:mt-4">Remove</Button>
                            </div>
                        </div>
                    ))}
                    <Button type="button" variant="ghost" size="xs" onClick={() => addQcaFeedbackItem(qcaIndex)} disabled={isSubmitting || !qca.course_id}>+ Add Specific Feedback Rule</Button>
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