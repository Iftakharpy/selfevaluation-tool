import React, { createContext, useState, useContext, useCallback } from 'react';
import type { ReactNode } from 'react';


type NotificationType = 'success' | 'error' | 'info' | 'warning';

interface Notification {
  id: number;
  message: string;
  type: NotificationType;
}

interface NotificationContextType {
  addNotification: (message: string, type: NotificationType) => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const NotificationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const addNotification = useCallback((message: string, type: NotificationType) => {
    const id = Date.now();
    setNotifications(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 5000); // Auto-dismiss after 5 seconds
  }, []);

  const removeNotification = (id: number) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const positionClasses = "fixed top-5 right-5 z-50 space-y-3";

  return (
    <NotificationContext.Provider value={{ addNotification }}>
      {children}
      <div className={positionClasses}>
        {notifications.map(n => (
          <ToastNotification 
            key={n.id} 
            message={n.message} 
            type={n.type} 
            onDismiss={() => removeNotification(n.id)} 
          />
        ))}
      </div>
    </NotificationContext.Provider>
  );
};

export const useNotifier = (): NotificationContextType => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifier must be used within a NotificationProvider');
  }
  return context;
};

// ToastNotification Component (could be in its own file)
interface ToastProps {
  message: string;
  type: NotificationType;
  onDismiss: () => void;
}

const ToastNotification: React.FC<ToastProps> = ({ message, type, onDismiss }) => {
  let bgColor = '';
  let textColor = 'text-white'; // Default for most
  let borderColor = '';

  switch (type) {
    case 'success':
      bgColor = 'bg-green-500';
      borderColor = 'border-green-600';
      break;
    case 'error':
      bgColor = 'bg-red-500';
      borderColor = 'border-red-600';
      break;
    case 'info':
      bgColor = 'bg-blue-500';
      borderColor = 'border-blue-600';
      break;
    case 'warning':
      bgColor = 'bg-yellow-500';
      textColor = 'text-yellow-900'; // Darker text for yellow
      borderColor = 'border-yellow-600';
      break;
  }

  return (
    <div 
      className={`max-w-sm w-full ${bgColor} ${textColor} shadow-lg rounded-lg pointer-events-auto ring-1 ring-black ring-opacity-5 overflow-hidden border-l-4 ${borderColor}`}
    >
      <div className="p-4 w-full">
        <div className="flex w-full items-start">
          <div className="ml-3 w-full flex-1 pt-0.5">
            <p className="text-sm font-medium">{message}</p>
          </div>
          <div className="ml-4 flex-shrink-0 flex">
            <button
              onClick={onDismiss}
              className={`inline-flex rounded-md ${bgColor} ${textColor} hover:opacity-80 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-white p-1`} // Adjusted focus for better contrast
            >
              <span className="sr-only">Close</span>
              {/* X Icon (Heroicons) */}
              <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};