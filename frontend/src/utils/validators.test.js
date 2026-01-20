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
  it("required() returns error for empty values", () => {
    expect(required("")).toBe("此字段为必填项");
    expect(required("   ")).toBe("此字段为必填项");
    expect(required(null)).toBe("此字段为必填项");
    expect(required(undefined)).toBe("此字段为必填项");
  });

  it("required() returns undefined for non-empty values", () => {
    expect(required("a")).toBeUndefined();
    // 注意：当前实现对 0/false 也视为“未填写”
    expect(required(0)).toBe("此字段为必填项");
    expect(required(false)).toBe("此字段为必填项");
  });

  it("email() validates email format", () => {
    expect(email("")).toBeUndefined();
    expect(email("not-an-email")).toBe("请输入有效的邮箱地址");
    expect(email("a@b.com")).toBeUndefined();
  });

  it("number()/minValue()/maxValue() validates numeric constraints", () => {
    expect(number("")).toBeUndefined();
    expect(number("abc")).toBe("请输入有效的数字");
    expect(number("1")).toBeUndefined();

    expect(minValue(2)("1")).toBe("值必须大于或等于 2");
    expect(minValue(2)("2")).toBeUndefined();

    expect(maxValue(2)("3")).toBe("值必须小于或等于 2");
    expect(maxValue(2)("2")).toBeUndefined();
  });

  it("minLength()/maxLength() validates string length", () => {
    expect(minLength(2)("a")).toBe("至少需要 2 个字符");
    expect(minLength(2)("ab")).toBeUndefined();
    expect(maxLength(2)("abc")).toBe("最多 2 个字符");
    expect(maxLength(2)("ab")).toBeUndefined();
  });

  it("url() validates url", () => {
    expect(url("")).toBeUndefined();
    expect(url("not-a-url")).toBe("请输入有效的 URL");
    expect(url("https://example.com")).toBeUndefined();
  });

  it("combine() returns first error", () => {
    const validator = combine(required, email);
    expect(validator("")).toBe("此字段为必填项");
    expect(validator("not-an-email")).toBe("请输入有效的邮箱地址");
    expect(validator("a@b.com")).toBeUndefined();
  });
});
