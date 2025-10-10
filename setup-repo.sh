#!/bin/bash

# English Learning AI Agent - Repository Setup Script
# This script automates the creation of the complete repository structure

echo "🎓 English Learning AI Agent - Repository Setup"
echo "================================================"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Error: Git is not installed. Please install Git first."
    exit 1
fi

# Get repository name
read -p "Enter your GitHub username: " username
repo_name="english-learning-ai"

echo ""
echo "📁 Creating directory structure..."

# Create main directories
mkdir -p docs
mkdir -p examples
mkdir -p templates
mkdir -p integrations/discord-bot
mkdir -p integrations/telegram-bot
mkdir -p integrations/api
mkdir -p resources/vocabulary-lists
mkdir -p resources/grammar-guides
mkdir -p tools/export-tools
mkdir -p .github/ISSUE_TEMPLATE
mkdir -p .github/workflows

echo "✅ Directory structure created"

# Create .gitignore
echo "📝 Creating .gitignore..."
cat > .gitignore << 'EOF'
# Personal learning files
*-learning.md
my-english-learning.md

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Python
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
venv/
env/

# Logs
*.log

# Temporary files
*.tmp
temp/

# Backups
*.bak
backup/

# Personal notes
notes.md
TODO.md
EOF

# Create LICENSE
echo "📝 Creating LICENSE (MIT)..."
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2025 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

# Create placeholder files
echo "📝 Creating placeholder files..."

# docs/CHANGELOG.md
cat > docs/CHANGELOG.md << 'EOF'
# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2025-01-09

### Added
- Initial release
- Core learning system with spaced repetition
- Automatic level assessment (A1-C2)
- Vocabulary lessons with memory techniques
- Grammar exercises
- Conversation practice
- Free writing feedback
- Progress tracking and statistics
- Complete documentation
- Example files for different levels

### Features
- Works with any AI assistant (Claude, ChatGPT, etc.)
- Single markdown file for all progress
- Completely free and open-source
- No app installation required
- Portable and works offline

---

## Future Releases

### [1.1.0] - Planned
- Multi-language support (Spanish, French, German)
- Discord bot integration
- Telegram bot integration
- Anki export tool
- More example files

### [1.2.0] - Planned
- Audio pronunciation integration
- Mobile app guides
- Progress visualization tools
- Advanced analytics

### [2.0.0] - Future
- Web interface
- Teacher dashboard
- Group learning features
- API for third-party integrations
EOF

# Issue templates
cat > .github/ISSUE_TEMPLATE/bug_report.md << 'EOF'
---
name: Bug Report
about: Report a bug to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description
A clear and concise description of what the bug is.

## To Reproduce
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## Expected Behavior
A clear description of what you expected to happen.

## Your Setup
- **English Level**: [A1/A2/B1/B2/C1/C2]
- **AI Assistant**: [Claude/ChatGPT/Other]
- **Operating System**: [Windows/Mac/Linux/iOS/Android]
- **Browser** (if applicable): [Chrome/Firefox/Safari/Other]

## File Excerpt
Please provide relevant parts of your `.md` file (remove personal information):

```markdown
[Paste relevant section here]
```

## Screenshots
If applicable, add screenshots to help explain your problem.

## Additional Context
Add any other context about the problem here.
EOF

cat > .github/ISSUE_TEMPLATE/feature_request.md << 'EOF'
---
name: Feature Request
about: Suggest an idea for this project
title: '[FEATURE] '
labels: enhancement
assignees: ''
---

## Is your feature request related to a problem?
A clear description of what the problem is. Ex. I'm always frustrated when [...]

## Describe the solution you'd like
A clear and concise description of what you want to happen.

## Describe alternatives you've considered
A clear description of any alternative solutions or features you've considered.

## Who would benefit from this feature?
- [ ] Beginners (A1-A2)
- [ ] Intermediate (B1-B2)
- [ ] Advanced (C1-C2)
- [ ] Teachers
- [ ] Developers
- [ ] Everyone

## Use Case
Describe a specific scenario where this feature would be useful.

## Implementation Ideas
If you have ideas about how this could be implemented, share them here.

## Additional Context
Add any other context, mockups, or screenshots about the feature request here.
EOF

