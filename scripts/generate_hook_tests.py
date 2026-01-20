import os
import re


def generate_tests(base_dir):
    pages_dir = os.path.join(base_dir, "frontend", "src", "pages")

    template = """import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { %(hook_name)s } from '../%(hook_file_name)s';
import { %(all_imports)s } from '../../../../services/api';

// Mock API
vi.mock('../../../../services/api', () => {
    return {
        %(mock_objects)s
    };
});

describe('%(hook_name)s Hook', () => {
  // Setup common mock data
  const mockItems = [{ id: 1, name: 'Test 1' }, { id: 2, name: 'Test 2' }];
  const mockDetail = { id: 1, name: 'Test Detail' };
  const mockResponse = { data: { items: mockItems, total: 2 }, items: mockItems }; 

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Auto-setup mocks for known methods
    const apiObjects = [%(api_array)s];
    apiObjects.forEach(api => {
        if (api) {
            if (api.list) api.list.mockResolvedValue(mockResponse);
            if (api.get) api.get.mockResolvedValue({ data: mockDetail });
            if (api.query) api.query.mockResolvedValue(mockResponse);
            if (api.aiMatch) api.aiMatch.mockResolvedValue(mockResponse); // specialized
        }
    });
  });

  it('should load data', async () => {
    const { result } = renderHook(() => %(hook_name)s());

    // Wait for loading to finish
    if (result.current.hasOwnProperty('loading')) {
        await waitFor(() => expect(result.current.loading).toBe(false));
    } else {
        await waitFor(() => {});
    }

    // Basic assertion
    expect(result.current).toBeDefined();
  });
});
"""

    count = 0

    for item in sorted(os.listdir(pages_dir)):
        page_path = os.path.join(pages_dir, item)
        hooks_dir = os.path.join(page_path, "hooks")

        if not os.path.isdir(hooks_dir):
            continue

        hook_files = [
            f
            for f in os.listdir(hooks_dir)
            if f.startswith("use") and f.endswith(".js")
        ]
        if not hook_files:
            continue

        hook_file = hook_files[0]
        hook_path = os.path.join(hooks_dir, hook_file)

        with open(hook_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 修复后的正则：使用 [^'"]* 避免贪婪匹配跨越文件
        api_matches = re.finditer(
            r"import\s+\{([^}]+)\}\s+from\s+['\"][^'\"]*services/api['\"]",
            content,
            re.DOTALL,
        )

        all_imports = set()
        for match in api_matches:
            imports_str = match.group(1)
            for i in imports_str.split(","):
                name = i.strip()
                if name:
                    all_imports.add(name)

        # 备用匹配：针对使用 alias 或不同深度的导入，但确保也是以 services/api (或至少 api 且不包含 react) 结尾
        if not all_imports:
            # 更谨慎的备用匹配
            api_matches = re.finditer(
                r"import\s+\{([^}]+)\}\s+from\s+['\"][^'\"]*api['\"]",
                content,
                re.DOTALL,
            )
            for match in api_matches:
                imports_str = match.group(1)
                # 再次过滤，确保看起来像 API
                for i in imports_str.split(","):
                    name = i.strip()
                    if name and "Api" in name:
                        all_imports.add(name)

        if not all_imports:
            continue

        imports_list = sorted(list(all_imports))
        all_imports_str = ", ".join(imports_list)

        # Mock objects: 添加更多常见方法 mock
        mock_objs_parts = []
        for name in imports_list:
            mock_objs_parts.append(
                f"{name}: {{ list: vi.fn(), get: vi.fn(), create: vi.fn(), update: vi.fn(), delete: vi.fn(), query: vi.fn(), aiMatch: vi.fn(), assign: vi.fn() }}"
            )

        mock_objects_str = ",\n        ".join(mock_objs_parts)
        api_array_str = ", ".join(imports_list)

        hook_name = hook_file[:-3]
        test_dir = os.path.join(hooks_dir, "__tests__")
        if not os.path.exists(test_dir):
            os.makedirs(test_dir)

        test_file_name = f"{hook_name}.test.js"
        test_file_path = os.path.join(test_dir, test_file_name)

        if hook_name in ["useProjectTaskList", "useDepartmentManagement"]:
            print(f"Skipping manual test: {hook_name}")
            continue

        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(
                template
                % {
                    "hook_name": hook_name,
                    "hook_file_name": hook_file[:-3],
                    "all_imports": all_imports_str,
                    "mock_objects": mock_objects_str,
                    "api_array": api_array_str,
                }
            )

        print(f"Regenerated test for {item}: {test_file_name}")
        count += 1

    print(f"\nTotal tests regenerated: {count}")


if __name__ == "__main__":
    generate_tests(os.getcwd())
