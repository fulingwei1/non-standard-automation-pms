/**
 * Common validation functions
 */

/**
 * Required field validator
 */
export function required(value, message = "此字段为必填项") {
  if (!value || (typeof value === "string" && value.trim() === "")) {
    return message;
  }
  return undefined;
}

/**
 * Email validator
 */
export function email(value, message = "请输入有效的邮箱地址") {
  if (!value) return undefined;
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(value)) {
    return message;
  }
  return undefined;
}

/**
 * Min length validator
 */
export function minLength(min, message) {
  return (value) => {
    if (!value) return undefined;
    if (value.length < min) {
      return message || `至少需要 ${min} 个字符`;
    }
    return undefined;
  };
}

/**
 * Max length validator
 */
export function maxLength(max, message) {
  return (value) => {
    if (!value) return undefined;
    if (value.length > max) {
      return message || `最多 ${max} 个字符`;
    }
    return undefined;
  };
}

/**
 * Number validator
 */
export function number(value, message = "请输入有效的数字") {
  if (!value) return undefined;
  if (isNaN(Number(value))) {
    return message;
  }
  return undefined;
}

/**
 * Min value validator
 */
export function minValue(min, message) {
  return (value) => {
    if (!value) return undefined;
    const num = Number(value);
    if (isNaN(num) || num < min) {
      return message || `值必须大于或等于 ${min}`;
    }
    return undefined;
  };
}

/**
 * Max value validator
 */
export function maxValue(max, message) {
  return (value) => {
    if (!value) return undefined;
    const num = Number(value);
    if (isNaN(num) || num > max) {
      return message || `值必须小于或等于 ${max}`;
    }
    return undefined;
  };
}

/**
 * Phone number validator
 */
export function phone(value, message = "请输入有效的手机号码") {
  if (!value) return undefined;
  const phoneRegex = /^1[3-9]\d{9}$/;
  if (!phoneRegex.test(value)) {
    return message;
  }
  return undefined;
}

/**
 * URL validator
 */
export function url(value, message = "请输入有效的 URL") {
  if (!value) return undefined;
  try {
    new URL(value);
    return undefined;
  } catch {
    return message;
  }
}

/**
 * Date validator
 */
export function date(value, message = "请输入有效的日期") {
  if (!value) return undefined;
  const date = new Date(value);
  if (isNaN(date.getTime())) {
    return message;
  }
  return undefined;
}

/**
 * Combine multiple validators
 */
export function combine(...validators) {
  return (value) => {
    for (const validator of validators) {
      const error = validator(value);
      if (error) return error;
    }
    return undefined;
  };
}

/**
 * Create validation function for form
 */
export function createValidator(validations) {
  return (values) => {
    const errors = {};

    for (const [field, validators] of Object.entries(validations)) {
      const value = values[field];

      // Handle array of validators
      const validatorList = Array.isArray(validators)
        ? validators
        : [validators];

      for (const validator of validatorList) {
        if (typeof validator === "function") {
          const error = validator(value, values);
          if (error) {
            errors[field] = error;
            break; // Stop at first error
          }
        }
      }
    }

    return errors;
  };
}
