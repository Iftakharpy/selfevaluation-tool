import React from 'react';
import type { InputHTMLAttributes } from 'react';
import clsx from 'clsx'; // Import clsx

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  labelClassName?: string;
  inputClassName?: string;
  errorClassName?: string;
  containerClassName?: string;
}

const Input: React.FC<InputProps> = ({
  label,
  id,
  error,
  labelClassName: propLabelClassName, // Rename to avoid conflict with default
  inputClassName: propInputClassName,   // Rename
  errorClassName: propErrorClassName,   // Rename
  containerClassName: propContainerClassName, // Rename
  ...props
}) => {
  // Define default class names
  const defaultLabelClassName = "block text-sm font-medium text-gray-700 mb-1";
  const defaultInputClassName = "appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm";
  const defaultErrorClassName = "mt-1 text-xs text-red-600";
  const defaultContainerClassName = "mb-4 width-full";

  // Merge class names using clsx
  const mergedLabelClassName = clsx(defaultLabelClassName, propLabelClassName);
  const mergedInputClassName = clsx(
    defaultInputClassName,
    propInputClassName,
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
      <input
        id={id || props.name}
        className={mergedInputClassName}
        {...props}
      />
      {error && <p className={mergedErrorClassName}>{error}</p>}
    </div>
  );
};

export default Input;