cat > .github/ISSUE_TEMPLATE/question.md << 'EOF'
---
name: Question
about: Ask a question about the project
title: '[QUESTION] '
labels: question
assignees: ''
---

## Your Question
Ask your question here. Be as specific as possible.

## What I've Already Tried
- [ ] Checked the README
- [ ] Read the FAQ
- [ ] Searched existing issues
- [ ] Read the documentation

## Context
Provide any additional context that might help answer your question:
- Your English level
- What you're trying to achieve
- Any error messages you're seeing

## Additional Information
Any other details that might be helpful.
EOF

# Create placeholder READMEs for subdirectories
cat > integrations/README.md << 'EOF'
# Integrations

This directory contains integration examples and guides for using the English Learning AI Agent with various platforms.

## Available Integrations

### Discord Bot
Build a Discord bot that provides English lessons to server members.

### Telegram Bot
Create a Telegram bot for personal English learning.

### API Integration
Guidelines for integrating the system into your own applications.

## Contributing

Have an integration to share? Please submit a pull request!

See [CONTRIBUTING.md](../docs/CONTRIBUTING.md) for details.
EOF

cat > resources/README.md << 'EOF'
# Learning Resources

This directory contains supplementary learning materials organized by level.

## Vocabulary Lists

Pre-compiled vocabulary lists for each level:
- A1: 500 most common words
- A2: 1000 essential words
- B1: 2000 intermediate words
- B2: 3500 advanced words
- C1-C2: Academic and sophisticated vocabulary

## Grammar Guides

Comprehensive grammar explanations:
- A1-A2: Beginner grammar
- B1-B2: Intermediate grammar
- C1-C2: Advanced grammar

## Contributing

Help expand these resources! Add:
- Topic-specific vocabulary (business, travel, technology)
- Grammar explanations with examples
- Common phrases and idioms
- Cultural notes

See [CONTRIBUTING.md](../docs/CONTRIBUTING.md) for guidelines.
EOF

cat > tools/README.md << 'EOF'
# Tools

Utility scripts to enhance your learning experience.

## Available Tools

### file-validator.py
Validates the structure of your `.md` learning file.

### progress-analyzer.py
Analyzes your learning progress and generates insights.

### Export Tools

#### to-anki.py
Exports your vocabulary to Anki flashcard format.

#### to-pdf.py
Generates a PDF progress report.

## Usage

Each tool includes its own documentation. See individual files for details.

## Contributing

Have a useful tool? Share it!
- File converters
- Progress visualizers
- Statistics calculators
- Integration helpers

See [CONTRIBUTING.md](../docs/CONTRIBUTING.md) for guidelines.
EOF

# Create simple validation script
cat > tools/file-validator.py << 'EOF'
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
EOF

chmod +x tools/file-validator.py

echo "✅ All placeholder files created"
echo ""
echo "📋 Summary:"
echo "   - Directory structure: ✅"
echo "   - .gitignore: ✅"
echo "   - LICENSE: ✅"
echo "   - Issue templates: ✅"
echo "   - Placeholder files: ✅"
echo "   - Validation tool: ✅"
echo ""
echo "📝 Next steps:"
echo "   1. Copy the artifacts from Claude into the following files:"
echo "      - README.md (from artifact: github-readme)"
echo "      - docs/SYSTEM_PROMPT.md (from artifact: system-prompt-doc)"
echo "      - docs/TEMPLATE.md (from artifact: template-file)"
echo "      - examples/beginner-example.md (from artifact: example-beginner)"
echo "      - docs/FAQ.md (from artifact: complete-repo-structure)"
echo "      - docs/CONTRIBUTING.md (from artifact: complete-repo-structure)"
echo "      - docs/GETTING_STARTED.md (from artifact: complete-repo-structure)"
echo "      - CODE_OF_CONDUCT.md (from artifact: complete-repo-structure)"
echo ""
echo "   2. Update LICENSE with your name"
echo ""
echo "   3. Initialize git repository:"
echo "      git init"
echo "      git add ."
echo "      git commit -m 'Initial commit: English Learning AI Agent system'"
echo ""
echo "   4. Create GitHub repository and push:"
echo "      git remote add origin https://github.com/$username/$repo_name.git"
echo "      git branch -M main"
echo "      git push -u origin main"
echo ""
echo "🚀 Repository structure is ready!"
echo ""