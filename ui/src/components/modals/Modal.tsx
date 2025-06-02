import React from 'react';
import type { ReactNode } from 'react';

interface ModalProps {
  isOpen: boolean;
  title: string;
  children: ReactNode;
  onClose?: () => void; 
  footer?: ReactNode | null; 
  size?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl'; // Added size prop
}

const Modal: React.FC<ModalProps> = ({ 
  isOpen, 
  onClose, 
  title, 
  children, 
  footer,
  size = 'lg' // Default to large, which was the previous sm:max-w-lg
}) => {
  if (!isOpen) return null;

  const sizeClasses: Record<string, string> = {
    'sm': 'sm:max-w-sm',
    'md': 'sm:max-w-md',
    'lg': 'sm:max-w-lg',   // Default from before
    'xl': 'sm:max-w-xl',
    '2xl': 'sm:max-w-2xl', // Good for forms with tooltips
    '3xl': 'sm:max-w-3xl', // Even wider
    '4xl': 'sm:max-w-4xl',
  };

  return (
    <div 
      className="z-10 fixed inset-0 overflow-y-auto backdrop-blur-xs backdrop-brightness-50 flex items-center justify-center p-4"
    >
      <div 
        className={`z-50 inline-block align-bottom bg-white rounded-lg text-left shadow-xl transform transition-all sm:my-8 sm:align-middle w-full ${sizeClasses[size] || sizeClasses['lg']}`} // Apply dynamic size, default to lg
        onClick={(e) => e.stopPropagation()} 
      >
        <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4 rounded-4xl">
          <div className="sm:flex sm:items-start">
            <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
              <div className="flex justify-between items-center pb-3">
                <h3 className="text-lg leading-6 font-medium text-gray-900" id="modal-title">
                  {title}
                </h3>
                {onClose && (
                   <button
                    onClick={onClose}
                    className="text-gray-400 hover:text-gray-600 focus:outline-none"
                    aria-label="Close modal"
                  >
                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>
              <div className="mt-2"> 
                {children}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Modal;