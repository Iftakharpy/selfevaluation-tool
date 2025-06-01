import React from 'react';
import type { SurveyQuestionDetailFE } from '../../../types/surveyTypes';

interface MultipleChoiceInputProps {
  question: SurveyQuestionDetailFE;
  currentAnswer: string | undefined;
  onChange: (value: string) => void;
  disabled?: boolean;
}

const MultipleChoiceInput: React.FC<MultipleChoiceInputProps> = ({
  question,
  currentAnswer,
  onChange,
  disabled = false,
}) => {
  const options = question.answer_options || {};

  return (
    <fieldset className="mt-2">
      <legend className="sr-only">Choose one option for {question.title}</legend>
      <div className="space-y-3">
        {Object.entries(options).map(([key, value]) => (
          <div key={key} className="flex items-center">
            <input
              id={`${question.question_id}-${key}`}
              name={question.question_id}
              type="radio"
              value={key}
              checked={currentAnswer === key}
              onChange={(e) => onChange(e.target.value)}
              disabled={disabled}
              className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300"
            />
            <label htmlFor={`${question.question_id}-${key}`} className="ml-3 block text-sm font-medium text-gray-700">
              {String(value)}
            </label>
          </div>
        ))}
      </div>
    </fieldset>
  );
};

export default MultipleChoiceInput;