#!/usr/bin/env python3
"""
Educational Error Handler for Python Web IDE
Provides student-friendly error messages and learning hints
"""

import re
import traceback
from typing import Dict, List, Tuple, Optional


class EducationalErrorHandler:
    """Transforms Python errors into educational messages for students"""

    def __init__(self):
        self.error_patterns = self._initialize_error_patterns()
        self.common_mistakes = self._initialize_common_mistakes()

    def _initialize_error_patterns(self) -> Dict[str, Dict]:
        """Define patterns for common Python errors with educational messages"""
        return {
            "SyntaxError": {
                "pattern": r"SyntaxError: (.+)",
                "educational_message": "Syntax Error: Python couldn't understand your code structure",
                "hints": {
                    "invalid syntax": [
                        "✓ Check for missing colons (:) after if, for, while, def statements",
                        "✓ Verify parentheses, brackets, and quotes are properly closed",
                        "✓ Ensure proper indentation (use 4 spaces consistently)",
                        "✓ Check for typos in Python keywords",
                    ],
                    "EOL while scanning": [
                        "✓ You have an unclosed string - check your quotes",
                        "✓ Make sure each opening quote has a closing quote",
                        "✓ For multi-line strings, use triple quotes (\"\"\" or ''')",
                    ],
                    "unexpected EOF": [
                        "✓ Your code ended unexpectedly",
                        "✓ Check if all blocks (if, for, while, def) have content",
                        "✓ Verify all parentheses and brackets are closed",
                    ],
                },
            },
            "IndentationError": {
                "pattern": r"IndentationError: (.+)",
                "educational_message": "Indentation Error: Python uses spacing to understand code blocks",
                "hints": {
                    "unexpected indent": [
                        "✓ Remove extra spaces at the beginning of the line",
                        "✓ Make sure the line aligns with others at the same level",
                        "✓ Use exactly 4 spaces for each indentation level",
                    ],
                    "expected an indented block": [
                        "✓ Add indented code after your if/for/while/def statement",
                        "✓ Use 4 spaces to indent the code block",
                        '✓ If you want an empty block, use "pass"',
                    ],
                    "unindent does not match": [
                        "✓ Your indentation doesn't match any outer level",
                        "✓ Check that all lines in the same block have the same indentation",
                        "✓ Don't mix tabs and spaces (use spaces only)",
                    ],
                },
            },
            "NameError": {
                "pattern": r"NameError: name \'(.+)\' is not defined",
                "educational_message": "Name Error: Python doesn't recognize this variable or function name",
                "hints": {
                    "default": [
                        "✓ Check the spelling of the variable/function name",
                        "✓ Make sure you defined the variable before using it",
                        "✓ Python is case-sensitive (myVar ≠ myvar)",
                        "✓ If it's a string, wrap it in quotes",
                    ]
                },
            },
            "TypeError": {
                "pattern": r"TypeError: (.+)",
                "educational_message": "Type Error: You're using a value in a way Python doesn't expect",
                "hints": {
                    "unsupported operand": [
                        "✓ You can't use this operation with these data types",
                        "✓ Check if you need to convert types (e.g., str() or int())",
                        "✓ Make sure you're not mixing strings and numbers in math",
                    ],
                    "not callable": [
                        "✓ You're trying to call something that isn't a function",
                        "✓ Remove parentheses if it's a variable, not a function",
                        "✓ Check if you accidentally overwrote a function name",
                    ],
                    "missing .* required positional": [
                        "✓ Your function needs more arguments",
                        "✓ Check the function definition to see what it expects",
                        "✓ Count the parameters and make sure you provide all of them",
                    ],
                    "takes .* positional argument": [
                        "✓ You're giving too many arguments to the function",
                        "✓ Check how many parameters the function expects",
                        "✓ Remove extra arguments from your function call",
                    ],
                },
            },
            "ValueError": {
                "pattern": r"ValueError: (.+)",
                "educational_message": "Value Error: The value you provided doesn't work for this operation",
                "hints": {
                    "invalid literal for int()": [
                        "✓ You're trying to convert something to a number that isn't numeric",
                        "✓ Check the input - it might contain letters or symbols",
                        "✓ Use .strip() to remove extra spaces",
                        "✓ Handle the case where user input might be invalid",
                    ],
                    "too many values to unpack": [
                        "✓ You're trying to assign to fewer variables than values provided",
                        "✓ Count the values on the right and variables on the left",
                        "✓ They need to match exactly",
                    ],
                    "not enough values to unpack": [
                        "✓ You're trying to assign to more variables than values provided",
                        "✓ Check if your data has all the expected elements",
                        "✓ Consider using a different unpacking approach",
                    ],
                },
            },
            "IndexError": {
                "pattern": r"IndexError: (.+)",
                "educational_message": "Index Error: You're trying to access a position that doesn't exist",
                "hints": {
                    "list index out of range": [
                        "✓ The list doesn't have an item at that position",
                        "✓ Remember: Python lists start at index 0, not 1",
                        "✓ A list with 5 items has indices 0, 1, 2, 3, 4",
                        "✓ Use len(list) to check the list size first",
                    ]
                },
            },
            "KeyError": {
                "pattern": r"KeyError: (.+)",
                "educational_message": "Key Error: The dictionary doesn't have that key",
                "hints": {
                    "default": [
                        "✓ Check if the key exists before accessing it",
                        "✓ Use .get(key, default) for safe access",
                        "✓ Check the spelling and case of your key",
                        "✓ Print the dictionary keys with .keys() to see what's available",
                    ]
                },
            },
            "AttributeError": {
                "pattern": r"AttributeError: (.+)",
                "educational_message": "Attribute Error: This object doesn't have that property or method",
                "hints": {
                    "has no attribute": [
                        "✓ Check the spelling of the attribute/method name",
                        "✓ Make sure you're using the right type of object",
                        "✓ Use dir(object) to see available attributes",
                        "✓ Check if you need to import a module first",
                    ]
                },
            },
            "ImportError": {
                "pattern": r"(ImportError|ModuleNotFoundError): (.+)",
                "educational_message": "Import Error: Python can't find the module you're trying to import",
                "hints": {
                    "No module named": [
                        "✓ Check the spelling of the module name",
                        "✓ Make sure the module is installed (pip install module_name)",
                        "✓ Verify the module is in your Python path",
                        "✓ For local files, check they're in the same directory",
                    ]
                },
            },
            "ZeroDivisionError": {
                "pattern": r"ZeroDivisionError: (.+)",
                "educational_message": "Division by Zero: You can't divide by zero in mathematics",
                "hints": {
                    "default": [
                        "✓ Check your denominator before dividing",
                        "✓ Add an if statement to handle zero cases",
                        "✓ Consider what should happen when the divisor is zero",
                        "✓ Use try/except to handle this gracefully",
                    ]
                },
            },
            "RecursionError": {
                "pattern": r"RecursionError: (.+)",
                "educational_message": "Recursion Error: Your function is calling itself too many times",
                "hints": {
                    "maximum recursion depth exceeded": [
                        "✓ Check your base case - recursion needs a stopping point",
                        "✓ Make sure your recursive calls move toward the base case",
                        "✓ Verify you're not creating an infinite loop",
                        "✓ Consider using a loop instead of recursion",
                    ]
                },
            },
        }

    def _initialize_common_mistakes(self) -> Dict[str, List[str]]:
        """Common beginner mistakes and their solutions"""
        return {
            "print without parentheses": [
                "In Python 3, print is a function",
                'Always use: print("text")',
                'Not: print "text"',
            ],
            "mixing tabs and spaces": [
                "Use spaces only for indentation",
                "Set your editor to show whitespace",
                "Use 4 spaces per indentation level",
            ],
            "using = instead of ==": [
                "Use = for assignment: x = 5",
                "Use == for comparison: if x == 5",
                "Common mistake in if statements",
            ],
            "forgetting self in methods": [
                "Class methods need self as first parameter",
                "def method(self, other_params):",
                "Access attributes with self.attribute",
            ],
        }

    def parse_error(self, error_output: str) -> Dict:
        """Parse Python error output and create educational response"""
        result = {
            "original_error": error_output,
            "error_type": None,
            "error_message": None,
            "line_number": None,
            "educational_message": None,
            "hints": [],
            "code_context": None,
            "suggested_fixes": [],
        }

        # Extract line number if present
        line_match = re.search(r'File ".*?", line (\d+)', error_output)
        if line_match:
            result["line_number"] = int(line_match.group(1))

        # Extract code context
        context_match = re.search(r'File ".*?", line \d+.*?\n\s*(.*?)\n\s*\^', error_output, re.DOTALL)
        if context_match:
            result["code_context"] = context_match.group(1).strip()

        # Identify error type and provide educational content
        for error_type, error_info in self.error_patterns.items():
            if error_type in error_output:
                result["error_type"] = error_type
                result["educational_message"] = error_info["educational_message"]

                # Extract specific error message
                match = re.search(error_info["pattern"], error_output)
                if match:
                    result["error_message"] = match.group(1) if len(match.groups()) > 0 else match.group(0)

                # Add relevant hints
                for hint_key, hints in error_info.get("hints", {}).items():
                    if hint_key == "default" or hint_key in error_output.lower():
                        result["hints"].extend(hints)
                        break

                # Add suggested fixes based on common patterns
                result["suggested_fixes"] = self._generate_fixes(
                    error_type, result["error_message"], result["code_context"]
                )
                break

        return result

    def _generate_fixes(self, error_type: str, error_message: str, code_context: Optional[str]) -> List[str]:
        """Generate specific fix suggestions based on error context"""
        fixes = []

        if error_type == "NameError" and code_context:
            # Check for common typos
            if "print" in error_message.lower():
                fixes.append("Did you mean: print() ?")
            elif "true" in error_message.lower() or "false" in error_message.lower():
                fixes.append("Python uses True and False (capital letters)")
            elif any(builtin in error_message.lower() for builtin in ["len", "range", "input", "int", "str"]):
                fixes.append("This looks like a built-in function - check spelling")

        elif error_type == "SyntaxError" and code_context:
            if "if " in code_context or "for " in code_context or "while " in code_context:
                if ":" not in code_context:
                    fixes.append("Add a colon (:) at the end of the line")
            if "=" in code_context and "==" not in code_context:
                fixes.append("If comparing values, use == instead of =")

        elif error_type == "IndentationError":
            fixes.append("Quick fix: Select all code and re-indent properly")
            fixes.append("In most editors: Select all → Tab to indent, Shift+Tab to unindent")

        return fixes

    def format_educational_error(self, error_data: Dict) -> str:
        """Format error data into student-friendly message"""
        output = []

        if error_data["error_type"]:
            output.append(f"Error Type: {error_data['error_type']}")
            output.append(f"{error_data['educational_message']}")

        if error_data["line_number"]:
            output.append(f"\nError Location: Line {error_data['line_number']}")

        if error_data["error_message"]:
            output.append(f"Specific Issue: {error_data['error_message']}")

        if error_data["hints"]:
            output.append("\nHow to Fix:")
            for hint in error_data["hints"]:
                output.append(f"  {hint}")

        if error_data["suggested_fixes"]:
            output.append("\nSuggested Fixes:")
            for fix in error_data["suggested_fixes"]:
                output.append(f"  → {fix}")

        output.append("\n" + "-" * 40)
        output.append("Original Python Error:")
        output.append(error_data["original_error"])

        return "\n".join(output)

    def process_error_output(self, raw_output: str) -> str:
        """Main method to process raw Python error output"""
        # Check if this is actually an error
        if not any(error in raw_output for error in ["Error", "Exception", "Traceback"]):
            return raw_output

        # Parse and format the error
        error_data = self.parse_error(raw_output)

        # If we successfully parsed the error, return educational format
        if error_data["error_type"]:
            return self.format_educational_error(error_data)

        # Otherwise return original
        return raw_output


# Example usage and testing
if __name__ == "__main__":
    handler = EducationalErrorHandler()

    # Test with a sample error
    sample_error = """Traceback (most recent call last):
  File "main.py", line 6, in <module>
    print(f" Hello {name}, how are you ?")
NameError: name 'name' is not defined"""

    result = handler.process_error_output(sample_error)
    print(result)
