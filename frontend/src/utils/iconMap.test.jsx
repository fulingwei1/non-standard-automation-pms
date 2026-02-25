import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render } from "@testing-library/react";
import { iconMap, DynamicIcon, getIcon } from "./iconMap";
import {
  CheckCircle2,
  FileText,
  Clock,
  Truck,
  AlertTriangle,
  Package,
  Trash2,
  Eye,
  Edit3,
  AlertCircle,
  XCircle,
  Info,
  Circle,
  MessageSquare,
  CheckCircle,
  Send,
} from "lucide-react";

describe("iconMap", () => {
  describe("iconMap object", () => {
    it("should contain all expected icons", () => {
      expect(iconMap.CheckCircle2).toBe(CheckCircle2);
      expect(iconMap.FileText).toBe(FileText);
      expect(iconMap.Clock).toBe(Clock);
      expect(iconMap.Truck).toBe(Truck);
      expect(iconMap.AlertTriangle).toBe(AlertTriangle);
      expect(iconMap.Package).toBe(Package);
      expect(iconMap.Trash2).toBe(Trash2);
      expect(iconMap.Eye).toBe(Eye);
      expect(iconMap.Edit3).toBe(Edit3);
      expect(iconMap.AlertCircle).toBe(AlertCircle);
      expect(iconMap.XCircle).toBe(XCircle);
      expect(iconMap.Info).toBe(Info);
      expect(iconMap.Circle).toBe(Circle);
      expect(iconMap.MessageSquare).toBe(MessageSquare);
      expect(iconMap.CheckCircle).toBe(CheckCircle);
      expect(iconMap.Send).toBe(Send);
    });

    it("should be an object", () => {
      expect(typeof iconMap).toBe("object");
    });

    it("should have at least 16 icons", () => {
      expect(Object.keys(iconMap).length).toBeGreaterThanOrEqual(16);
    });
  });

  describe("DynamicIcon component", () => {
    let consoleWarnSpy;

    beforeEach(() => {
      consoleWarnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
    });

    afterEach(() => {
      consoleWarnSpy.mockRestore();
    });

    it("should render correct icon for valid name", () => {
      const { container } = render(<DynamicIcon name="CheckCircle2" />);
      expect(container.querySelector("svg")).toBeInTheDocument();
    });

    it("should render Clock icon", () => {
      const { container } = render(
        <DynamicIcon name="Clock" className="test-class" />
      );
      const svg = container.querySelector("svg");
      expect(svg).toBeInTheDocument();
      expect(svg).toHaveClass("test-class");
    });

    it("should pass props to icon component", () => {
      const { container } = render(
        <DynamicIcon name="FileText" className="w-4 h-4" data-testid="icon" />
      );
      const svg = container.querySelector("svg");
      expect(svg).toHaveClass("w-4");
      expect(svg).toHaveClass("h-4");
    });

    it("should return null for invalid icon name", () => {
      const { container } = render(<DynamicIcon name="InvalidIcon" />);
      expect(container.firstChild).toBeNull();
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        "[DynamicIcon] 未找到图标: InvalidIcon"
      );
    });

    it("should return null when name is not provided", () => {
      const { container } = render(<DynamicIcon />);
      expect(container.firstChild).toBeNull();
    });

    it("should return null for null name", () => {
      const { container } = render(<DynamicIcon name={null} />);
      expect(container.firstChild).toBeNull();
    });

    it("should return null for undefined name", () => {
      const { container } = render(<DynamicIcon name={undefined} />);
      expect(container.firstChild).toBeNull();
    });

    it("should return null for empty string name", () => {
      const { container } = render(<DynamicIcon name="" />);
      expect(container.firstChild).toBeNull();
    });

    it("should warn for non-existent icon", () => {
      render(<DynamicIcon name="NonExistentIcon" />);
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        "[DynamicIcon] 未找到图标: NonExistentIcon"
      );
    });

    it("should handle all available icons", () => {
      const iconNames = Object.keys(iconMap);

      iconNames.forEach((name) => {
        const { container } = render(<DynamicIcon name={name} />);
        expect(container.querySelector("svg")).toBeInTheDocument();
      });
    });

    it("should pass size prop correctly", () => {
      const { container } = render(<DynamicIcon name="Edit3" size={24} />);
      const svg = container.querySelector("svg");
      expect(svg).toBeInTheDocument();
      // lucide-react icons accept size prop
    });

    it("should pass color prop correctly", () => {
      const { container } = render(
        <DynamicIcon name="AlertTriangle" color="red" />
      );
      const svg = container.querySelector("svg");
      expect(svg).toBeInTheDocument();
    });

    it("should handle multiple props", () => {
      const { container } = render(
        <DynamicIcon
          name="Truck"
          size={32}
          color="blue"
          className="custom-icon"
        />
      );
      const svg = container.querySelector("svg");
      expect(svg).toBeInTheDocument();
      expect(svg).toHaveClass("custom-icon");
    });
  });

  describe("getIcon function", () => {
    it("should return correct icon component for valid name", () => {
      expect(getIcon("CheckCircle2")).toBe(CheckCircle2);
      expect(getIcon("Clock")).toBe(Clock);
      expect(getIcon("FileText")).toBe(FileText);
    });

    it("should return Package icon for invalid name", () => {
      expect(getIcon("InvalidIcon")).toBe(Package);
    });

    it("should return Package icon for null", () => {
      expect(getIcon(null)).toBe(Package);
    });

    it("should return Package icon for undefined", () => {
      expect(getIcon(undefined)).toBe(Package);
    });

    it("should return Package icon for empty string", () => {
      expect(getIcon("")).toBe(Package);
    });

    it("should return Package icon for non-string input", () => {
      expect(getIcon(123)).toBe(Package);
      expect(getIcon({})).toBe(Package);
      expect(getIcon([])).toBe(Package);
    });

    it("should handle all available icons", () => {
      const iconNames = Object.keys(iconMap);

      iconNames.forEach((name) => {
        const IconComponent = getIcon(name);
        expect(IconComponent).toBe(iconMap[name]);
      });
    });

    it("should return a React component", () => {
      const IconComponent = getIcon("Clock");
      expect(typeof IconComponent).toBe("function");
      // It should be renderable
      const { container } = render(<IconComponent />);
      expect(container.querySelector("svg")).toBeInTheDocument();
    });
  });

  describe("integration", () => {
    it("should work together: getIcon and DynamicIcon", () => {
      const IconComponent = getIcon("AlertCircle");
      const { container: container1 } = render(<IconComponent />);
      const { container: container2 } = render(
        <DynamicIcon name="AlertCircle" />
      );

      expect(container1.querySelector("svg")).toBeInTheDocument();
      expect(container2.querySelector("svg")).toBeInTheDocument();
    });

    it("should handle fallback consistently", () => {
      const FallbackIcon = getIcon("NonExistent");
      expect(FallbackIcon).toBe(Package);

      const { container: container1 } = render(<FallbackIcon />);
      const { container: container2 } = render(<DynamicIcon name="Package" />);

      expect(container1.querySelector("svg")).toBeInTheDocument();
      expect(container2.querySelector("svg")).toBeInTheDocument();
    });
  });
});
