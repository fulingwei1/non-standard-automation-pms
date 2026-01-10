import { useState, useCallback } from "react";
import { getValidationErrors } from "../utils/errorHandler";

/**
 * Custom hook for form management with validation
 * @param {Object} initialValues - Initial form values
 * @param {Function} validate - Validation function
 * @param {Function} onSubmit - Submit handler
 * @returns {Object} - Form state and handlers
 */
export function useForm(initialValues = {}, validate, onSubmit) {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = useCallback(
    (name, value) => {
      setValues((prev) => ({ ...prev, [name]: value }));

      // Clear error when user starts typing
      if (errors[name]) {
        setErrors((prev) => {
          const newErrors = { ...prev };
          delete newErrors[name];
          return newErrors;
        });
      }

      // Mark field as touched
      setTouched((prev) => ({ ...prev, [name]: true }));
    },
    [errors],
  );

  const handleBlur = useCallback(
    (name) => {
      setTouched((prev) => ({ ...prev, [name]: true }));

      // Validate on blur if validation function provided
      if (validate) {
        const fieldErrors = validate({ [name]: values[name] });
        if (fieldErrors[name]) {
          setErrors((prev) => ({ ...prev, [name]: fieldErrors[name] }));
        }
      }
    },
    [values, validate],
  );

  const setFieldValue = useCallback(
    (name, value) => {
      handleChange(name, value);
    },
    [handleChange],
  );

  const setFieldError = useCallback((name, error) => {
    setErrors((prev) => ({ ...prev, [name]: error }));
  }, []);

  const setErrorsFromApi = useCallback((apiErrors) => {
    const validationErrors = getValidationErrors(apiErrors);
    setErrors(validationErrors);
  }, []);

  const reset = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
    setIsSubmitting(false);
  }, [initialValues]);

  const handleSubmit = useCallback(
    async (e) => {
      if (e) {
        e.preventDefault();
      }

      // Validate all fields
      if (validate) {
        const validationErrors = validate(values);
        if (Object.keys(validationErrors).length > 0) {
          setErrors(validationErrors);
          // Mark all fields as touched
          const allTouched = Object.keys(values).reduce((acc, key) => {
            acc[key] = true;
            return acc;
          }, {});
          setTouched(allTouched);
          return;
        }
      }

      setIsSubmitting(true);
      setErrors({});

      try {
        await onSubmit(values);
      } catch (error) {
        // Handle validation errors from API
        if (error.response?.status === 400 || error.response?.status === 422) {
          setErrorsFromApi(error);
        } else {
          // Other errors are handled by error handler
          throw error;
        }
      } finally {
        setIsSubmitting(false);
      }
    },
    [values, validate, onSubmit, setErrorsFromApi],
  );

  return {
    values,
    errors,
    touched,
    isSubmitting,
    handleChange,
    handleBlur,
    handleSubmit,
    setFieldValue,
    setFieldError,
    setErrorsFromApi,
    reset,
  };
}
