import React from 'react';
import type { SurveyQuestionDetailFE } from '../../../types/surveyTypes';

interface RangeInputProps {
  question: SurveyQuestionDetailFE;
  currentAnswer: number | undefined;
  onChange: (value: number) => void;
  disabled?: boolean;
}

const RangeInput: React.FC<RangeInputProps> = ({
  question,
  currentAnswer,
  onChange,
  disabled = false,
}) => {
  const min = question.answer_options?.min as number ?? 0;
  const max = question.answer_options?.max as number ?? 10;
  const step = question.answer_options?.step as number ?? 1;
  const value = currentAnswer === undefined ? Math.round((min + max) / 2) : currentAnswer;

  return (
    <div className="mt-4">
      <input
        id={question.question_id}
        name={question.question_id}
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        disabled={disabled}
        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
      />
      <div className="flex justify-between text-xs text-gray-600 mt-1">
        <span>{min}</span>
        <span className="font-semibold text-indigo-600 text-sm">{value}</span>
        <span>{max}</span>
      </div>
    </div>
  );
};

export default RangeInput;
