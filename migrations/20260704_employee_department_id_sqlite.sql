-- HR-05: add canonical department_id to employees while preserving legacy department names.

ALTER TABLE employees ADD COLUMN department_id INTEGER;

CREATE INDEX IF NOT EXISTS idx_employees_department_id
ON employees(department_id);

UPDATE employees
SET department_id = (
    SELECT departments.id
    FROM departments
    WHERE departments.dept_name = employees.department
    ORDER BY departments.id
    LIMIT 1
)
WHERE department_id IS NULL
  AND department IS NOT NULL
  AND TRIM(department) != ''
  AND EXISTS (
      SELECT 1
      FROM departments
      WHERE departments.dept_name = employees.department
  );
