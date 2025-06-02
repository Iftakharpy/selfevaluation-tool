import React from 'react';
import { Link } from 'react-router-dom';

const DashboardCard: React.FC<{ title: string; description: string; linkTo: string }> = ({ title, description, linkTo }) => (
  <Link to={linkTo} className="block p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 ease-in-out">
    <h3 className="text-xl font-semibold text-indigo-600 mb-2">{title}</h3>
    <p className="text-gray-600 text-sm">{description}</p>
  </Link>
);

const TeacherDashboardPage: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-800 mb-8">Teacher Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <DashboardCard 
          title="Manage Courses" 
          description="Create, view, edit, and delete courses or skills." 
          linkTo="/courses/manage" 
        />
        <DashboardCard 
          title="Manage Questions" 
          description="Create, view, edit, and delete assessment questions." 
          linkTo="/questions/manage" 
        />
        <DashboardCard 
          title="Manage Surveys" 
          description="Create, view, edit, publish, and delete surveys." 
          linkTo="/surveys/manage" 
        />
         {/* Add more cards as needed, e.g., "View Student Results" */}
      </div>
    </div>
  );
};

export default TeacherDashboardPage;