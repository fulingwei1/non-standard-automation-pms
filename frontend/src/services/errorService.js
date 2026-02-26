/**
 * Error Service - Re-exports from centralized errorHandler
 * 
 * @deprecated Import from '@/utils/errorHandler' directly
 */
export {
  ERROR_TYPES,
  formatErrorMessage,
  showError,
  showSuccess,
  showWarning,
  showInfo,
  showErrorModal,
  getApiErrorMessage as handleApiError,
  withErrorHandling,
} from '../utils/errorHandler';

export { default } from '../utils/errorHandler';
