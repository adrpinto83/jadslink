import React from 'react';
import { AlertCircle, CheckCircle } from 'lucide-react';

interface FormInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  success?: boolean;
  helperText?: string;
  required?: boolean;
}

/**
 * Enhanced form input with validation feedback
 */
const FormInput = React.forwardRef<HTMLInputElement, FormInputProps>(
  (
    {
      label,
      error,
      success,
      helperText,
      required,
      className = '',
      ...props
    },
    ref
  ) => {
    return (
      <div className="space-y-2">
        {label && (
          <label className="block text-sm font-medium text-gray-700">
            {label}
            {required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}

        <div className="relative">
          <input
            ref={ref}
            className={`
              w-full px-4 py-2.5 rounded-lg border-2 transition-all duration-200
              focus:outline-none focus:ring-2 focus:ring-offset-0
              ${
                error
                  ? 'border-red-300 focus:border-red-500 focus:ring-red-200'
                  : success
                    ? 'border-green-300 focus:border-green-500 focus:ring-green-200'
                    : 'border-gray-200 focus:border-blue-500 focus:ring-blue-200'
              }
              ${className}
            `}
            {...props}
          />

          {error && (
            <AlertCircle className="absolute right-3 top-3 w-5 h-5 text-red-500 animate-in fade-in duration-200" />
          )}
          {success && (
            <CheckCircle className="absolute right-3 top-3 w-5 h-5 text-green-500 animate-in fade-in duration-200" />
          )}
        </div>

        {error && (
          <p className="text-sm text-red-500 flex items-center gap-1 animate-in fade-in duration-200">
            <AlertCircle className="w-4 h-4" />
            {error}
          </p>
        )}

        {helperText && !error && (
          <p className="text-sm text-gray-500">{helperText}</p>
        )}
      </div>
    );
  }
);

FormInput.displayName = 'FormInput';

export default FormInput;
