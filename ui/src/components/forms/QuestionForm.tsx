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
import Tooltip from '../common/Tooltip'; 
import { InformationCircleIcon } from '../icons/InformationCircleIcon'; 

import courseService from '../../services/courseService';
import qcaService from '../../services/qcaService';


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

  const [expectedAnswers, setExpectedAnswers] = useState<Array<{text: string; score: number; case_sensitive: boolean}>>([{text: '', score: 1, case_sensitive: false}]);
  
  const [targetValue, setTargetValue] = useState<number>(5);
  const [scoreAtTarget, setScoreAtTarget] = useState<number>(10);
  const [scorePerDeviation, setScorePerDeviation] = useState<number>(-1);

  const [defaultFeedbacks, setDefaultFeedbacks] = useState<ScoreFeedbackItemFE[]>([]);
  
  const [allCourses, setAllCourses] = useState<Course[]>([]);
  const [associatedQCAs, setAssociatedQCAs] = useState<Array<QCACreate & { id?: string, courseName?: string }>>([]);
  const [qcasToDelete, setQcasToDelete] = useState<string[]>([]);

  const [localFormError, setLocalFormError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const parseAndSetInitialData = useCallback(() => {
    setTitle(initialData?.title || '');
    setDetails(initialData?.details || '');
    const currentAnswerType = initialData?.answer_type || AnswerTypeEnumFE.MULTIPLE_CHOICE;
    setAnswerType(currentAnswerType);

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
    
    const populatedInitialQcas = initialQcas.map(qca => ({
        ...qca, 
        question_id: initialData?.id || qca.question_id, 
        courseName: allCourses.find(c => c.id === qca.course_id)?.name || 'Unknown Course'
    }));
    setAssociatedQCAs(populatedInitialQcas);
    setQcasToDelete([]);

    setFieldErrors({});
    setLocalFormError(null);
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
    const newFieldErrors: Record<string, string> = {};
    if (!title.trim()) newFieldErrors.title = "Question title is required.";

    associatedQCAs.forEach((qca, index) => {
        if (!qca.course_id) {
            newFieldErrors[`qca_course_${index}`] = "Course must be selected for this association.";
        }
    });

    setFieldErrors(newFieldErrors);
    if (Object.keys(newFieldErrors).length > 0) {
        setLocalFormError("Please correct the errors highlighted in the form.");
        return false;
    }
    setLocalFormError(null);
    return true;
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setLocalFormError(null); 
    setFieldErrors({}); 

    if (!validate()) return;

    let answer_options_payload: Record<string, any> | null = null;
    let scoring_rules_payload: Record<string, any> = {};

    switch(answerType) {
        case AnswerTypeEnumFE.MULTIPLE_CHOICE:
        case AnswerTypeEnumFE.MULTIPLE_SELECT:
            answer_options_payload = options.reduce((acc, opt) => { 
                if(opt.key.trim() && opt.value.trim()) acc[opt.key.trim()] = opt.value.trim(); 
                return acc; 
            }, {} as Record<string, string>);
            
            if (Object.keys(optionScores).length > 0) {
                scoring_rules_payload.option_scores = optionScores;
            } else if (answerType === AnswerTypeEnumFE.MULTIPLE_CHOICE && correctKey) {
                scoring_rules_payload.correct_option_key = correctKey;
                scoring_rules_payload.score_if_correct = 10; 
                scoring_rules_payload.score_if_incorrect = 0;
            } else if (answerType === AnswerTypeEnumFE.MULTIPLE_SELECT && correctKeys.length > 0) {
                scoring_rules_payload.correct_option_keys = correctKeys;
                scoring_rules_payload.score_per_correct = correctKeys.length > 0 ? (10 / correctKeys.length) : 0; 
                scoring_rules_payload.penalty_per_incorrect = 0;
            }
            break;
        case AnswerTypeEnumFE.INPUT:
            answer_options_payload = inputMaxLength ? { max_length: inputMaxLength } : null;
            scoring_rules_payload.expected_answers = expectedAnswers.filter(ea => ea.text.trim() !== '');
            if (!scoring_rules_payload.expected_answers || scoring_rules_payload.expected_answers.length === 0) {
                scoring_rules_payload.default_incorrect_score = 0; 
            }
            break;
        case AnswerTypeEnumFE.RANGE:
            answer_options_payload = { min: rangeMin, max: rangeMax, step: rangeStep };
            scoring_rules_payload = { target_value: targetValue, score_at_target: scoreAtTarget, score_per_deviation_unit: scorePerDeviation };
            break;
    }

    const questionData: QuestionCreateFE | QuestionUpdateFE = {
      title,
      details: details.trim() || undefined,
      answer_type: answerType,
      answer_options: Object.keys(answer_options_payload || {}).length > 0 ? answer_options_payload : undefined,
      scoring_rules: scoring_rules_payload,
      default_feedbacks_on_score: defaultFeedbacks.length > 0 ? defaultFeedbacks : undefined,
    };

    const qcasToSubmit = associatedQCAs
      .filter(qca => qca.course_id) 
      .map(({ courseName, ...qca }) => qca);

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
  const addOption = () => setOptions([...options, {key: String.fromCharCode(97 + options.length), value: ''}]);
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
  const handleOptionScoreChange = (key: string, score: string) => {
    setOptionScores(prev => ({...prev, [key]: parseFloat(score) || 0}));
  };

  const handleExpectedAnswerChange = (index: number, field: keyof typeof expectedAnswers[0], value: string | number | boolean) => {
    const newAnswers = [...expectedAnswers];
    // @ts-expect-error - dynamic field assignment for varying types
    newAnswers[index][field] = field === 'score' ? Number(value) : value;
    setExpectedAnswers(newAnswers);
  };
  const addExpectedAnswer = () => setExpectedAnswers([...expectedAnswers, {text: '', score: 1, case_sensitive: false}]);
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
        // @ts-expect-error - dynamic field assignment for varying types
        newQCAs[index][field] = value;
    }
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

  const displayError = submitError || localFormError;

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-h-[75vh] overflow-y-auto p-2">
      {displayError && (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-3 mb-4" role="alert">
          <p className="font-bold">Error</p>
          <p>{displayError}</p>
        </div>
      )}
      {Object.keys(fieldErrors).length > 0 && !displayError && (
         <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-3 mb-4" role="alert">
            <p className="font-bold">Please check the following:</p>
            <ul className="list-disc list-inside">
                {Object.entries(fieldErrors).map(([key, message]) => (
                    <li key={key}>{message}</li>
                ))}
            </ul>
         </div>
      )}

      <Input label="Question Title" id="question-title" value={title} onChange={(e) => setTitle(e.target.value)} error={fieldErrors.title} disabled={isSubmitting} required />
      <Textarea label="Details (Optional)" id="question-details" value={details} onChange={(e) => setDetails(e.target.value)} rows={3} disabled={isSubmitting} />
      <Select label="Answer Type" id="question-answerType" options={answerTypeOptions} value={answerType} onChange={(e) => setAnswerType(e.target.value as AnswerTypeEnumFE)} error={fieldErrors.answerType} disabled={isSubmitting} required />
      
      <fieldset className="border p-4 rounded-md">
        <legend className="text-md font-medium text-gray-700 px-1 flex items-center">
          Answer Options & Scoring
          <Tooltip text="Define options for answers and rules for scoring. Individual question scores are capped at 10 points by the system during survey taking.">
            <InformationCircleIcon className="h-5 w-5 text-gray-400 hover:text-gray-600 ml-1 cursor-pointer" />
          </Tooltip>
        </legend>
        {(answerType === AnswerTypeEnumFE.MULTIPLE_CHOICE || answerType === AnswerTypeEnumFE.MULTIPLE_SELECT) && (
            <div className="space-y-3 mt-2">
                <div className="text-xs text-gray-600 mb-2 p-2 bg-blue-50 rounded-md border border-blue-200">
                    <InformationCircleIcon className="h-4 w-4 inline mr-1 text-blue-500" />
                    For <strong>Multiple Choice</strong>: Select one correct key using the radio button (awards 10 points if correct, 0 if incorrect by default), OR provide specific scores for each option key (e.g., a:5, b:2, c:0).
                    <br/>
                    <InformationCircleIcon className="h-4 w-4 inline mr-1 text-blue-500" />
                    For <strong>Multiple Select</strong>: Check multiple correct keys using checkboxes (distributes 10 points among them by default), OR provide specific scores per option key.
                    <br/>
                    <InformationCircleIcon className="h-4 w-4 inline mr-1 text-blue-500" />
                    Using specific scores will override the default single/multiple correct key scoring.
                    <br/>
                    <InformationCircleIcon className="h-4 w-4 inline mr-1 text-blue-500" />
                    Survey outcomes can be edited from the <strong>Survey Management</strong> page.
                    <br/>
                </div>
                {options.map((opt, index) => (
                    <div key={index} className="flex items-center space-x-2 p-2 border rounded bg-gray-50">
                        <Input labelClassName="sr-only" label={`Option ${index+1} Key`} placeholder="Key (e.g. a)" value={opt.key} onChange={e => handleOptionChange(index, 'key', e.target.value)} containerClassName="mb-0 flex-shrink w-20" disabled={isSubmitting}/>
                        <Input labelClassName="sr-only" label={`Option ${index+1} Value`} placeholder="Option Text" value={opt.value} onChange={e => handleOptionChange(index, 'value', e.target.value)} containerClassName="mb-0 flex-grow" disabled={isSubmitting}/>
                        {answerType === AnswerTypeEnumFE.MULTIPLE_CHOICE && (
                            <input type="radio" name="correctKey" title="Mark as correct" value={opt.key} checked={correctKey === opt.key} onChange={() => handleCorrectKeyChange(opt.key)} className="form-radio h-5 w-5 text-indigo-600" disabled={isSubmitting}/>
                        )}
                        {answerType === AnswerTypeEnumFE.MULTIPLE_SELECT && (
                             <input type="checkbox" value={opt.key} title="Mark as correct" checked={correctKeys.includes(opt.key)} onChange={() => handleCorrectKeyChange(opt.key)} className="form-checkbox h-5 w-5 text-indigo-600 rounded" disabled={isSubmitting}/>
                        )}
                        <Input labelClassName="sr-only" label={`Score for ${opt.key}`} type="number" step="any" placeholder="Score (opt.)" value={optionScores[opt.key] === undefined ? '' : optionScores[opt.key]} onChange={e => handleOptionScoreChange(opt.key, e.target.value)} containerClassName="mb-0 w-24" disabled={isSubmitting}/>
                        <Button type="button" variant="danger" size="xs" onClick={() => removeOption(index)} disabled={isSubmitting}>X</Button>
                    </div>
                ))}
                <Button type="button" variant="secondary" size="sm" onClick={addOption} disabled={isSubmitting}>Add Option</Button>
            </div>
        )}
        {answerType === AnswerTypeEnumFE.INPUT && (
            <div className="space-y-3 mt-2">
                {/*@ts-ignore */}
                 <Input type="number" label={
                    <span className="flex items-center">Max Length (Optional)
                        <Tooltip text="Maximum allowed characters for the input.">
                             <InformationCircleIcon className="h-5 w-5 text-gray-400 hover:text-gray-600 ml-1 cursor-pointer" />
                        </Tooltip>
                    </span>} value={inputMaxLength || ''} onChange={e => setInputMaxLength(parseInt(e.target.value) || undefined)} disabled={isSubmitting} />
                <h5 className="text-sm font-medium mt-2 flex items-center">
                    Expected Answers
                     <Tooltip text="Define specific answers and their scores. If no expected answers, default incorrect score (usually 0) applies.">
                         <InformationCircleIcon className="h-5 w-5 text-gray-400 hover:text-gray-600 ml-1 cursor-pointer" />
                    </Tooltip>
                </h5>
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
                {/*@ts-ignore */}
                <Input type="number" label={
                    <span className="flex items-center">Target Value
                         <Tooltip text="The ideal value the student should select for maximum points.">
                             <InformationCircleIcon className="h-5 w-5 text-gray-400 hover:text-gray-600 ml-1 cursor-pointer" />
                        </Tooltip>
                    </span>
                } value={targetValue} onChange={e => setTargetValue(parseFloat(e.target.value))} disabled={isSubmitting}/>
                {/*@ts-ignore */}
                <Input type="number" label={
                     <span className="flex items-center">Score at Target
                         <Tooltip text="Points awarded if student selects the target value. Capped at 10 by the system.">
                             <InformationCircleIcon className="h-5 w-5 text-gray-400 hover:text-gray-600 ml-1 cursor-pointer" />
                        </Tooltip>
                    </span>
                } step="any" value={scoreAtTarget} onChange={e => setScoreAtTarget(parseFloat(e.target.value))} disabled={isSubmitting}/>
                {/*@ts-ignore */}
                <Input type="number" label={
                     <span className="flex items-center">Score Change per Deviation
                         <Tooltip text="Points to add/subtract (usually negative) for each unit of deviation from the target value.">
                             <InformationCircleIcon className="h-5 w-5 text-gray-400 hover:text-gray-600 ml-1 cursor-pointer" />
                        </Tooltip>
                    </span>
                } step="any" value={scorePerDeviation} onChange={e => setScorePerDeviation(parseFloat(e.target.value))} disabled={isSubmitting}/>
            </div>
        )}
      </fieldset>

      <fieldset className="border p-4 rounded-md mt-4">
        <legend className="text-md font-medium text-gray-700 px-1 flex items-center">
            Default Feedback Rules (based on question score)
            <Tooltip text="Feedback shown to student based on their score for THIS question, if not overridden by course-specific QCA feedback.">
                <InformationCircleIcon className="h-5 w-5 text-gray-400 hover:text-gray-600 ml-1 cursor-pointer" />
            </Tooltip>
        </legend>
        {defaultFeedbacks.map((fb, index) => (
          <div key={index} className="p-3 border rounded-md space-y-2 bg-gray-50 my-2">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 items-end">
              <Input label={`Score Value ${index + 1}`} type="number" step="any" value={fb.score_value} onChange={(e) => updateFeedbackItem(index, 'score_value', e.target.value)} error={fieldErrors[`feedback_score_${index}`]} disabled={isSubmitting} containerClassName="mb-0" />
              <Select label="Comparison" options={comparisonOptions} value={fb.comparison} onChange={(e) => updateFeedbackItem(index, 'comparison', e.target.value as FeedbackComparisonEnumFE)} disabled={isSubmitting} containerClassName="mb-0" />
              <Button type="button" variant="danger" size="xs" onClick={() => removeFeedbackItem(index)} disabled={isSubmitting} className="self-end mb-0">Remove</Button>
            </div>
            <Textarea label={`Feedback Text ${index + 1}`} value={fb.feedback} onChange={(e) => updateFeedbackItem(index, 'feedback', e.target.value)} rows={2} error={fieldErrors[`feedback_text_${index}`]} disabled={isSubmitting} containerClassName="mb-0" />
          </div>
        ))}
        <Button type="button" variant="secondary" size="sm" onClick={addFeedbackItem} disabled={isSubmitting}>Add Default Feedback Rule</Button>
      </fieldset>

      <fieldset className="border p-4 rounded-md mt-4">
        <legend className="text-md font-medium text-gray-700 px-1">Course Associations (QCA)</legend>
        {associatedQCAs.map((qca, qcaIndex) => (
            <div key={qca.id || `new-${qcaIndex}`} className="p-3 border rounded-md space-y-3 bg-gray-50 my-2">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-center">
                    <Select
                        label={`Associated Course ${qcaIndex+1}`}
                        options={allCourses.map(c => ({ value: c.id, label: `${c.name} (${c.code})` }))}
                        value={qca.course_id || ""} 
                        onChange={e => handleQCAChange(qcaIndex, 'course_id', e.target.value)}
                        disabled={isSubmitting || !!qca.id} 
                        placeholder="Select a course"
                        containerClassName="mb-0"
                        error={fieldErrors[`qca_course_${qcaIndex}`]} 
                    />
                    {/*@ts-ignore */}
                     <Select label={
                            <span className="flex items-center">
                                Answer Association Type
                                <Tooltip text="Positive: Question score contributes positively to the course total. Negative: Question score subtracts from the course total (e.g., a high score on a pre-assessment question means less need for this specific course).">
                                    <InformationCircleIcon className="h-5 w-5 text-gray-400 hover:text-gray-600 ml-1 cursor-pointer" />
                                </Tooltip>
                            </span>
                        }
                        options={associationTypeOptions}
                        value={qca.answer_association_type}
                        onChange={e => handleQCAChange(qcaIndex, 'answer_association_type', e.target.value as AnswerAssociationTypeEnumFE)}
                        disabled={isSubmitting}
                        containerClassName="mb-0"
                    />
                    <Button type="button" variant="danger" size="xs" onClick={() => handleRemoveQCA(qcaIndex)} disabled={isSubmitting} className="self-center mt-4 md:mt-0">Remove Association</Button>
                </div>
                <div className="ml-4 border-l-2 pl-3 space-y-2">
                    <h5 className="text-sm font-medium text-gray-600 flex items-center">
                        Course-Specific Feedback for "{qca.courseName || 'Selected Course'}"
                        <Tooltip text="This feedback overrides the default question feedback when this question is answered in the context of this specific course.">
                           <InformationCircleIcon className="h-5 w-5 text-gray-400 hover:text-gray-600 ml-1 cursor-pointer" />
                        </Tooltip>
                    </h5>
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