import React from 'react';
import type { SurveyQuestionDetailFE } from '../../../types/surveyTypes';
import Textarea from '../../forms/TextArea'; // Use your reusable Textarea

interface TextInputProps {
  question: SurveyQuestionDetailFE;
  currentAnswer: string | undefined;
  onChange: (value: string) => void;
  disabled?: boolean;
}

const TextInput: React.FC<TextInputProps> = ({
  question,
  currentAnswer,
  onChange,
  disabled = false,
}) => {
  return (
    <div className="mt-2">
      <Textarea
        id={question.question_id}
        name={question.question_id}
        rows={3}
        placeholder="Type your answer here..."
        value={currentAnswer || ''}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        maxLength={question.answer_options?.max_length as number || undefined}
      />
    </div>
  );
};

export default TextInput;