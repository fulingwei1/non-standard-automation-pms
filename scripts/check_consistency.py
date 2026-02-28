import os


def check_refactoring_consistency(base_dir):
    print(f"Checking consistency in: {base_dir}")
    print("-" * 50)

    pages_dir = os.path.join(base_dir, "frontend", "src", "pages")
    if not os.path.exists(pages_dir):
        print(f"Error: Directory not found: {pages_dir}")
        return

    report = {
        "missing_hooks_dir": [],
        "missing_constants": [],
        "empty_hooks_dir": [],
        "missing_hook_index": [],
        "naming_issues": [],
        "good_pages": 0,
        "total_checked": 0,
    }

    # 遍历所有页面目录
    for item in sorted(os.listdir(pages_dir)):
        page_path = os.path.join(pages_dir, item)
        if not os.path.isdir(page_path):
            continue

        # 忽略非页面组件目录（如 components 或其他工具目录）
        if item in ["components", "hooks", "utils", "assets", "layout"]:
            continue

        report["total_checked"] += 1
        page_issues = []

        # 1. 检查 hooks 目录
        hooks_dir = os.path.join(page_path, "hooks")
        if not os.path.exists(hooks_dir):
            # 只有当目录下有主要的 .jsx 文件时才认为是一个需要重构的页面
            main_jsx = os.path.join(page_path, "index.jsx")
            # 兼容旧结构，有些页面可能直接是 PageName.jsx 放在 pages 根目录，
            # 但我们这里只检查已经有目录结构的页面
            if os.path.exists(main_jsx) or any(
                f.endswith(".jsx") for f in os.listdir(page_path)
            ):
                # 如果是新创建的目录结构，应该有 hooks
                pass  # 暂时不标记为错误，因为有些小页面可能不需要
        else:
            # check empty
            hooks_files = [f for f in os.listdir(hooks_dir) if f.endswith(".js")]
            if not hooks_files:
                report["empty_hooks_dir"].append(item)
                page_issues.append("Empty hooks directory")
            else:
                # check index.js
                if "index.js" not in hooks_files:
                    report["missing_hook_index"].append(item)
                    page_issues.append("Missing index.js in hooks")
                else:
                    # Check hook naming convention (use[Name].js)
                    for hook_file in hooks_files:
                        if hook_file == "index.js":
                            continue
                        if not hook_file.startswith("use"):
                            report["naming_issues"].append(f"{item}/hooks/{hook_file}")
                            page_issues.append(f"Invalid hook name: {hook_file}")

        # 2. 检查 constants.js
        constants_file = os.path.join(page_path, "constants.js")
        if not os.path.exists(constants_file):
            # 同样，只有已经开始重构的页面才会有这个
            pass

        if not page_issues:
            report["good_pages"] += 1

    return report


def print_report(report):
    print(f"\nTotal Pages Checked: {report['total_checked']}")
    print(f"Pages with Clean Structure: {report['good_pages']}")
    print("-" * 30)

    if report["empty_hooks_dir"]:
        print("\n[!] Empty Hooks Directory (Created but unused?):")
        for p in report["empty_hooks_dir"]:
            print(f"  - {p}")

    if report["missing_hook_index"]:
        print("\n[!] Missing index.js in Hooks Directory:")
        for p in report["missing_hook_index"]:
            print(f"  - {p}")

    if report["naming_issues"]:
        print("\n[!] Hook Naming Issues (Should start with 'use'):")
        for p in report["naming_issues"]:
            print(f"  - {p}")

    print("\nCheck completed.")


if __name__ == "__main__":
    report = check_refactoring_consistency(os.getcwd())
    print_report(report)
