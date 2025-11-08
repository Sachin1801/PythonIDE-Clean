# CSV File Operations Tutorial

## Overview
Your PythonIDE fully supports CSV (Comma-Separated Values) file operations! You can create, read, write, and manipulate CSV files using Python's built-in `csv` module or external libraries like `pandas`.

## ✅ What Works

- ✅ **Writing CSV files** - Create new CSV files in your workspace
- ✅ **Reading CSV files** - Load existing CSV files
- ✅ **Appending data** - Add rows to existing CSV files
- ✅ **File persistence** - CSV files persist across sessions on AWS EFS
- ✅ **Relative paths** - Use `open('data.csv')` in same directory as script
- ✅ **Absolute paths** - Not recommended due to security restrictions

## 📁 File Location

All CSV files are saved in the **same directory** as your Python script by default:
- Your script: `Local/sa9082/assignment1.py`
- Your CSV: `Local/sa9082/data.csv` (automatically created)

## Example 1: Writing CSV Files

```python
import csv

# Create a CSV file with student grades
with open('grades.csv', 'w', newline='') as file:
    writer = csv.writer(file)

    # Write header row
    writer.writerow(['Student', 'Assignment', 'Grade'])

    # Write data rows
    writer.writerow(['Alice', 'HW1', 95])
    writer.writerow(['Bob', 'HW1', 87])
    writer.writerow(['Charlie', 'HW1', 92])

print("CSV file 'grades.csv' created successfully!")
```

## Example 2: Reading CSV Files

```python
import csv

# Read the CSV file
with open('grades.csv', 'r') as file:
    reader = csv.reader(file)

    # Skip header
    header = next(reader)
    print(f"Columns: {header}")

    # Process each row
    for row in reader:
        student, assignment, grade = row
        print(f"{student} scored {grade} on {assignment}")
```

## Example 3: Reading with DictReader

```python
import csv

# Read CSV as dictionaries (easier to work with)
with open('grades.csv', 'r') as file:
    reader = csv.DictReader(file)

    for row in reader:
        print(f"{row['Student']}: {row['Grade']}")
```

## Example 4: Appending to Existing CSV

```python
import csv

# Add new rows to existing file
with open('grades.csv', 'a', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['David', 'HW1', 88])
    writer.writerow(['Eve', 'HW1', 94])

print("New grades added!")
```

## Example 5: Processing CSV Data

```python
import csv

# Calculate average grade
total = 0
count = 0

with open('grades.csv', 'r') as file:
    reader = csv.DictReader(file)

    for row in reader:
        total += int(row['Grade'])
        count += 1

average = total / count
print(f"Class average: {average:.2f}")
```

## Example 6: Creating Custom CSV Format

```python
import csv

# Use semicolons instead of commas
with open('data.csv', 'w', newline='') as file:
    writer = csv.writer(file, delimiter=';')
    writer.writerow(['Name', 'Age', 'City'])
    writer.writerow(['Alice', '20', 'New York'])
    writer.writerow(['Bob', '21', 'Boston'])
```

## Example 7: Handling Multi-line Cells

```python
import csv

# Write data with line breaks in cells
with open('feedback.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Student', 'Feedback'])
    writer.writerow(['Alice', 'Excellent work!\nGreat attention to detail.'])
    writer.writerow(['Bob', 'Good job.\nNeeds improvement on edge cases.'])
```

## Example 8: Error Handling

```python
import csv
import os

# Check if file exists before reading
if os.path.exists('grades.csv'):
    with open('grades.csv', 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            print(row)
else:
    print("File not found. Creating new file...")
    with open('grades.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Student', 'Grade'])
```

## 🚀 Advanced: Using Pandas (Optional)

If pandas is installed, you can use more advanced operations:

```python
import pandas as pd

# Create DataFrame
df = pd.DataFrame({
    'Student': ['Alice', 'Bob', 'Charlie'],
    'HW1': [95, 87, 92],
    'HW2': [88, 91, 85]
})

# Save to CSV
df.to_csv('grades_advanced.csv', index=False)

# Read from CSV
df_loaded = pd.read_csv('grades_advanced.csv')
print(df_loaded)

# Calculate statistics
print(f"Average HW1 score: {df_loaded['HW1'].mean()}")
```

## 📝 Best Practices

1. **Always use `newline=''`** when opening CSV files for writing
2. **Use context managers (`with`)** to ensure files are closed properly
3. **Handle exceptions** when reading files that might not exist
4. **Use DictReader** for easier column access
5. **Keep CSV files in your workspace** (same directory as script)

## ⚠️ Important Notes

- **File paths**: Use relative paths like `'data.csv'` (not `/home/user/data.csv`)
- **File size limit**: 10MB maximum per file
- **Allowed extensions**: `.csv` files are explicitly allowed for upload
- **Persistence**: Your CSV files persist across sessions (saved on AWS EFS)
- **Security**: You can only access files in your `Local/{username}/` directory

## 🎯 Common Use Cases

### 1. Student Grade Tracker
```python
import csv

# Write grades
with open('my_grades.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Assignment', 'Score', 'Max Points'])
    writer.writerow(['HW1', 95, 100])
    writer.writerow(['Quiz1', 18, 20])

# Calculate percentage
with open('my_grades.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        pct = (int(row['Score']) / int(row['Max Points'])) * 100
        print(f"{row['Assignment']}: {pct:.1f}%")
```

### 2. Data Cleaning
```python
import csv

# Read messy data and clean it
with open('input.csv', 'r') as infile, open('cleaned.csv', 'w', newline='') as outfile:
    reader = csv.reader(infile)
    writer = csv.writer(outfile)

    for row in reader:
        # Remove empty cells
        cleaned_row = [cell.strip() for cell in row if cell.strip()]
        if cleaned_row:
            writer.writerow(cleaned_row)
```

### 3. Survey Data Collection
```python
import csv

# Collect survey responses
print("Student Survey")
name = input("Your name: ")
course = input("Course: ")
rating = input("Rate 1-5: ")

# Save to CSV
with open('survey.csv', 'a', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([name, course, rating])

print("Response saved!")
```

## 🐛 Troubleshooting

**Problem**: `FileNotFoundError`
**Solution**: Make sure the CSV file exists or create it first

**Problem**: Extra blank lines in CSV
**Solution**: Use `newline=''` when opening files

**Problem**: Can't find uploaded CSV
**Solution**: CSV files must be uploaded to `Local/{username}/` directory

## 📚 Further Reading

- [Python CSV Documentation](https://docs.python.org/3/library/csv.html)
- [Pandas CSV Tutorial](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html)

---

**Questions?** Ask your instructor during office hours!
