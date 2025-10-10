#!/usr/bin/env python3
"""
Context Sharding Validator
Validates section markers and structure for context sharding optimization.

Usage:
    python context-sharding-validator.py <your-learning-file.md>
    python context-sharding-validator.py english-learning.md --fix

Options:
    --fix       Automatically fix common issues (backup created)
    --verbose   Show detailed section analysis
    --stats     Display section size statistics
"""

import sys
import re
import os
from datetime import datetime
from collections import defaultdict


# Required section markers for context sharding
REQUIRED_SECTIONS = {
    'PROFILE': 'Learner Profile',
    'VOCAB_ACTIVE': 'Vocabulary - Active Learning',
    'VOCAB_ARCHIVE': 'Vocabulary - Archive',
    'GRAMMAR_DETAILED': 'Grammar - Completed Topics',
    'CONVERSATION_HISTORY': 'Conversation - Completed Sessions',
    'REVIEW_SCHEDULE': 'Review Schedule',
    'STATISTICS': 'Statistics',
    'LEARNING_PLAN': 'Learning Plan',
    'NOTES': 'Notes & Observations',
    'ACHIEVEMENTS': 'Achievements'
}


class ContextShardingValidator:
    def __init__(self, filepath, verbose=False):
        self.filepath = filepath
        self.verbose = verbose
        self.content = ""
        self.errors = []
        self.warnings = []
        self.stats = defaultdict(int)

    def load_file(self):
        """Load file content."""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.content = f.read()
            return True
        except FileNotFoundError:
            print(f"❌ Error: File '{self.filepath}' not found")
            return False
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return False

    def check_sharding_enabled(self):
        """Check if context sharding is enabled in file header."""
        if "CONTEXT SHARDING ENABLED" in self.content:
            return True
        else:
            self.warnings.append(
                "Context sharding not explicitly enabled in file header. "
                "Add '⚡ CONTEXT SHARDING ENABLED' to the header."
            )
            return False

    def check_section_markers(self):
        """Validate all section markers are present and properly formatted."""
        found_sections = {}

        # Pattern: <!-- §SECTION_NAME -->
        opening_pattern = r'<!-- §([A-Z_]+) -->'
        closing_pattern = r'<!-- /§([A-Z_]+) -->'

        # Find all opening tags
        opening_tags = re.findall(opening_pattern, self.content)
        closing_tags = re.findall(closing_pattern, self.content)

        for section in opening_tags:
            if section in found_sections:
                self.errors.append(f"Duplicate opening tag for §{section}")
            found_sections[section] = {'open': True, 'close': False}

        for section in closing_tags:
            if section not in found_sections:
                self.errors.append(f"Closing tag without opening tag: /§{section}")
            else:
                found_sections[section]['close'] = True

        # Check for required sections
        for section_id, section_name in REQUIRED_SECTIONS.items():
            if section_id not in found_sections:
                self.errors.append(
                    f"Missing required section: §{section_id} ({section_name})"
                )
            elif not found_sections[section_id].get('close'):
                self.errors.append(
                    f"Missing closing tag for §{section_id}"
                )

        # Check for unknown sections
        for section_id in found_sections:
            if section_id not in REQUIRED_SECTIONS:
                self.warnings.append(
                    f"Unknown section marker: §{section_id} (not in standard set)"
                )

        self.stats['sections_found'] = len(found_sections)
        self.stats['sections_required'] = len(REQUIRED_SECTIONS)

        return len(self.errors) == 0

    def check_section_order(self):
        """Check if sections appear in recommended order."""
        recommended_order = [
            'PROFILE', 'VOCAB_ACTIVE', 'VOCAB_ARCHIVE',
            'GRAMMAR_DETAILED', 'CONVERSATION_HISTORY',
            'REVIEW_SCHEDULE', 'STATISTICS', 'LEARNING_PLAN',
            'NOTES', 'ACHIEVEMENTS'
        ]

        # Extract sections in order they appear
        pattern = r'<!-- §([A-Z_]+) -->'
        sections_in_file = re.findall(pattern, self.content)

        # Filter to only known sections
        sections_in_file = [s for s in sections_in_file if s in REQUIRED_SECTIONS]

        if sections_in_file != [s for s in recommended_order if s in sections_in_file]:
            self.warnings.append(
                "Sections are not in recommended order. "
                f"Found: {' → '.join(sections_in_file[:5])}..."
            )

    def check_nested_markers(self):
        """Check for improperly nested section markers."""
        stack = []
        pattern = r'<!-- (/?§[A-Z_]+) -->'

        for match in re.finditer(pattern, self.content):
            tag = match.group(1)
            if tag.startswith('/'):
                # Closing tag
                section = tag[2:]  # Remove /§
                if not stack:
                    self.errors.append(f"Closing tag {tag} without matching opening tag")
                elif stack[-1] != section:
                    self.errors.append(
                        f"Mismatched tags: expected /§{stack[-1]}, found {tag}"
                    )
                else:
                    stack.pop()
            else:
                # Opening tag
                section = tag[1:]  # Remove §
                stack.append(section)

        if stack:
            self.errors.append(f"Unclosed section markers: {', '.join(f'§{s}' for s in stack)}")

    def analyze_section_sizes(self):
        """Analyze the size of each section for optimization insights."""
        section_sizes = {}

        pattern = r'<!-- §([A-Z_]+) -->(.*?)<!-- /§\1 -->'

        for match in re.finditer(pattern, self.content, re.DOTALL):
            section = match.group(1)
            content = match.group(2)

            lines = len(content.split('\n'))
            chars = len(content)
            words = len(content.split())

            section_sizes[section] = {
                'lines': lines,
                'chars': chars,
                'words': words
            }

        return section_sizes

    def check_vocab_active_size(self):
        """Check if VOCAB_ACTIVE section is getting too large."""
        pattern = r'<!-- §VOCAB_ACTIVE -->(.*?)<!-- /§VOCAB_ACTIVE -->'
        match = re.search(pattern, self.content, re.DOTALL)

        if match:
            vocab_content = match.group(1)

            # Count vocabulary entries (table rows)
            word_rows = len(re.findall(r'^\|[^-|]', vocab_content, re.MULTILINE))

            self.stats['vocab_active_words'] = word_rows

            if word_rows > 100:
                self.warnings.append(
                    f"§VOCAB_ACTIVE has {word_rows} words. Consider archiving "
                    "words older than 30 days with mastery ⭐⭐⭐ to §VOCAB_ARCHIVE."
                )
            elif word_rows > 50:
                self.warnings.append(
                    f"§VOCAB_ACTIVE has {word_rows} words. Plan to archive old words soon."
                )

    def check_archive_exists(self):
        """Check if archive section exists and is being used."""
        pattern = r'<!-- §VOCAB_ARCHIVE -->(.*?)<!-- /§VOCAB_ARCHIVE -->'
        match = re.search(pattern, self.content, re.DOTALL)

        if match:
            archive_content = match.group(1)
            word_rows = len(re.findall(r'^\|[^-|]', archive_content, re.MULTILINE))

            self.stats['vocab_archive_words'] = word_rows

            if word_rows == 0 and self.stats.get('vocab_active_words', 0) > 50:
                self.warnings.append(
                    "No words in archive, but many active words. "
                    "Consider archiving mastered words."
                )

    def validate(self):
        """Run all validation checks."""
        print(f"🔍 Validating context sharding in: {self.filepath}")
        print()

        if not self.load_file():
            return False

        # Run all checks
        self.check_sharding_enabled()
        self.check_section_markers()
        self.check_section_order()
        self.check_nested_markers()
        self.check_vocab_active_size()
        self.check_archive_exists()

        # Display results
        return self.display_results()

    def display_results(self):
        """Display validation results."""
        if not self.errors and not self.warnings:
            print("✅ Context sharding validation PASSED!")
            print("🎉 All section markers are correct!")
            print()
            self.display_stats()
            return True

        if self.errors:
            print("❌ ERRORS FOUND:")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")
            print()

        if self.warnings:
            print("⚠️  WARNINGS:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")
            print()

        self.display_stats()

        if self.errors:
            print("❌ Validation FAILED - please fix errors above")
            return False
        else:
            print("✅ Validation PASSED (with warnings)")
            return True

    def display_stats(self):
        """Display statistics about the file."""
        print("📊 SECTION STATISTICS:")
        print(f"   Sections found: {self.stats.get('sections_found', 0)}/{self.stats.get('sections_required', 10)}")

        if 'vocab_active_words' in self.stats:
            print(f"   Active vocabulary: {self.stats['vocab_active_words']} words")

        if 'vocab_archive_words' in self.stats:
            print(f"   Archived vocabulary: {self.stats['vocab_archive_words']} words")

        print()

        if self.verbose:
            self.display_section_sizes()

    def display_section_sizes(self):
        """Display detailed section size analysis."""
        print("📏 SECTION SIZE ANALYSIS:")
        section_sizes = self.analyze_section_sizes()

        for section, sizes in sorted(section_sizes.items()):
            print(f"   §{section}:")
            print(f"      Lines: {sizes['lines']}, Words: {sizes['words']}, Chars: {sizes['chars']}")

        print()

    def create_backup(self):
        """Create backup of the file before fixing."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.filepath}.backup_{timestamp}"

        try:
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(self.content)
            print(f"💾 Backup created: {backup_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to create backup: {e}")
            return False

    def auto_fix(self):
        """Attempt to automatically fix common issues."""
        print("🔧 Attempting to auto-fix issues...")
        print()

        if not self.create_backup():
            print("❌ Cannot proceed without backup")
            return False

        fixed_content = self.content
        fixes_applied = []

        # Fix 1: Add context sharding header if missing
        if "CONTEXT SHARDING ENABLED" not in fixed_content:
            header_pattern = r'(For complete system instructions, see: docs/SYSTEM_PROMPT\.md)'
            replacement = r'\1\n\n⚡ CONTEXT SHARDING ENABLED - Load only relevant sections based on lesson type'
            fixed_content = re.sub(header_pattern, replacement, fixed_content)
            fixes_applied.append("Added context sharding header")

        # Fix 2: Wrap sections missing markers (basic heuristic)
        # This is a simplified fix - in production, you'd want more sophisticated logic

        if fixes_applied:
            try:
                with open(self.filepath, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)

                print("✅ Auto-fix applied:")
                for fix in fixes_applied:
                    print(f"   • {fix}")
                print()
                print("Run validator again to verify fixes.")
                return True
            except Exception as e:
                print(f"❌ Failed to write fixes: {e}")
                return False
        else:
            print("ℹ️  No auto-fixable issues found")
            return True


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    filepath = sys.argv[1]
    verbose = '--verbose' in sys.argv or '--stats' in sys.argv
    auto_fix = '--fix' in sys.argv

    validator = ContextShardingValidator(filepath, verbose=verbose)

    if auto_fix:
        validator.load_file()
        validator.auto_fix()
        print()

    success = validator.validate()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
