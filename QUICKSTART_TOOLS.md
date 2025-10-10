# 🚀 Quick Start: Context Sharding Tools

> Get up and running with context sharding optimization in 5 minutes

## ⚡ What You Get

**50-60% token reduction** on AI interactions through smart section loading.

---

## 📋 Step-by-Step Guide

### 1. Validate Your File

Check if context sharding is properly configured:

```bash
cd /path/to/your/project
python tools/context-sharding-validator.py english-learning.md
```

**Expected output:**
```
✅ Context sharding validation PASSED!
🎉 All section markers are correct!

📊 SECTION STATISTICS:
   Sections found: 10/10
   Active vocabulary: 5 words
```

**If you see errors**, run auto-fix:
```bash
python tools/context-sharding-validator.py english-learning.md --fix
```

---

### 2. Monitor Your Vocabulary

Check section sizes to see if archiving is needed:

```bash
python tools/context-sharding-validator.py english-learning.md --verbose
```

**Watch for:**
```
⚠️ WARNINGS:
   1. §VOCAB_ACTIVE has 52 words. Plan to archive old words soon.
```

---

### 3. Archive Old Words (When Ready)

After 30+ days of learning, archive mastered words:

```bash
# Preview what would be archived
python tools/archive-manager.py english-learning.md --dry-run

# Actually archive (creates backup automatically)
python tools/archive-manager.py english-learning.md
```

**Expected output:**
```
📦 WORDS TO ARCHIVE (3):

   ✓ accomplish          (45 days old, ⭐⭐⭐)
   ✓ realize             (32 days old, ⭐⭐⭐)
   ✓ achieve             (31 days old, ⭐⭐⭐)

Continue with archiving? [y/N]: y

💾 Backup created: english-learning.md.backup_20251009_143522
✅ Successfully archived!
```

---

## 🔄 Regular Workflow

### Daily/Weekly

```bash
# Quick validation
python tools/context-sharding-validator.py english-learning.md
```

### Monthly (or when §VOCAB_ACTIVE >50 words)

```bash
# Archive old mastered words
python tools/archive-manager.py english-learning.md --dry-run
python tools/archive-manager.py english-learning.md
```

### After Major Edits

```bash
# Full validation with details
python tools/context-sharding-validator.py english-learning.md --verbose
```

---

## 🎯 Common Scenarios

### Scenario 1: New User (Just Starting)

```bash
# 1. Copy template
cp templates/english-learning-template.md my-learning.md

# 2. Validate (should pass immediately)
python tools/context-sharding-validator.py my-learning.md

# 3. Start learning!
# (No archiving needed for first 30 days)
```

---

### Scenario 2: Existing User (Migrating)

Your file has been updated with section markers already. Just validate:

```bash
python tools/context-sharding-validator.py english-learning.md
```

---

### Scenario 3: Power User (Many Words)

```bash
# 1. Check status
python tools/context-sharding-validator.py english-learning.md --verbose

# 2. Archive aggressively (lower threshold)
python tools/archive-manager.py english-learning.md --days 20 --dry-run

# 3. If happy with preview, archive
python tools/archive-manager.py english-learning.md --days 20
```

---

## 🔧 Customization Options

### Validator Options

```bash
# Basic check
python tools/context-sharding-validator.py english-learning.md

# Detailed analysis
python tools/context-sharding-validator.py english-learning.md --verbose

# Auto-fix issues
python tools/context-sharding-validator.py english-learning.md --fix
```

### Archive Manager Options

```bash
# Change age threshold
python tools/archive-manager.py english-learning.md --days 45

# Require higher mastery
python tools/archive-manager.py english-learning.md --mastery 3

# Archive regardless of mastery (use carefully!)
python tools/archive-manager.py english-learning.md --force

# See detailed processing
python tools/archive-manager.py english-learning.md --dry-run --verbose
```

---

## 📊 Measuring Impact

### Before Context Sharding
```
File: 1000 lines, 150 words
Tokens per lesson: ~3000
Response time: 3-5 seconds
```

### After Context Sharding + Archiving
```
File: 1000 lines, 150 words (50 active, 100 archived)
Tokens per lesson: ~1200 (60% reduction!)
Response time: 1-2 seconds (2x faster!)
```

---

## ⚠️ Troubleshooting

### "Missing required section" error

Run auto-fix:
```bash
python tools/context-sharding-validator.py english-learning.md --fix
```

### "Closing tag without opening tag" error

Manually add opening tag before the closing tag:
```markdown
<!-- §SECTION_NAME -->
## Section Title
...
<!-- /§SECTION_NAME -->
```

### Words not being archived

Check criteria:
```bash
python tools/archive-manager.py english-learning.md --dry-run --verbose
```

Output will show why each word isn't eligible:
```
⏳ 'achieve' - only 15 days old (need 30)
📚 'improve' - mastery 2/3 stars (need 3)
```

---

## 💡 Pro Tips

1. **Always use --dry-run first** when archiving
2. **Run validator after every major edit**
3. **Archive monthly** to keep §VOCAB_ACTIVE lean
4. **Use --verbose** to understand your vocabulary growth
5. **Backups are automatic** - restore with `.backup_*` files if needed

---

## 📚 Next Steps

- Read [CONTEXT_SHARDING.md](docs/CONTEXT_SHARDING.md) for deep dive
- Check [tools/README.md](tools/README.md) for all options
- See [FAQ.md](docs/FAQ.md) for common questions

---

## 🆘 Getting Help

- Validator failing? Check [tools/README.md](tools/README.md#troubleshooting)
- Archive issues? See [CONTEXT_SHARDING.md](docs/CONTEXT_SHARDING.md#faq)
- General questions? Read [FAQ.md](docs/FAQ.md)

---

**Happy optimizing! ⚡**

*Last updated: 2025-10-09*
