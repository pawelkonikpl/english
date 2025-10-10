#!/usr/bin/env python3
"""
English Learning File Validator
Checks if your learning file has the correct structure.
"""

import sys
import re

def validate_file(filepath):
    """Validate the structure of an English learning file."""

    print(f"🔍 Validating {filepath}...")
    print()

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ Error: File '{filepath}' not found")
        return False
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

    errors = []
    warnings = []

    # Check for system prompt
    if "AI AGENT INSTRUCTIONS" not in content:
        errors.append("Missing AI Agent Instructions at the beginning")

    # Check for required sections
    required_sections = [
        "Learner Profile",
        "Vocabulary - Learned Words",
        "Grammar - Completed Topics",
        "Review Schedule",
        "Statistics"
    ]

    for section in required_sections:
        if section not in content:
            errors.append(f"Missing section: {section}")

    # Check vocabulary table structure
    if "| Word | Translation | Date Learned | Last Review | Mastery |" not in content:
        warnings.append("Vocabulary table header might be malformed")

    # Check for level
    level_pattern = r'\*\*Level:\*\* (A1|A2|B1|B2|C1|C2)'
    if not re.search(level_pattern, content):
        warnings.append("English level not properly specified")

    # Display results
    if not errors and not warnings:
        print("✅ File structure is valid!")
        print("🎉 Everything looks good!")
        return True

    if errors:
        print("❌ ERRORS FOUND:")
        for error in errors:
            print(f"   • {error}")
        print()

    if warnings:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"   • {warning}")
        print()

    if errors:
        print("Please fix the errors above.")
        return False
    else:
        print("File is valid but has some warnings.")
        return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python file-validator.py <your-learning-file.md>")
        sys.exit(1)

    filepath = sys.argv[1]
    success = validate_file(filepath)
    sys.exit(0 if success else 1)
