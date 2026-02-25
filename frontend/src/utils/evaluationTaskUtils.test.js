import { describe, expect, it } from "vitest";
import {
  getStatusBadge,
  getTypeBadge,
  getUrgencyColor,
  calculateTaskStatistics,
  filterTasks,
} from "./evaluationTaskUtils";
import { Clock, CheckCircle2, Users, Briefcase } from "lucide-react";

describe("evaluationTaskUtils", () => {
  describe("getStatusBadge", () => {
    it("should return PENDING badge configuration", () => {
      const badge = getStatusBadge("PENDING");
      expect(badge.label).toBe("待评价");
      expect(badge.color).toBe("bg-amber-500/20 text-amber-400");
      expect(badge.icon).toBe(Clock);
    });

    it("should return COMPLETED badge configuration", () => {
      const badge = getStatusBadge("COMPLETED");
      expect(badge.label).toBe("已完成");
      expect(badge.color).toBe("bg-emerald-500/20 text-emerald-400");
      expect(badge.icon).toBe(CheckCircle2);
    });

    it("should return PENDING badge for unknown status", () => {
      const badge = getStatusBadge("UNKNOWN");
      expect(badge.label).toBe("待评价");
      expect(badge.color).toBe("bg-amber-500/20 text-amber-400");
    });

    it("should return PENDING badge for null/undefined", () => {
      expect(getStatusBadge(null).label).toBe("待评价");
      expect(getStatusBadge(undefined).label).toBe("待评价");
    });
  });

  describe("getTypeBadge", () => {
    it("should return department badge for 'dept' type", () => {
      const badge = getTypeBadge("dept");
      expect(badge.label).toBe("部门评价");
      expect(badge.color).toBe("bg-blue-500/20 text-blue-400");
      expect(badge.icon).toBe(Users);
    });

    it("should return department badge for 'DEPT_MANAGER' type", () => {
      const badge = getTypeBadge("DEPT_MANAGER");
      expect(badge.label).toBe("部门评价");
      expect(badge.color).toBe("bg-blue-500/20 text-blue-400");
      expect(badge.icon).toBe(Users);
    });

    it("should return project badge with project name", () => {
      const badge = getTypeBadge("project", "项目A");
      expect(badge.label).toBe("项目评价: 项目A");
      expect(badge.color).toBe("bg-purple-500/20 text-purple-400");
      expect(badge.icon).toBe(Briefcase);
    });

    it("should return project badge without project name", () => {
      const badge = getTypeBadge("project");
      expect(badge.label).toBe("项目评价: 未知项目");
      expect(badge.color).toBe("bg-purple-500/20 text-purple-400");
      expect(badge.icon).toBe(Briefcase);
    });

    it("should return project badge for unknown type", () => {
      const badge = getTypeBadge("unknown", "测试项目");
      expect(badge.label).toBe("项目评价: 测试项目");
    });
  });

  describe("getUrgencyColor", () => {
    it("should return slate color for expired tasks", () => {
      expect(getUrgencyColor(-1)).toBe("text-slate-500");
      expect(getUrgencyColor(-10)).toBe("text-slate-500");
    });

    it("should return red color for urgent tasks (<=2 days)", () => {
      expect(getUrgencyColor(0)).toBe("text-red-400");
      expect(getUrgencyColor(1)).toBe("text-red-400");
      expect(getUrgencyColor(2)).toBe("text-red-400");
    });

    it("should return amber color for warning tasks (3-5 days)", () => {
      expect(getUrgencyColor(3)).toBe("text-amber-400");
      expect(getUrgencyColor(4)).toBe("text-amber-400");
      expect(getUrgencyColor(5)).toBe("text-amber-400");
    });

    it("should return emerald color for normal tasks (>5 days)", () => {
      expect(getUrgencyColor(6)).toBe("text-emerald-400");
      expect(getUrgencyColor(10)).toBe("text-emerald-400");
      expect(getUrgencyColor(30)).toBe("text-emerald-400");
    });
  });

  describe("calculateTaskStatistics", () => {
    it("should calculate statistics for empty task list", () => {
      const stats = calculateTaskStatistics([]);
      expect(stats.total).toBe(0);
      expect(stats.pending).toBe(0);
      expect(stats.completed).toBe(0);
      expect(stats.dept).toBe(0);
      expect(stats.project).toBe(0);
      expect(stats.avgScore).toBe(0);
    });

    it("should calculate statistics for task list", () => {
      const tasks = [
        { status: "PENDING", evaluationType: "dept", score: 80 },
        { status: "COMPLETED", evaluationType: "project", score: 90 },
        { status: "pending", evaluator_type: "DEPT_MANAGER", score: 85 },
        { status: "completed", evaluator_type: "PROJECT_MANAGER", score: null },
      ];

      const stats = calculateTaskStatistics(tasks);

      expect(stats.total).toBe(4);
      expect(stats.pending).toBe(2);
      expect(stats.completed).toBe(2);
      expect(stats.dept).toBe(2);
      expect(stats.project).toBe(2);
      expect(stats.avgScore).toBeCloseTo(85, 2); // (80+90+85)/3
    });

    it("should handle mixed case status", () => {
      const tasks = [
        { status: "PeNdInG", evaluationType: "dept" },
        { status: "CoMpLeTeD", evaluationType: "project" },
      ];

      const stats = calculateTaskStatistics(tasks);
      expect(stats.pending).toBe(1);
      expect(stats.completed).toBe(1);
    });

    it("should handle missing status", () => {
      const tasks = [{ evaluationType: "dept" }, { evaluationType: "project" }];

      const stats = calculateTaskStatistics(tasks);
      expect(stats.pending).toBe(0);
      expect(stats.completed).toBe(0);
    });

    it("should handle null scores", () => {
      const tasks = [
        { score: null },
        { score: undefined },
        { score: 90 },
        { score: 80 },
      ];

      const stats = calculateTaskStatistics(tasks);
      expect(stats.avgScore).toBe(85); // (90+80)/2
    });

    it("should handle all null scores", () => {
      const tasks = [{ score: null }, { score: undefined }];

      const stats = calculateTaskStatistics(tasks);
      expect(stats.avgScore).toBe(0);
    });
  });

  describe("filterTasks", () => {
    const tasks = [
      {
        employeeName: "张三",
        evaluationType: "dept",
        status: "PENDING",
      },
      {
        employee_name: "李四",
        evaluator_type: "PROJECT_MANAGER",
        status: "COMPLETED",
      },
      {
        employeeName: "王五",
        evaluationType: "DEPT_MANAGER",
        status: "PENDING",
      },
      {
        employee_name: "赵六",
        evaluator_type: "project",
        status: "COMPLETED",
      },
    ];

    it("should return all tasks without filters", () => {
      const result = filterTasks(tasks, "", "all");
      expect(result).toHaveLength(4);
    });

    it("should filter by search term", () => {
      const result = filterTasks(tasks, "张三", "all");
      expect(result).toHaveLength(1);
      expect(result[0].employeeName).toBe("张三");
    });

    it("should filter by search term (case insensitive)", () => {
      const result = filterTasks(tasks, "李", "all");
      expect(result).toHaveLength(1);
      expect(result[0].employee_name).toBe("李四");
    });

    it("should filter by dept type", () => {
      const result = filterTasks(tasks, "", "dept");
      expect(result).toHaveLength(2);
      expect(
        result.every(
          (t) =>
            t.evaluationType === "dept" ||
            t.evaluator_type === "DEPT_MANAGER" ||
            t.evaluationType === "DEPT_MANAGER"
        )
      ).toBe(true);
    });

    it("should filter by project type", () => {
      const result = filterTasks(tasks, "", "project");
      expect(result).toHaveLength(2);
      expect(
        result.every(
          (t) =>
            t.evaluationType === "project" ||
            t.evaluator_type === "PROJECT_MANAGER" ||
            t.evaluator_type === "project"
        )
      ).toBe(true);
    });

    it("should filter by both search term and type", () => {
      const result = filterTasks(tasks, "李", "project");
      expect(result).toHaveLength(1);
      expect(result[0].employee_name).toBe("李四");
    });

    it("should return empty array when no match", () => {
      const result = filterTasks(tasks, "不存在的员工", "all");
      expect(result).toHaveLength(0);
    });

    it("should handle missing employee name", () => {
      const tasksWithMissingName = [
        { evaluationType: "dept" },
        { employeeName: "张三", evaluationType: "project" },
      ];

      const result = filterTasks(tasksWithMissingName, "张", "all");
      expect(result).toHaveLength(1);
      expect(result[0].employeeName).toBe("张三");
    });

    it("should handle empty search term as no filter", () => {
      const result = filterTasks(tasks, "", "all");
      expect(result).toHaveLength(4);
    });
  });
});
