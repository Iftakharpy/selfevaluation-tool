import React from 'react';
import { OutcomeCategoryEnumFE } from '../../types/surveyTypes';

interface CourseResultCardProps {
  courseName: string; // You'll need to fetch/pass this
  score: number;
  overallFeedback?: string | null;
  detailedFeedbackItems?: string[] | null;
  outcome?: OutcomeCategoryEnumFE | null;
}

const getOutcomeStyling = (outcome?: OutcomeCategoryEnumFE | null) => {
  switch (outcome) {
    case OutcomeCategoryEnumFE.ELIGIBLE_FOR_ERPL:
      return { text: 'Eligible for eRPL', color: 'text-green-700', bg: 'bg-green-100' };
    case OutcomeCategoryEnumFE.RECOMMENDED:
      return { text: 'Recommended to Take Course', color: 'text-blue-700', bg: 'bg-blue-100' };
    case OutcomeCategoryEnumFE.NOT_SUITABLE:
      return { text: 'Not Suitable / Needs Improvement', color: 'text-red-700', bg: 'bg-red-100' };
    case OutcomeCategoryEnumFE.UNDEFINED:
    default:
      return { text: 'Outcome Undefined', color: 'text-gray-700', bg: 'bg-gray-100' };
  }
};

const CourseResultCard: React.FC<CourseResultCardProps> = ({
  courseName,
  score,
  overallFeedback,
  detailedFeedbackItems,
  outcome,
}) => {
  const outcomeStyle = getOutcomeStyling(outcome);

  return (
    <div className="bg-white shadow-md rounded-lg p-6 mb-6">
      <h4 className="text-xl font-semibold text-indigo-600 mb-2">{courseName}</h4>
      <div className="mb-3">
        <span className="text-gray-700 font-medium">Your Score: </span>
        <span className="text-2xl font-bold text-indigo-500">{score.toFixed(1)}</span>
      </div>

      {outcome && (
        <div className={`p-2 rounded-md text-sm font-medium mb-3 ${outcomeStyle.bg} ${outcomeStyle.color}`}>
          Outcome: {outcomeStyle.text}
        </div>
      )}

      {overallFeedback && (
        <div className="mb-3">
          <h5 className="text-sm font-semibold text-gray-700 mb-1">Overall Feedback:</h5>
          <p className="text-gray-600 text-sm">{overallFeedback}</p>
        </div>
      )}

      {detailedFeedbackItems && detailedFeedbackItems.length > 0 && (
        <div>
          <h5 className="text-sm font-semibold text-gray-700 mb-1">Detailed Feedback:</h5>
          <ul className="list-disc list-inside space-y-1 pl-4">
            {detailedFeedbackItems.map((item, index) => (
              <li key={index} className="text-gray-600 text-sm">{item}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default CourseResultCard;
