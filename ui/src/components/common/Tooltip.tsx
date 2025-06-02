import React, { useState } from 'react';
import "./Tooltip.css"

interface TooltipProps {
  text: string;
  children: React.ReactElement;
  position?: 'top' | 'bottom' | 'left' | 'right';
  className?: string; 
}

const Tooltip: React.FC<TooltipProps> = ({ text, children, position = 'top', className }) => {
  const [showTooltip, setShowTooltip] = useState(false);

  const getPositionClasses = () => {
    // These position the tooltip relative to its parent (.relative .inline-flex)
    switch (position) {
      case 'bottom':
        return 'top-full left-1/2 -translate-x-1/2 mt-2';
      case 'left':
        return 'top-1/2 -translate-y-1/2 right-full mr-2';
      case 'right':
        return 'top-1/2 -translate-y-1/2 left-full ml-2';
      case 'top':
      default:
        return 'bottom-full left-1/2 -translate-x-1/2 mb-2';
    }
  };

  // Tooltip bubble itself should have a high enough z-index to appear above siblings
  // within its local stacking context, but it won't break out of an ancestor with overflow:hidden.
  const tooltipBaseClasses = "absolute z-30 px-3 py-2 text-xs font-medium text-white bg-gray-800 rounded-md shadow-lg"; 
  const contentConstraintClasses = "max-w-sm min-w-xs whitespace-normal break-words"; 

  const arrowBaseClasses = "absolute w-2 h-2 bg-gray-800 transform rotate-45";
  const arrowPositionClasses = 
    position === 'top' ? 'bottom-[-4px] left-1/2 -translate-x-1/2' :
    position === 'bottom' ? 'top-[-4px] left-1/2 -translate-x-1/2' :
    position === 'left' ? 'right-[-4px] top-1/2 -translate-y-1/2' :
    position === 'right' ? 'left-[-4px] top-1/2 -translate-y-1/2' : '';

  return (
    <div className="relative inline-flex"> {/* This creates a new stacking context for the tooltip */}
      {React.cloneElement(children, {
        /*@ts-ignore*/
        onMouseEnter: () => setShowTooltip(true),
        onMouseLeave: () => setShowTooltip(false),
        onFocus: () => setShowTooltip(true), 
        onBlur: () => setShowTooltip(false),  
      })}

      {showTooltip && (
        <div
          role="tooltip"
          className={`${tooltipBaseClasses} ${contentConstraintClasses} ${getPositionClasses()} ${className || ''}`}
        >
          {text}
          <div className={`${arrowBaseClasses} ${arrowPositionClasses}`}></div>
        </div>
      )}
    </div>
  );
};

export default Tooltip;