# 🛠️ Tools

Utility scripts to enhance your English learning experience.

## Available Tools

### 1. file-validator.py
**Basic structure validation for learning files**

Validates that your `.md` learning file has all required sections and proper formatting.

**Usage:**
```bash
python file-validator.py english-learning.md
```

**What it checks:**
- ✅ System prompt presence
- ✅ Required sections (Profile, Vocabulary, Grammar, etc.)
- ✅ Vocabulary table structure
- ✅ English level specification

---

### 2. context-sharding-validator.py ⚡ NEW
**Advanced validation for context sharding optimization**

Validates section markers and structure to ensure optimal token usage with context sharding.

**Usage:**
```bash
# Basic validation
python context-sharding-validator.py english-learning.md

# Detailed section analysis
python context-sharding-validator.py english-learning.md --verbose

# Auto-fix common issues (creates backup)
python context-sharding-validator.py english-learning.md --fix
```

**What it checks:**
- ✅ All 10 required section markers (`<!-- §SECTION -->`)
- ✅ Proper opening/closing tag pairs
- ✅ No duplicate or improperly nested markers
- ✅ Section order optimization
- ✅ VOCAB_ACTIVE size (warns if >50 words)
- ✅ Archive usage recommendations
- ✅ Context sharding enabled in header

**Example output:**
```
🔍 Validating context sharding in: english-learning.md

✅ Context sharding validation PASSED!
🎉 All section markers are correct!

📊 SECTION STATISTICS:
   Sections found: 10/10
   Active vocabulary: 5 words
   Archived vocabulary: 0 words
```

**Required sections:**
- `§PROFILE` - Learner profile
- `§VOCAB_ACTIVE` - Active vocabulary (last 30 days)
- `§VOCAB_ARCHIVE` - Archived mastered words
- `§GRAMMAR_DETAILED` - Grammar topics
- `§CONVERSATION_HISTORY` - Conversation sessions
- `§REVIEW_SCHEDULE` - Spaced repetition calendar
- `§STATISTICS` - Learning stats
- `§LEARNING_PLAN` - Weekly goals
- `§NOTES` - Performance observations
- `§ACHIEVEMENTS` - Unlocked badges

**Options:**
- `--verbose` - Show detailed section size analysis
- `--stats` - Display section statistics
- `--fix` - Auto-fix common issues (with backup)

---

### 3. archive-manager.py 📦 NEW
**Automatic vocabulary archiving for optimization**

Automatically moves mastered words from `§VOCAB_ACTIVE` to `§VOCAB_ARCHIVE` to keep your active vocabulary lean and token-efficient.

**Usage:**
```bash
# Dry run - see what would be archived
python archive-manager.py english-learning.md --dry-run

# Archive with default settings (30 days, 3 stars)
python archive-manager.py english-learning.md

# Custom thresholds
python archive-manager.py english-learning.md --days 45 --mastery 3

# Force archive (ignore mastery requirement)
python archive-manager.py english-learning.md --force

# Verbose output
python archive-manager.py english-learning.md --dry-run --verbose
```

**What it does:**
- ✅ Finds words older than N days (default: 30)
- ✅ Checks mastery level (default: ⭐⭐⭐)
- ✅ Moves qualified words to `§VOCAB_ARCHIVE`
- ✅ Updates statistics (Active/Archived counts)
- ✅ Creates backup before changes
- ✅ Preserves all word data (translation, mastery, dates)

**Archive criteria:**
1. Word learned >30 days ago (configurable with `--days`)
2. Mastery level ⭐⭐⭐ (3 stars, configurable with `--mastery`)
3. Both criteria must be met (unless `--force` is used)

**Example output:**
```
🗄️  Archive Manager - english-learning.md

⚙️  Settings:
   Days threshold: 30
   Mastery requirement: 3 stars (⭐⭐⭐)
   Mode: DRY RUN (no changes)

📖 Analyzing vocabulary...
⏳ 'achieve' - only 15 days old (need 30)
✓ 'accomplish' (45 days old, ⭐⭐⭐)
✓ 'realize' (32 days old, ⭐⭐⭐)

📊 ANALYSIS RESULTS:
   Total active words: 25
   Eligible for archive: 2
   Too young to archive: 23

📦 WORDS TO ARCHIVE (2):

   ✓ accomplish          (45 days old, ⭐⭐⭐)
   ✓ realize             (32 days old, ⭐⭐⭐)

🔍 DRY RUN - No changes made

To actually archive these words, run without --dry-run:
   python archive-manager.py english-learning.md
```

**Options:**
- `--dry-run` - Preview what would be archived (no changes)
- `--days N` - Archive words older than N days (default: 30)
- `--mastery N` - Require N stars for archiving (default: 3)
- `--force` - Archive regardless of mastery level
- `--verbose` - Show detailed processing info

**Safety features:**
- Always creates backup before modifying
- Confirms before archiving (unless `--force`)
- Validates file structure
- Preserves all word metadata

**When to use:**
- `§VOCAB_ACTIVE` has >50 words (validator warns you)
- You want to optimize token usage
- Old words are taking up space
- Before a progress test

---

## Coming Soon

### section-optimizer.py
Analyze section sizes and suggest optimizations for better token efficiency.

### progress-analyzer.py
Generate insights about your learning progress, streaks, and mastery rates.

### Export Tools

#### to-anki.py
Export vocabulary to Anki flashcard format with spaced repetition.

#### to-csv.py
Export learning data to CSV for analysis in Excel/Google Sheets.

#### to-pdf.py
Generate beautiful PDF progress reports.

---

## Troubleshooting

### Common Issues

**"Missing required section" error:**
```bash
# Add the missing section with proper markers
<!-- §SECTION_NAME -->
## Section Title
[content]
<!-- /§SECTION_NAME -->
```

**"Closing tag without opening tag" error:**
```bash
# Ensure every section has an opening tag BEFORE the closing tag
<!-- §PROFILE -->      ← Opening tag
## 👤 Learner Profile
...
<!-- /§PROFILE -->     ← Closing tag
```

**"VOCAB_ACTIVE has too many words" warning:**
```bash
# Use archive-manager.py to automatically archive old words
python archive-manager.py english-learning.md --dry-run
python archive-manager.py english-learning.md
```

---

## Usage Tips

1. **Run validator after every major edit:**
   ```bash
   python context-sharding-validator.py english-learning.md
   ```

2. **Use --verbose to monitor section growth:**
   ```bash
   python context-sharding-validator.py english-learning.md --verbose
   ```

3. **Auto-fix creates backups** - safe to use:
   ```bash
   python context-sharding-validator.py english-learning.md --fix
   ```

---

## Contributing

Have a useful tool idea? We'd love to see it!

**Ideas welcome:**
- File format converters
- Progress visualizers
- Statistics calculators
- Integration helpers (Discord bots, Telegram bots)
- Mobile app connectors
- Language-specific tools (pronunciation guides, etc.)

See [CONTRIBUTING.md](../docs/CONTRIBUTING.md) for guidelines.

---

*For questions or bug reports, open an issue on GitHub*
