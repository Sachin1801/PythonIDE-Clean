#!/usr/bin/env python3
"""
Example 4: Advanced CSV Operations with Pandas
Demonstrates pandas DataFrame operations for data analysis
"""
import pandas as pd

print("Creating sample dataset...")

# Create a DataFrame
data = {
    'Student': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
    'HW1': [95, 87, 92, 88, 94],
    'HW2': [88, 91, 85, 95, 89],
    'Quiz1': [18, 19, 17, 20, 18],
    'Quiz2': [19, 18, 20, 19, 20]
}

df = pd.DataFrame(data)

# Save to CSV
df.to_csv('course_grades.csv', index=False)
print("✅ course_grades.csv created\n")

# Read from CSV
df_loaded = pd.read_csv('course_grades.csv')

print("📊 Course Grades:")
print("=" * 60)
print(df_loaded)
print("=" * 60)

# Calculate statistics
print("\n📈 Statistics:")
print("-" * 60)
print(f"Average HW1 score: {df_loaded['HW1'].mean():.2f}")
print(f"Average HW2 score: {df_loaded['HW2'].mean():.2f}")
print(f"Average Quiz1 score: {df_loaded['Quiz1'].mean():.2f}")
print(f"Average Quiz2 score: {df_loaded['Quiz2'].mean():.2f}")
print("-" * 60)

# Add total column
df_loaded['Total'] = (df_loaded['HW1'] + df_loaded['HW2'] +
                      df_loaded['Quiz1'] + df_loaded['Quiz2'])

# Sort by total
df_sorted = df_loaded.sort_values('Total', ascending=False)

print("\n🏆 Students Ranked by Total Score:")
print("=" * 60)
for idx, row in df_sorted.iterrows():
    print(f"{row['Student']:10} | Total: {row['Total']:.0f}")
print("=" * 60)

# Save updated file
df_sorted.to_csv('course_grades_with_totals.csv', index=False)
print("\n✅ Saved updated grades to 'course_grades_with_totals.csv'")
