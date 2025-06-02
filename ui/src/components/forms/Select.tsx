import React from 'react';
import type { SelectHTMLAttributes } from 'react';
import clsx from 'clsx'; 

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options: Array<{ value: string | number; label: string }>;
  labelClassName?: string;
  selectClassName?: string;
  errorClassName?: string;
  containerClassName?: string;
  placeholder?: string;
}

const Select: React.FC<SelectProps> = ({
  label,
  id,
  error,
  options,
  labelClassName: propLabelClassName,      
  selectClassName: propSelectClassName,    
  errorClassName: propErrorClassName,      
  containerClassName: propContainerClassName, 
  placeholder,
  value, // Ensure value prop is used for controlled component
  ...props
}) => {
  const defaultLabelClassName = "block text-sm font-medium text-gray-700 mb-1";
  const defaultSelectClassName = "mt-1 block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md";
  const defaultErrorClassName = "mt-1 text-xs text-red-600";
  const defaultContainerClassName = "mb-4";

  const mergedLabelClassName = clsx(defaultLabelClassName, propLabelClassName);
  const mergedSelectClassName = clsx(
    defaultSelectClassName,
    propSelectClassName,
    error ? 'border-red-500' : 'border-gray-300' 
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
      <select
        id={id || props.name}
        className={mergedSelectClassName}
        value={value === undefined && placeholder ? "" : value} // Handle placeholder selection with value prop
        {...props}
      >
        {/* @ts-ignore */}
        {placeholder && (<option value="" disabled={props.value !== "" && props.value !== undefined}> 
            {placeholder}
          </option>
        )}
        {options.map(option => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error && <p className={mergedErrorClassName}>{error}</p>}
    </div>
  );
};

export default Select;