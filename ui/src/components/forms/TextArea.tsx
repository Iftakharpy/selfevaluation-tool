import React from 'react';
import type { TextareaHTMLAttributes } from 'react';
import clsx from 'clsx'; // Import clsx

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  labelClassName?: string;
  textareaClassName?: string;
  errorClassName?: string;
  containerClassName?: string;
}

const Textarea: React.FC<TextareaProps> = ({
  label,
  id,
  error,
  labelClassName: propLabelClassName,       // Rename
  textareaClassName: propTextareaClassName,  // Rename
  errorClassName: propErrorClassName,        // Rename
  containerClassName: propContainerClassName, // Rename
  ...props
}) => {
  // Define default class names
  const defaultLabelClassName = "block text-sm font-medium text-gray-700 mb-1";
  const defaultTextareaClassName = "appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm";
  const defaultErrorClassName = "mt-1 text-xs text-red-600";
  const defaultContainerClassName = "mb-4";

  // Merge class names using clsx
  const mergedLabelClassName = clsx(defaultLabelClassName, propLabelClassName);
  const mergedTextareaClassName = clsx(
    defaultTextareaClassName,
    propTextareaClassName,
    error ? 'border-red-500' : 'border-gray-300' // Conditional class for error
  );
  const mergedErrorClassName = clsx(defaultErrorClassName, propErrorClassName);
  const mergedContainerClassName = clsx(defaultContainerClassName, propContainerClassName);

  return (
    <div className={mergedContainerClassName}>
      {label && (
        <label htmlFor={id || props.name} className={mergedLabelClassName}>
          {label}
        </label>
      )}
      <textarea
        id={id || props.name}
        className={mergedTextareaClassName}
        {...props}
      />
      {error && <p className={mergedErrorClassName}>{error}</p>}
    </div>
  );
};

export default Textarea;
