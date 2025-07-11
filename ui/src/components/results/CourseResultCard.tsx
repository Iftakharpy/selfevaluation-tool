// File: ui/src/components/results/CourseResultCard.tsx
import React from 'react';
import { OutcomeCategoryEnumFE } from '../../types/surveyTypes';
import Tooltip from '../common/Tooltip'; // IMPORT
import { InformationCircleIcon } from '../icons/InformationCircleIcon'; // IMPORT

interface CourseResultCardProps {
  courseName: string;
  score: number;
  maxScore?: number | null;
  overallFeedback?: string | null;
  detailedFeedbackItems?: string[] | null;
  outcome?: OutcomeCategoryEnumFE | null;
}

const getOutcomeStyling = (outcome?: OutcomeCategoryEnumFE | null) => {
  switch (outcome) {
    case OutcomeCategoryEnumFE.ELIGIBLE_FOR_ERPL:
      return { text: 'Eligible for eRPL', color: 'text-green-700', bg: 'bg-green-100', description: "Your performance suggests you may have prior learning that could be recognized for this course." };
    case OutcomeCategoryEnumFE.RECOMMENDED:
      return { text: 'Recommended to Take Course', color: 'text-blue-700', bg: 'bg-blue-100', description: "It's recommended that you take this course to build foundational or further skills." };
    case OutcomeCategoryEnumFE.NOT_SUITABLE:
      return { text: 'Not Suitable / Needs Improvement', color: 'text-red-700', bg: 'bg-red-100', description: "Your current assessment indicates this course may not be the best fit right now, or significant improvement is needed." };
    case OutcomeCategoryEnumFE.UNDEFINED:
    default:
      return { text: 'Outcome Undefined', color: 'text-gray-700', bg: 'bg-gray-100', description: "An outcome category could not be determined based on your score." };
  }
};

const CourseResultCard: React.FC<CourseResultCardProps> = ({
  courseName,
  score,
  maxScore,
  overallFeedback,
  detailedFeedbackItems,
  outcome,
}) => {
  const outcomeStyle = getOutcomeStyling(outcome);
  const percentageScore = (maxScore !== undefined && maxScore !== null && maxScore > 0) 
    ? ((score / maxScore) * 100) 
    : null;

  return (
    <div className="bg-white shadow-md rounded-lg p-6 mb-6">
      <h4 className="text-xl font-semibold text-indigo-600 mb-2">{courseName}</h4>
      <div className="mb-3 flex items-baseline space-x-2">
        <div>
          <span className="text-gray-700 font-medium">Your Score: </span>
          <span className="text-2xl font-bold text-indigo-500">{score.toFixed(1)}</span>
          {(maxScore !== undefined && maxScore !== null) && <span className="text-sm text-gray-500"> / {maxScore.toFixed(1)}</span>}
        </div>
        {percentageScore !== null && (
          <div className="text-lg font-semibold text-green-600 bg-green-100 px-2 py-1 rounded">
            ({percentageScore.toFixed(0)}%)
          </div>
        )}
      </div>

      {outcome && (
        <div className={`p-2 rounded-md text-sm font-medium mb-3 ${outcomeStyle.bg} ${outcomeStyle.color} flex items-center`}>
          Outcome: {outcomeStyle.text}
          <Tooltip text={outcomeStyle.description}>
            <InformationCircleIcon className="h-4 w-4 text-current hover:opacity-70 ml-2 cursor-pointer" />
          </Tooltip>
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