import React from 'react';
import type { ReactNode } from 'react';

interface ModalProps {
  isOpen: boolean;
  title: string;
  children: ReactNode;
  onClose?: () => void; // Make onClose truly optional for cases where footer handles closing
  footer?: ReactNode | null; // Allow null to explicitly indicate no footer
}

const Modal: React.FC<ModalProps> = ({ isOpen, onClose, title, children, footer }) => {
  if (!isOpen) return null;

  return (
    // Overlay for click-outside-to-close
    // Using a more common pattern for the overlay and modal container
    <div 
      className="z-10 fixed inset-0 overflow-y-auto backdrop-blur-xs backdrop-brightness-50 flex items-center justify-center p-4"
      // onClick={onClose} // Click on overlay closes modal
    >
      <div 
        className="z-50 inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full"
        onClick={(e) => e.stopPropagation()} // Prevent click inside modal from closing it
      >
        <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4 isolate">
          <div className="sm:flex sm:items-start">
            {/* Optional: Icon can go here */}
            <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
              <div className="flex justify-between items-center pb-3">
                <h3 className="text-lg leading-6 font-medium text-gray-900" id="modal-title">
                  {title}
                </h3>
                {/* Optional explicit X close button in header if onClose is provided */}
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
              <div className="mt-2"> {/* Changed from mt-4 */}
                {children}
              </div>
            </div>
          </div>
        </div>
        {/* Footer is now part of the children or handled by the component using Modal */}
        {/* If a specific footer prop is desired, it should be passed to and rendered by children */}
        {/* OR handle footer directly in the component using Modal */}
        {/* For this fix, we assume forms will provide their own action buttons */}
      </div>
    </div>
  );
};

export default Modal;