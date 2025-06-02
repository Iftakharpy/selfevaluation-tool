import React from 'react';
import Modal from './Modal'; // Assuming path is now modals/Modal.tsx or models/Model.tsx
import Button from '../forms/Button';

interface ConfirmDeleteModalProps {
  isOpen: boolean;
  onClose: () => void; // This will be used by Modal's overlay click / X button
  onConfirm: () => void;
  itemName: string;
  isLoading?: boolean;
}

const ConfirmDeleteModal: React.FC<ConfirmDeleteModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  itemName,
  isLoading = false,
}) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Delete ${itemName}`}>
      <> {/* Use a fragment to group content and buttons */}
        <p className="text-sm text-gray-600">
          Are you sure you want to delete this {itemName}? This action cannot be undone.
        </p>
        {/* Action buttons are now part of the children passed to Modal */}
        <div className="mt-5 sm:mt-4 flex flex-row-reverse space-x-2 space-x-reverse">
          <Button
            variant="danger"
            onClick={onConfirm}
            isLoading={isLoading}
            // className="w-full sm:ml-3 sm:w-auto"
          >
            Delete
          </Button>
          <Button
            variant="ghost"
            onClick={onClose} // This button calls the onClose prop to close the modal
            disabled={isLoading}
            // className="mt-3 w-full sm:mt-0 sm:w-auto"
          >
            Cancel
          </Button>
        </div>
      </>
    </Modal>
  );
};

export default ConfirmDeleteModal;
