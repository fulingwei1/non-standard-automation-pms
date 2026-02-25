import { describe, expect, it, vi } from "vitest";
import {
  getResponseData,
  getPaginatedResponse,
  getListResponse,
  getItems,
  handleResponse,
  getItemsCompat,
} from "./apiResponse";

// Mock responseFormatter functions
vi.mock("./responseFormatter.js", () => ({
  extractData: vi.fn((data) => data?.data || data),
  extractItems: vi.fn((data) => {
    if (Array.isArray(data?.items)) return data.items;
    if (Array.isArray(data)) return data;
    return [];
  }),
  extractPaginatedData: vi.fn((data) => ({
    items: data?.items || [],
    total: data?.total || 0,
    page: data?.page || 1,
    pageSize: data?.pageSize || 10,
  })),
  extractListData: vi.fn((data) => ({
    items: data?.items || [],
    total: data?.total || 0,
  })),
}));

describe("apiResponse", () => {
  describe("getResponseData", () => {
    it("should extract data from axios response", () => {
      const response = { data: { id: 1, name: "test" } };
      const result = getResponseData(response);
      expect(result).toEqual({ id: 1, name: "test" });
    });

    it("should handle direct data object", () => {
      const data = { id: 1, name: "test" };
      const result = getResponseData(data);
      expect(result).toEqual({ id: 1, name: "test" });
    });

    it("should handle nested data object", () => {
      const response = { data: { data: { id: 1, name: "test" } } };
      const result = getResponseData(response);
      expect(result).toEqual({ id: 1, name: "test" });
    });

    it("should handle undefined response", () => {
      const result = getResponseData(undefined);
      expect(result).toBeUndefined();
    });

    it("should handle null response", () => {
      const result = getResponseData(null);
      expect(result).toBeNull();
    });
  });

  describe("getPaginatedResponse", () => {
    it("should extract paginated data from response", () => {
      const response = {
        data: {
          items: [{ id: 1 }, { id: 2 }],
          total: 100,
          page: 1,
          pageSize: 10,
        },
      };
      const result = getPaginatedResponse(response);
      expect(result).toEqual({
        items: [{ id: 1 }, { id: 2 }],
        total: 100,
        page: 1,
        pageSize: 10,
      });
    });

    it("should handle direct data object", () => {
      const data = {
        items: [{ id: 1 }],
        total: 50,
        page: 2,
        pageSize: 20,
      };
      const result = getPaginatedResponse(data);
      expect(result).toEqual({
        items: [{ id: 1 }],
        total: 50,
        page: 2,
        pageSize: 20,
      });
    });

    it("should handle empty response", () => {
      const result = getPaginatedResponse({});
      expect(result).toEqual({
        items: [],
        total: 0,
        page: 1,
        pageSize: 10,
      });
    });
  });

  describe("getListResponse", () => {
    it("should extract list data from response", () => {
      const response = {
        data: {
          items: [{ id: 1 }, { id: 2 }],
          total: 2,
        },
      };
      const result = getListResponse(response);
      expect(result).toEqual({
        items: [{ id: 1 }, { id: 2 }],
        total: 2,
      });
    });

    it("should handle direct data object", () => {
      const data = {
        items: [{ id: 1 }],
        total: 1,
      };
      const result = getListResponse(data);
      expect(result).toEqual({
        items: [{ id: 1 }],
        total: 1,
      });
    });

    it("should handle empty response", () => {
      const result = getListResponse({});
      expect(result).toEqual({
        items: [],
        total: 0,
      });
    });
  });

  describe("getItems", () => {
    it("should extract items from response", () => {
      const response = {
        data: {
          items: [{ id: 1 }, { id: 2 }],
        },
      };
      const result = getItems(response);
      expect(result).toEqual([{ id: 1 }, { id: 2 }]);
    });

    it("should handle direct array", () => {
      const response = { data: [{ id: 1 }, { id: 2 }] };
      const result = getItems(response);
      expect(result).toEqual([{ id: 1 }, { id: 2 }]);
    });

    it("should handle empty response", () => {
      const result = getItems({});
      expect(result).toEqual([]);
    });
  });

  describe("handleResponse", () => {
    it("should handle 'single' type", () => {
      const response = { data: { id: 1, name: "test" } };
      const result = handleResponse(response, { type: "single" });
      expect(result).toEqual({ id: 1, name: "test" });
    });

    it("should handle 'paginated' type", () => {
      const response = {
        data: {
          items: [{ id: 1 }],
          total: 100,
          page: 1,
          pageSize: 10,
        },
      };
      const result = handleResponse(response, { type: "paginated" });
      expect(result).toEqual({
        items: [{ id: 1 }],
        total: 100,
        page: 1,
        pageSize: 10,
      });
    });

    it("should handle 'list' type", () => {
      const response = {
        data: {
          items: [{ id: 1 }],
          total: 1,
        },
      };
      const result = handleResponse(response, { type: "list" });
      expect(result).toEqual({
        items: [{ id: 1 }],
        total: 1,
      });
    });

    it("should handle 'items' type", () => {
      const response = {
        data: {
          items: [{ id: 1 }, { id: 2 }],
        },
      };
      const result = handleResponse(response, { type: "items" });
      expect(result).toEqual([{ id: 1 }, { id: 2 }]);
    });

    it("should auto-detect paginated response", () => {
      const response = {
        data: {
          items: [{ id: 1 }],
          page: 1,
          total: 100,
        },
      };
      const result = handleResponse(response, { type: "auto" });
      expect(result).toEqual({
        items: [{ id: 1 }],
        total: 100,
        page: 1,
        pageSize: 10,
      });
    });

    it("should auto-detect list response", () => {
      const response = {
        data: {
          items: [{ id: 1 }],
          total: 1,
        },
      };
      const result = handleResponse(response, { type: "auto" });
      expect(result).toEqual({
        items: [{ id: 1 }],
        total: 1,
      });
    });

    it("should auto-detect single object response", () => {
      const response = {
        data: { id: 1, name: "test" },
      };
      const result = handleResponse(response, { type: "auto" });
      expect(result).toEqual({ id: 1, name: "test" });
    });

    it("should default to auto mode", () => {
      const response = {
        data: { id: 1, name: "test" },
      };
      const result = handleResponse(response);
      expect(result).toEqual({ id: 1, name: "test" });
    });
  });

  describe("getItemsCompat", () => {
    it("should extract items from response", () => {
      const response = {
        data: {
          items: [{ id: 1 }, { id: 2 }],
        },
      };
      const result = getItemsCompat(response);
      expect(result).toEqual([{ id: 1 }, { id: 2 }]);
    });

    it("should handle direct array", () => {
      const response = { data: [{ id: 1 }, { id: 2 }] };
      const result = getItemsCompat(response);
      expect(result).toEqual([{ id: 1 }, { id: 2 }]);
    });

    it("should handle nested data array", () => {
      const response = {
        data: {
          data: [{ id: 1 }, { id: 2 }],
        },
      };
      const result = getItemsCompat(response);
      expect(result).toEqual([{ id: 1 }, { id: 2 }]);
    });

    it("should return empty array for empty response", () => {
      const result = getItemsCompat({});
      expect(result).toEqual([]);
    });

    it("should return empty array for object without items", () => {
      const response = { data: { id: 1, name: "test" } };
      const result = getItemsCompat(response);
      expect(result).toEqual([]);
    });

    it("should return empty array for null response", () => {
      const result = getItemsCompat(null);
      expect(result).toEqual([]);
    });

    it("should return empty array for undefined response", () => {
      const result = getItemsCompat(undefined);
      expect(result).toEqual([]);
    });
  });
});
