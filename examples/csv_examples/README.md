# CSV Examples for PythonIDE

This directory contains practical examples of CSV file operations that work in your web-based Python IDE.

## 📚 Examples

### Example 1: Basic CSV Writing
**File**: `example1_basic_write.py`
- Creates a CSV file with student records
- Demonstrates basic `csv.writer()` usage
- Shows proper file handling with `with` statement

**Run this first!**

### Example 2: Basic CSV Reading
**File**: `example2_basic_read.py`
- Reads the CSV file created by Example 1
- Shows how to handle headers
- Demonstrates row-by-row processing

**Requires**: Run Example 1 first

### Example 3: Dictionary Operations
**File**: `example3_dict_operations.py`
- Uses `DictReader` and `DictWriter` for easier column access
- Creates a grades tracking system
- Calculates percentages from scores

**Best for**: Working with named columns

### Example 4: Pandas Advanced Operations
**File**: `example4_pandas_advanced.py`
- Demonstrates pandas DataFrame operations
- Shows data analysis and statistics
- Sorts and ranks data
- Creates multiple output files

**Requires**: pandas library (included in your IDE)

### Example 5: Interactive Data Entry
**File**: `example5_interactive_input.py`
- Collects user input via `input()`
- Appends data to existing CSV
- Displays all collected responses
- Creates file if it doesn't exist

**Best for**: Building survey or data collection tools

## 🚀 How to Use

1. **Upload to your workspace**: Upload these `.py` files to your `Local/{username}/` directory
2. **Run in order**: Start with Example 1, then Example 2, etc.
3. **View CSV files**: After running, you'll see `.csv` files in the same directory
4. **Experiment**: Modify the examples to fit your needs!

## 📁 File Locations

All CSV files created by these examples will be saved in the **same directory** as the script:
- Script location: `Local/sa9082/example1_basic_write.py`
- CSV location: `Local/sa9082/students.csv`

## 🎯 Common Patterns

### Writing CSV
```python
import csv

with open('data.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Header1', 'Header2'])
    writer.writerow(['Value1', 'Value2'])
```

### Reading CSV
```python
import csv

with open('data.csv', 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        print(row)
```

### Using Dictionaries
```python
import csv

# Writing
with open('data.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['Name', 'Age'])
    writer.writeheader()
    writer.writerow({'Name': 'Alice', 'Age': 20})

# Reading
with open('data.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(row['Name'], row['Age'])
```

## 🔧 Troubleshooting

**Q: File not found error?**
A: Make sure you run examples in order (Example 1 before Example 2)

**Q: Extra blank lines in CSV?**
A: Always use `newline=''` when opening files for writing

**Q: Can't see CSV files in IDE?**
A: They're in the same folder as your script - refresh the file tree

**Q: pandas not found?**
A: pandas is included in the IDE dependencies (version 2.2.0+)

## 📖 Further Learning

See `CSV_TUTORIAL.md` in the root directory for comprehensive documentation.

## 💡 Tips

- Always use `with` statements for automatic file closing
- Use `newline=''` when writing CSV files
- Check if files exist before reading with `os.path.exists()`
- Use DictReader for easier column access by name
- CSV files persist across sessions on AWS EFS

---

**Happy coding!** 🐍
