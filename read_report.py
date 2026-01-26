import pandas as pd

file_path = "/Users/flw/Desktop/功能重复问题分析报告_2026-01-25.xlsx"
try:
    xl = pd.ExcelFile(file_path)
    for sheet_name in xl.sheet_names:
        print(f"\n--- Sheet: {sheet_name} ---")
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        # Limit the number of rows to avoid huge output, but get enough to analyze
        print(df.head(50).to_markdown(index=False))
        if len(df) > 50:
            print(f"... and {len(df) - 50} more rows")
except Exception as e:
    print(f"Error reading excel: {e}")
