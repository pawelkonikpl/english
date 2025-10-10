#!/usr/bin/env python3
"""
Archive Manager for English Learning System
Automatically moves mastered words from §VOCAB_ACTIVE to §VOCAB_ARCHIVE

Usage:
    python archive-manager.py <your-learning-file.md>
    python archive-manager.py english-learning.md --dry-run
    python archive-manager.py english-learning.md --days 30 --mastery 3

Options:
    --dry-run       Show what would be archived without making changes
    --days N        Archive words older than N days (default: 30)
    --mastery N     Require N stars for archiving (default: 3 = ⭐⭐⭐)
    --force         Archive even if mastery requirement not met
    --verbose       Show detailed processing information
"""

import sys
import re
import os
from datetime import datetime, timedelta
from collections import defaultdict


class ArchiveManager:
    def __init__(self, filepath, days=30, mastery_level=3, dry_run=False,
                 force=False, verbose=False):
        self.filepath = filepath
        self.days_threshold = days
        self.mastery_level = mastery_level
        self.dry_run = dry_run
        self.force = force
        self.verbose = verbose
        self.content = ""
        self.words_to_archive = []
        self.stats = {
            'total_active': 0,
            'eligible': 0,
            'archived': 0,
            'too_young': 0,
            'low_mastery': 0
        }

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

    def parse_date(self, date_str):
        """Parse date string in format YYYY-MM-DD."""
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d')
            except:
                return None

    def count_stars(self, mastery_str):
        """Count stars in mastery string."""
        return mastery_str.count('⭐')

    def extract_vocab_active(self):
        """Extract vocabulary from §VOCAB_ACTIVE section."""
        pattern = r'<!-- §VOCAB_ACTIVE -->(.*?)<!-- /§VOCAB_ACTIVE -->'
        match = re.search(pattern, self.content, re.DOTALL)

        if not match:
            print("❌ Error: §VOCAB_ACTIVE section not found")
            return []

        vocab_section = match.group(1)

        # Find all table rows (format: | word | translation | date | ... | mastery | next_review |)
        row_pattern = r'\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*([^|]*?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|'

        words = []
        for match in re.finditer(row_pattern, vocab_section):
            word = match.group(1).strip()
            translation = match.group(2).strip()
            date_learned = match.group(3).strip()
            last_review = match.group(4).strip()
            mastery = match.group(5).strip()
            next_review = match.group(6).strip()

            # Skip header row
            if word.lower() == 'word' or '---' in word:
                continue

            words.append({
                'word': word,
                'translation': translation,
                'date_learned': date_learned,
                'last_review': last_review,
                'mastery': mastery,
                'next_review': next_review,
                'full_match': match.group(0)
            })

        self.stats['total_active'] = len(words)
        return words

    def identify_archivable_words(self, words):
        """Identify words that should be archived."""
        today = datetime.now()
        archivable = []

        for word in words:
            date_learned = self.parse_date(word['date_learned'])
            if not date_learned:
                if self.verbose:
                    print(f"⚠️  Skipping '{word['word']}' - invalid date format")
                continue

            days_old = (today - date_learned).days
            star_count = self.count_stars(word['mastery'])

            # Check if word is old enough
            if days_old < self.days_threshold:
                self.stats['too_young'] += 1
                if self.verbose:
                    print(f"⏳ '{word['word']}' - only {days_old} days old (need {self.days_threshold})")
                continue

            # Check mastery level (unless force mode)
            if not self.force and star_count < self.mastery_level:
                self.stats['low_mastery'] += 1
                if self.verbose:
                    print(f"📚 '{word['word']}' - mastery {star_count}/{self.mastery_level} stars (need {self.mastery_level})")
                continue

            # Word is eligible for archiving
            self.stats['eligible'] += 1
            archivable.append({
                **word,
                'days_old': days_old,
                'star_count': star_count
            })

        return archivable

    def create_backup(self):
        """Create backup of the file."""
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

    def move_to_archive(self, words_to_archive):
        """Move words from §VOCAB_ACTIVE to §VOCAB_ARCHIVE."""
        if not words_to_archive:
            return self.content

        modified_content = self.content

        # Extract current archive section
        archive_pattern = r'(<!-- §VOCAB_ARCHIVE -->)(.*?)(<!-- /§VOCAB_ARCHIVE -->)'
        archive_match = re.search(archive_pattern, modified_content, re.DOTALL)

        if not archive_match:
            print("❌ Error: §VOCAB_ARCHIVE section not found")
            return modified_content

        archive_content = archive_match.group(2)
        archive_start = archive_match.group(1)
        archive_end = archive_match.group(3)

        # Prepare archive entries
        today = datetime.now().strftime("%Y-%m-%d")
        current_month = datetime.now().strftime("%B %Y")

        # Check if we need to add a new month header
        if f"### Archive - {current_month}" not in archive_content:
            # Add new month section
            new_month_section = f"\n\n### Archive - {current_month}\n| Word | Translation | Mastery | Archived Date |\n|------|-------------|---------|---------------|\n"

            # Insert after the intro text
            intro_pattern = r'(\*[^\*]+\*)'
            if re.search(intro_pattern, archive_content):
                archive_content = re.sub(intro_pattern, r'\1' + new_month_section, archive_content, count=1)
            else:
                archive_content = new_month_section + archive_content

        # Add each word to archive
        for word in words_to_archive:
            archive_row = f"| {word['word']} | {word['translation']} | {word['mastery']} | {today} |\n"

            # Find the right month section and append
            month_pattern = f"(### Archive - {current_month}.*?\\n\\|[^\\n]+\\n\\|[^\\n]+\\n)"
            archive_content = re.sub(
                month_pattern,
                r'\1' + archive_row,
                archive_content,
                flags=re.DOTALL
            )

        # Reconstruct archive section
        new_archive_section = archive_start + archive_content + archive_end
        modified_content = re.sub(archive_pattern, new_archive_section, modified_content, flags=re.DOTALL)

        # Remove archived words from §VOCAB_ACTIVE
        for word in words_to_archive:
            # Escape special regex characters in word
            escaped_word = re.escape(word['full_match'])
            modified_content = re.sub(escaped_word + r'\s*\n?', '', modified_content)

        # Update statistics
        stats_pattern = r'(- \*\*Total Words Learned:\*\* )(\d+)'
        stats_match = re.search(stats_pattern, modified_content)
        if stats_match:
            total_words = int(stats_match.group(2))

            # Update Active Words count
            active_pattern = r'(- \*\*Active Words \(Learning\):\*\* )(\d+)'
            active_match = re.search(active_pattern, modified_content)
            if active_match:
                new_active = int(active_match.group(2)) - len(words_to_archive)
                modified_content = re.sub(active_pattern, r'\g<1>' + str(new_active), modified_content)

            # Update Archived Words count
            archived_pattern = r'(- \*\*Archived Words \(Mastered\):\*\* )(\d+)'
            archived_match = re.search(archived_pattern, modified_content)
            if archived_match:
                new_archived = int(archived_match.group(2)) + len(words_to_archive)
                modified_content = re.sub(archived_pattern, r'\g<1>' + str(new_archived), modified_content)

        return modified_content

    def save_file(self, content):
        """Save modified content to file."""
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"❌ Error writing file: {e}")
            return False

    def run(self):
        """Run the archive manager."""
        print(f"🗄️  Archive Manager - {self.filepath}")
        print()
        print(f"⚙️  Settings:")
        print(f"   Days threshold: {self.days_threshold}")
        print(f"   Mastery requirement: {self.mastery_level} stars ({'⭐' * self.mastery_level})")
        print(f"   Mode: {'DRY RUN (no changes)' if self.dry_run else 'LIVE (will modify file)'}")
        if self.force:
            print(f"   ⚠️  FORCE mode: ignoring mastery requirement")
        print()

        # Load file
        if not self.load_file():
            return False

        # Extract vocabulary
        print("📖 Analyzing vocabulary...")
        words = self.extract_vocab_active()

        if not words:
            print("ℹ️  No words found in §VOCAB_ACTIVE")
            return True

        # Identify archivable words
        archivable = self.identify_archivable_words(words)

        # Display results
        print()
        print("📊 ANALYSIS RESULTS:")
        print(f"   Total active words: {self.stats['total_active']}")
        print(f"   Eligible for archive: {self.stats['eligible']}")
        if self.stats['too_young'] > 0:
            print(f"   Too young to archive: {self.stats['too_young']}")
        if self.stats['low_mastery'] > 0:
            print(f"   Low mastery (not ready): {self.stats['low_mastery']}")
        print()

        if not archivable:
            print("✅ No words to archive!")
            print()
            print("💡 Tips:")
            print(f"   • Words need to be at least {self.days_threshold} days old")
            print(f"   • Words need {self.mastery_level} stars ({'⭐' * self.mastery_level})")
            print(f"   • Use --force to archive regardless of mastery")
            print(f"   • Use --days N to change age threshold")
            return True

        # Show words to be archived
        print(f"📦 WORDS TO ARCHIVE ({len(archivable)}):")
        print()
        for word in archivable:
            print(f"   ✓ {word['word']:<20} ({word['days_old']} days old, {word['mastery']})")
        print()

        if self.dry_run:
            print("🔍 DRY RUN - No changes made")
            print()
            print("To actually archive these words, run without --dry-run:")
            print(f"   python archive-manager.py {self.filepath}")
            return True

        # Confirm action
        if not self.force:
            response = input("Continue with archiving? [y/N]: ")
            if response.lower() not in ['y', 'yes']:
                print("❌ Cancelled by user")
                return False
            print()

        # Create backup
        if not self.create_backup():
            return False

        # Perform archiving
        print("🔄 Archiving words...")
        modified_content = self.move_to_archive(archivable)

        # Save file
        if self.save_file(modified_content):
            print("✅ Successfully archived!")
            print()
            print("📊 UPDATED STATISTICS:")
            print(f"   Words archived: {len(archivable)}")
            print(f"   Active words remaining: {self.stats['total_active'] - len(archivable)}")
            print()
            print("💡 Next steps:")
            print("   1. Attach your file to AI to verify")
            print("   2. Run context-sharding-validator.py to check structure")
            self.stats['archived'] = len(archivable)
            return True
        else:
            return False


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    filepath = sys.argv[1]

    # Parse options
    dry_run = '--dry-run' in sys.argv
    force = '--force' in sys.argv
    verbose = '--verbose' in sys.argv

    # Parse --days argument
    days = 30
    try:
        days_idx = sys.argv.index('--days')
        days = int(sys.argv[days_idx + 1])
    except (ValueError, IndexError):
        pass

    # Parse --mastery argument
    mastery = 3
    try:
        mastery_idx = sys.argv.index('--mastery')
        mastery = int(sys.argv[mastery_idx + 1])
    except (ValueError, IndexError):
        pass

    # Create manager and run
    manager = ArchiveManager(
        filepath=filepath,
        days=days,
        mastery_level=mastery,
        dry_run=dry_run,
        force=force,
        verbose=verbose
    )

    success = manager.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
