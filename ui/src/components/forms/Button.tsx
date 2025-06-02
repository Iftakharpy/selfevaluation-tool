// ui/src/components/forms/Button.tsx
import React from 'react';
import type { ButtonHTMLAttributes } from 'react';
import clsx from 'clsx';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; // Size prop
  isLoading?: boolean;
  fullWidth?: boolean;
  // className?: string; // Already part of ButtonHTMLAttributes, handled by propClassName
}

const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md', // Default size
  isLoading = false,
  fullWidth = false,
  className: propClassName, // To merge with generated classes
  ...props
}) => {
  const baseStyle = "inline-flex items-center justify-center border border-transparent font-medium rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors duration-150 ease-in-out";
  const fullWidthStyle = fullWidth ? "w-full" : "";

  let variantStyle = '';
  switch (variant) {
    case 'secondary':
      variantStyle = 'text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:ring-indigo-500';
      break;
    case 'danger':
      variantStyle = 'text-white bg-red-600 hover:bg-red-700 focus:ring-red-500';
      break;
    case 'ghost':
      variantStyle = 'text-gray-700 bg-transparent hover:bg-gray-100 focus:ring-indigo-500 border-gray-300'; // Added border for ghost for better definition
      break;
    case 'primary':
    default:
      variantStyle = 'text-white bg-indigo-600 hover:bg-indigo-700 focus:ring-indigo-500';
      break;
  }

  let sizeStyle = '';
  switch (size) {
    case 'xs':
      sizeStyle = 'px-2.5 py-1.5 text-xs';
      break;
    case 'sm':
      sizeStyle = 'px-3 py-1.5 text-sm leading-4'; // Adjusted py for sm
      break;
    case 'lg':
      sizeStyle = 'px-4 py-2 text-base';
      break;
    case 'xl':
      sizeStyle = 'px-6 py-3 text-base';
      break;
    case 'md': // Default
    default:
      sizeStyle = 'px-4 py-2 text-sm'; // Standard button size
      break;
  }

  const disabledStyle = props.disabled || isLoading ? 'opacity-50 cursor-not-allowed' : '';

  // Spinner color adjustment based on variant for better contrast
  const spinnerColorClass = () => {
    if (variant === 'secondary' || variant === 'ghost') {
      return 'text-indigo-500'; // Spinner color for light background buttons
    }
    return 'text-white'; // Default spinner color for dark background buttons
  };

  const mergedClassName = clsx(
    baseStyle,
    variantStyle,
    sizeStyle,
    fullWidthStyle,
    disabledStyle,
    propClassName // User-provided classes
  );

  return (
    <button
      className={mergedClassName}
      disabled={props.disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <>
          <svg 
            className={clsx(
              "animate-spin h-5 w-5", 
              size === 'xs' || size === 'sm' ? "mr-2 -ml-0.5" : "mr-3 -ml-1", // Adjust margin based on size
              spinnerColorClass() // Dynamic spinner color
            )} 
            xmlns="http://www.w3.org/2000/svg" 
            fill="none" 
            viewBox="0 0 24 24"
          >
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          Processing...
        </>
      ) : (
        children
      )}
    </button>
  );
};

export default Button;
