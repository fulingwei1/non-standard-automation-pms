#!/bin/bash
# Script to fix vi.mock in test files

cd /Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/frontend

# Common API methods
COMMON_METHODS="list:vi.fn(),get:vi.fn(),create:vi.fn(),update:vi.fn(),delete:vi.fn(),query:vi.fn(),getStatistics:vi.fn(),export:vi.fn(),import:vi.fn()"

# Function to generate API mock entries
generate_api_mocks() {
    local apis="$1"
    local result=""
    for api in $apis; do
        # Skip aliases, use original name
        original=$(echo "$api" | sed 's/ as .*//')
        result="$result
    $original: {
      list: vi.fn(),
      get: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
      query: vi.fn(),
      getStatistics: vi.fn(),
      export: vi.fn(),
      import: vi.fn(),
    },"
    done
    echo "$result"
}

# Find all failing test files
files=$(find src/pages -name "*.test.js" -exec grep -l "api.list.mockResolvedValue\|api.get.mockResolvedValue" {} \; 2>/dev/null)

for file in $files; do
    echo "Processing: $file"
    
    # Extract API imports
    apis=$(grep -E "^import.*{.*Api.*}.*from.*services/api" "$file" | sed 's/.*import //' | sed 's/ from .*//' | tr ',' '\n' | sed 's/ as .*//' | sed 's/  */ /g' | sed 's/^ //' | sed 's/ $//' | sort -u | tr '\n' ' ')
    
    if [ -z "$apis" ]; then
        echo "  No APIs found, skipping"
        continue
    fi
    
    echo "  APIs: $apis"
    
    # Generate the new mock
    api_mocks=$(generate_api_mocks "$apis")
    
    # Get the mock path
    mock_path=$(grep -o "vi\.mock('[^']*services/api[^']*'" "$file" | sed "s/vi\.mock('//" | sed "s/'$//")
    
    if [ -z "$mock_path" ]; then
        echo "  No mock path found, skipping"
        continue
    fi
    
    # Create new mock content
    new_mock="// Mock API
vi.mock('$mock_path', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    default: {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      patch: vi.fn(),
      defaults: { baseURL: '/api' },
    },$api_mocks
  };
});"

    # Use sed to replace the old mock
    # First, get the line numbers
    start_line=$(grep -n "vi.mock.*services/api" "$file" | head -1 | cut -d: -f1)
    
    if [ -z "$start_line" ]; then
        echo "  Could not find mock line, skipping"
        continue
    fi
    
    # Find the end of the mock (closing });)
    end_line=$(awk -v start="$start_line" 'NR>=start{if(/^});/){print NR; exit}}' "$file")
    
    if [ -z "$end_line" ]; then
        echo "  Could not find end of mock, skipping"
        continue
    fi
    
    # Replace the lines
    sed -i '' "${start_line},${end_line}d" "$file"
    sed -i '' "${start_line}i\\
$new_mock\\
" "$file"
    
    echo "  Fixed: lines $start_line-$end_line"
done

echo "Done!"