import React from 'react';
import type { SurveyQuestionDetailFE } from '../../../types/surveyTypes';

interface MultipleSelectInputProps {
  question: SurveyQuestionDetailFE;
  currentAnswers: string[]; // Array of selected keys
  onChange: (selectedKeys: string[]) => void;
  disabled?: boolean;
}

const MultipleSelectInput: React.FC<MultipleSelectInputProps> = ({
  question,
  currentAnswers,
  onChange,
  disabled = false,
}) => {
  const options = question.answer_options || {};

  const handleCheckboxChange = (key: string, checked: boolean) => {
    if (checked) {
      onChange([...currentAnswers, key]);
    } else {
      onChange(currentAnswers.filter(k => k !== key));
    }
  };

  return (
    <fieldset className="mt-2">
      <legend className="sr-only">Select applicable options for {question.title}</legend>
      <div className="space-y-3">
        {Object.entries(options).map(([key, value]) => (
          <div key={key} className="flex items-center">
            <input
              id={`${question.question_id}-${key}`}
              name={`${question.question_id}-${key}`} // Unique name per checkbox for forms
              type="checkbox"
              value={key}
              checked={currentAnswers.includes(key)}
              onChange={(e) => handleCheckboxChange(key, e.target.checked)}
              disabled={disabled}
              className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
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

export default MultipleSelectInput;