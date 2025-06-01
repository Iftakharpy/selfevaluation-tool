import React from 'react';
import { Link } from 'react-router-dom';
import type { SurveySummaryListItemFE } from '../../types/surveyTypes';
import Button from '../forms/Button';

interface SurveyCardProps {
  survey: SurveySummaryListItemFE;
  actionText?: string;
  actionLink?: string;
}

const SurveyCard: React.FC<SurveyCardProps> = ({ survey, actionText = "Take Survey", actionLink }) => {
  const linkTo = actionLink || `/survey/take/${survey.id}`;
  return (
    <div className="bg-white shadow-lg rounded-lg p-6 mb-6 hover:shadow-xl transition-shadow duration-200">
      <h3 className="text-2xl font-semibold text-indigo-700 mb-2">{survey.title}</h3>
      <p className="text-gray-600 mb-1 text-sm">
        Courses: {survey.course_ids.length} 
        {/* Ideally, fetch course names or include them in API response */}
      </p>
      {survey.description && (
        <p className="text-gray-700 mb-4 text-sm leading-relaxed">
          {survey.description.length > 150 ? `${survey.description.substring(0, 147)}...` : survey.description}
        </p>
      )}
      <div className="mt-4">
        <Link to={linkTo}>
          <Button variant="primary" >{actionText}</Button>
        </Link>
      </div>
       <p className="text-xs text-gray-400 mt-3">Last updated: {new Date(survey.updated_at).toLocaleDateString()}</p>
    </div>
  );
};

export default SurveyCard;