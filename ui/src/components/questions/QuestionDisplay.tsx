import React from 'react';
import type { SurveyQuestionDetailFE } from '../../types/surveyTypes';
import { AnswerTypeEnumFE } from '../../types/surveyTypes';
import MultipleChoiceInput from './inputs/MultipleChoiceInput';
import MultipleSelectInput from './inputs/MultipleSelectInput';
import TextInput from './inputs/TextInput';
import RangeInput from './inputs/RangeInput';

interface QuestionDisplayProps {
  question: SurveyQuestionDetailFE;
  currentAnswer: any; // string | string[] | number | undefined
  onAnswerChange: (questionId: string, qcaId: string, courseId: string, answerValue: any) => void;
  isSubmitted: boolean; // To disable inputs after submission
}

const QuestionDisplay: React.FC<QuestionDisplayProps> = ({
  question,
  currentAnswer,
  onAnswerChange,
  isSubmitted,
}) => {
  const handleAnswer = (value: any) => {
    onAnswerChange(question.question_id, question.qca_id, question.course_id, value);
  };

  const renderAnswerInput = () => {
    switch (question.answer_type) {
      case AnswerTypeEnumFE.MULTIPLE_CHOICE:
        return (
          <MultipleChoiceInput
            question={question}
            currentAnswer={currentAnswer as string | undefined}
            onChange={handleAnswer}
            disabled={isSubmitted}
          />
        );
      case AnswerTypeEnumFE.MULTIPLE_SELECT:
        return (
          <MultipleSelectInput
            question={question}
            currentAnswers={(currentAnswer as string[] | undefined) || []}
            onChange={handleAnswer}
            disabled={isSubmitted}
          />
        );
      case AnswerTypeEnumFE.INPUT:
        return (
          <TextInput
            question={question}
            currentAnswer={currentAnswer as string | undefined}
            onChange={handleAnswer}
            disabled={isSubmitted}
          />
        );
      case AnswerTypeEnumFE.RANGE:
        return (
          <RangeInput
            question={question}
            currentAnswer={currentAnswer as number | undefined}
            onChange={handleAnswer}
            disabled={isSubmitted}
          />
        );
      default:
        return <p className="text-red-500">Unsupported question type: {question.answer_type}</p>;
    }
  };

  return (
    <div className="bg-white shadow-md rounded-lg p-6 mb-6">
      <h4 className="text-lg font-semibold text-gray-800 mb-1">{question.title}</h4>
      {question.details && <p className="text-sm text-gray-600 mb-3">{question.details}</p>}
      {renderAnswerInput()}
    </div>
  );
};

export default QuestionDisplay;