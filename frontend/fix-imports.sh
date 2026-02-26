#!/bin/bash
# Fix duplicate import statements

find src -type f \( -name "*.jsx" -o -name "*.js" \) | while read file; do
  # Check if file has duplicate import { patterns
  if perl -0777 -ne 'print if /import \{\n\s*import \{/' "$file" 2>/dev/null; then
    echo "Fixing: $file"
    # Create backup
    cp "$file" "$file.bak"
    # Remove duplicate import { lines - keep only the second one
    perl -i -0777 -pe 's/import \{\n(\s*)import \{/$1import {/g' "$file"
    echo "Fixed: $file"
  fi
done
