import { describe, expect, it } from "vitest";
import {
  combine,
  email,
  maxLength,
  maxValue,
  minLength,
  minValue,
  number,
  required,
  url,
} from "./validators";

describe("validators", () => {
  describe("required", () => {
    it("should return error for empty values", () => {
      expect(required("")).toBe("此字段为必填项");
      expect(required("   ")).toBe("此字段为必填项");
      expect(required(null)).toBe("此字段为必填项");
      expect(required(undefined)).toBe("此字段为必填项");
    });

    it("should return undefined for non-empty values", () => {
      expect(required("a")).toBeUndefined();
      expect(required("hello")).toBeUndefined();
      expect(required("123")).toBeUndefined();
    });

    it("should treat 0 and false as empty (current implementation)", () => {
      expect(required(0)).toBe("此字段为必填项");
      expect(required(false)).toBe("此字段为必填项");
    });

    it("should handle objects and arrays", () => {
      expect(required({})).toBeUndefined();
      expect(required([])).toBeUndefined();
      expect(required({ key: "value" })).toBeUndefined();
      expect(required([1, 2, 3])).toBeUndefined();
    });

    it("should handle numbers", () => {
      expect(required(1)).toBeUndefined();
      expect(required(-1)).toBeUndefined();
      expect(required(100)).toBeUndefined();
    });
  });

  describe("email", () => {
    it("should accept empty string", () => {
      expect(email("")).toBeUndefined();
      expect(email(null)).toBeUndefined();
      expect(email(undefined)).toBeUndefined();
    });

    it("should reject invalid email formats", () => {
      expect(email("not-an-email")).toBe("请输入有效的邮箱地址");
      expect(email("missing@")).toBe("请输入有效的邮箱地址");
      expect(email("@missing.com")).toBe("请输入有效的邮箱地址");
      expect(email("no-at-sign.com")).toBe("请输入有效的邮箱地址");
      expect(email("spaces in@email.com")).toBe("请输入有效的邮箱地址");
    });

    it("should accept valid email formats", () => {
      expect(email("a@b.com")).toBeUndefined();
      expect(email("test@example.com")).toBeUndefined();
      expect(email("user.name@domain.co.uk")).toBeUndefined();
      expect(email("user+tag@example.com")).toBeUndefined();
      expect(email("123@456.com")).toBeUndefined();
    });
  });

  describe("number", () => {
    it("should accept empty values", () => {
      expect(number("")).toBeUndefined();
      expect(number(null)).toBeUndefined();
      expect(number(undefined)).toBeUndefined();
    });

    it("should reject non-numeric strings", () => {
      expect(number("abc")).toBe("请输入有效的数字");
      expect(number("12abc")).toBe("请输入有效的数字");
      expect(number("abc12")).toBe("请输入有效的数字");
    });

    it("should accept numeric strings", () => {
      expect(number("1")).toBeUndefined();
      expect(number("123")).toBeUndefined();
      expect(number("0")).toBeUndefined();
      expect(number("-1")).toBeUndefined();
      expect(number("3.14")).toBeUndefined();
    });

    it("should accept numeric values", () => {
      expect(number(1)).toBeUndefined();
      expect(number(0)).toBeUndefined();
      expect(number(-1)).toBeUndefined();
      expect(number(3.14)).toBeUndefined();
    });
  });

  describe("minValue", () => {
    it("should accept empty values", () => {
      const validator = minValue(5);
      expect(validator("")).toBeUndefined();
      expect(validator(null)).toBeUndefined();
      expect(validator(undefined)).toBeUndefined();
    });

    it("should reject values below minimum", () => {
      const validator = minValue(10);
      expect(validator("5")).toBe("值必须大于或等于 10");
      expect(validator("9")).toBe("值必须大于或等于 10");
      expect(validator(5)).toBe("值必须大于或等于 10");
    });

    it("should accept values at or above minimum", () => {
      const validator = minValue(10);
      expect(validator("10")).toBeUndefined();
      expect(validator("11")).toBeUndefined();
      expect(validator(10)).toBeUndefined();
      expect(validator(100)).toBeUndefined();
    });

    it("should work with negative numbers", () => {
      const validator = minValue(-5);
      expect(validator("-10")).toBe("值必须大于或等于 -5");
      expect(validator("-5")).toBeUndefined();
      expect(validator("0")).toBeUndefined();
    });

    it("should work with decimal numbers", () => {
      const validator = minValue(3.5);
      expect(validator("3.4")).toBe("值必须大于或等于 3.5");
      expect(validator("3.5")).toBeUndefined();
      expect(validator("3.6")).toBeUndefined();
    });
  });

  describe("maxValue", () => {
    it("should accept empty values", () => {
      const validator = maxValue(5);
      expect(validator("")).toBeUndefined();
      expect(validator(null)).toBeUndefined();
      expect(validator(undefined)).toBeUndefined();
    });

    it("should reject values above maximum", () => {
      const validator = maxValue(10);
      expect(validator("11")).toBe("值必须小于或等于 10");
      expect(validator("100")).toBe("值必须小于或等于 10");
      expect(validator(15)).toBe("值必须小于或等于 10");
    });

    it("should accept values at or below maximum", () => {
      const validator = maxValue(10);
      expect(validator("10")).toBeUndefined();
      expect(validator("9")).toBeUndefined();
      expect(validator(10)).toBeUndefined();
      expect(validator(0)).toBeUndefined();
    });

    it("should work with negative numbers", () => {
      const validator = maxValue(-5);
      expect(validator("-4")).toBe("值必须小于或等于 -5");
      expect(validator("-5")).toBeUndefined();
      expect(validator("-10")).toBeUndefined();
    });

    it("should work with decimal numbers", () => {
      const validator = maxValue(3.5);
      expect(validator("3.6")).toBe("值必须小于或等于 3.5");
      expect(validator("3.5")).toBeUndefined();
      expect(validator("3.4")).toBeUndefined();
    });
  });

  describe("minLength", () => {
    it("should accept empty values", () => {
      const validator = minLength(5);
      expect(validator("")).toBeUndefined();
      expect(validator(null)).toBeUndefined();
      expect(validator(undefined)).toBeUndefined();
    });

    it("should reject strings shorter than minimum", () => {
      const validator = minLength(5);
      expect(validator("a")).toBe("至少需要 5 个字符");
      expect(validator("ab")).toBe("至少需要 5 个字符");
      expect(validator("abcd")).toBe("至少需要 5 个字符");
    });

    it("should accept strings at or above minimum length", () => {
      const validator = minLength(5);
      expect(validator("abcde")).toBeUndefined();
      expect(validator("abcdef")).toBeUndefined();
      expect(validator("hello world")).toBeUndefined();
    });

    it("should handle Chinese characters", () => {
      const validator = minLength(3);
      expect(validator("你好")).toBe("至少需要 3 个字符");
      expect(validator("你好啊")).toBeUndefined();
    });
  });

  describe("maxLength", () => {
    it("should accept empty values", () => {
      const validator = maxLength(5);
      expect(validator("")).toBeUndefined();
      expect(validator(null)).toBeUndefined();
      expect(validator(undefined)).toBeUndefined();
    });

    it("should reject strings longer than maximum", () => {
      const validator = maxLength(5);
      expect(validator("abcdef")).toBe("最多 5 个字符");
      expect(validator("hello world")).toBe("最多 5 个字符");
    });

    it("should accept strings at or below maximum length", () => {
      const validator = maxLength(5);
      expect(validator("abcde")).toBeUndefined();
      expect(validator("abcd")).toBeUndefined();
      expect(validator("a")).toBeUndefined();
    });

    it("should handle Chinese characters", () => {
      const validator = maxLength(3);
      expect(validator("你好")).toBeUndefined();
      expect(validator("你好啊")).toBeUndefined();
      expect(validator("你好啊朋友")).toBe("最多 3 个字符");
    });
  });

  describe("url", () => {
    it("should accept empty values", () => {
      expect(url("")).toBeUndefined();
      expect(url(null)).toBeUndefined();
      expect(url(undefined)).toBeUndefined();
    });

    it("should reject invalid URLs", () => {
      expect(url("not-a-url")).toBe("请输入有效的 URL");
      expect(url("ftp://example.com")).toBe("请输入有效的 URL");
      expect(url("//example.com")).toBe("请输入有效的 URL");
      expect(url("http://")).toBe("请输入有效的 URL");
    });

    it("should accept valid HTTP URLs", () => {
      expect(url("http://example.com")).toBeUndefined();
      expect(url("http://www.example.com")).toBeUndefined();
      expect(url("http://example.com/path")).toBeUndefined();
      expect(url("http://example.com:8080")).toBeUndefined();
    });

    it("should accept valid HTTPS URLs", () => {
      expect(url("https://example.com")).toBeUndefined();
      expect(url("https://www.example.com")).toBeUndefined();
      expect(url("https://example.com/path?query=value")).toBeUndefined();
      expect(url("https://sub.domain.example.com")).toBeUndefined();
    });
  });

  describe("combine", () => {
    it("should return first error encountered", () => {
      const validator = combine(required, email);
      expect(validator("")).toBe("此字段为必填项");
      expect(validator("not-an-email")).toBe("请输入有效的邮箱地址");
      expect(validator("a@b.com")).toBeUndefined();
    });

    it("should pass through all validators if all pass", () => {
      const validator = combine(required, minLength(5), maxLength(10));
      expect(validator("hello")).toBeUndefined();
      expect(validator("hello world")).toBeUndefined();
    });

    it("should stop at first error", () => {
      const validator = combine(required, minLength(5), email);
      // Empty string fails required check first
      expect(validator("")).toBe("此字段为必填项");
      // Short string fails minLength, doesn't check email
      expect(validator("ab")).toBe("至少需要 5 个字符");
      // Valid length but invalid email
      expect(validator("hello")).toBe("请输入有效的邮箱地址");
    });

    it("should work with three validators", () => {
      const validator = combine(required, number, minValue(10));
      expect(validator("")).toBe("此字段为必填项");
      expect(validator("abc")).toBe("请输入有效的数字");
      expect(validator("5")).toBe("值必须大于或等于 10");
      expect(validator("15")).toBeUndefined();
    });

    it("should work with single validator", () => {
      const validator = combine(required);
      expect(validator("")).toBe("此字段为必填项");
      expect(validator("hello")).toBeUndefined();
    });

    it("should return undefined for no validators", () => {
      const validator = combine();
      expect(validator("anything")).toBeUndefined();
      expect(validator("")).toBeUndefined();
    });
  });
});
