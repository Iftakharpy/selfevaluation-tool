import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';


const HomePage: React.FC = () => {
	const { user, logoutUser } = useAuth();
	return (
		<div className="text-center">
			<h1 className="text-4xl font-bold mb-6">Welcome to Narsus, {user?.display_name}!</h1>
			<p className="text-lg mb-2">Your role: <span className="font-semibold">{user?.role}</span></p>
			{user?.role === 'teacher' && (
				<p className="mb-4">
					<Link to="/dashboard" className="text-blue-600 hover:text-blue-800 underline">
						Go to Teacher Dashboard
					</Link>
				</p>
			)}
			{user?.role === 'student' && (
				<p className="mb-4">
					<Link to="/surveys" className="text-blue-600 hover:text-blue-800 underline">
						View Available Surveys
					</Link>
				</p>
			)}
			<button
				onClick={logoutUser}
				className="mt-6 px-6 py-2 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg shadow-md transition duration-150 ease-in-out"
			>
				Logout
			</button>
		</div>
	);
};

export default HomePage;