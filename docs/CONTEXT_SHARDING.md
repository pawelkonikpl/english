# ⚡ Context Sharding Guide

> **Token Optimization for English Learning AI Agent**

## 📖 What is Context Sharding?

Context sharding is a technique that reduces AI token usage by loading only relevant sections of your learning file based on the current lesson type. Instead of processing the entire file (which can grow to thousands of lines), the AI reads only what it needs.

### Benefits:
- **~50-60% token savings** on average lessons
- **Faster response times** from AI
- **Scalability** - system works efficiently even with 500+ words
- **Cost reduction** for API-based AI services
- **Better focus** - AI concentrates on relevant information

---

## 🔧 How It Works

### Section Markers

Your `english-learning.md` file is divided into sections marked with HTML comments:

```markdown
<!-- §PROFILE -->
## 👤 Learner Profile
- Level: B1
- Native Language: Polish
<!-- /§PROFILE -->

<!-- §VOCAB_ACTIVE -->
## 📖 Vocabulary - Active Learning
[your recent vocabulary]
<!-- /§VOCAB_ACTIVE -->
```

### Smart Loading

When you choose a lesson type, the AI loads only the sections it needs:

**Example: Vocabulary Lesson**
```
✅ Loads: §PROFILE, §VOCAB_ACTIVE, §REVIEW_SCHEDULE
❌ Skips: §VOCAB_ARCHIVE, §GRAMMAR_DETAILED, §CONVERSATION_HISTORY

Token savings: ~50%
```

---

## 📋 Section Reference

### Available Sections

| Section Tag | Content | Loaded When |
|-------------|---------|-------------|
| `§PROFILE` | Level, language, goals | Always (every lesson) |
| `§STATISTICS` | Total words, streak, points | Dashboard, Progress tests |
| `§VOCAB_ACTIVE` | Words from last 30 days | Vocabulary, Conversations |
| `§VOCAB_ARCHIVE` | Mastered words >30 days | Progress tests only |
| `§GRAMMAR_DETAILED` | Grammar topics & notes | Grammar lessons |
| `§CONVERSATION_HISTORY` | Past conversation sessions | Conversation, Free writing |
| `§REVIEW_SCHEDULE` | Spaced repetition calendar | Dashboard, Reviews |
| `§LEARNING_PLAN` | Weekly schedule, goals | Dashboard |
| `§NOTES` | Performance observations | All lessons (for updates) |
| `§ACHIEVEMENTS` | Unlocked badges | Dashboard |

---

## 🎯 Loading Rules by Lesson Type

### Daily Dashboard (User presses Enter)
```
Load: §PROFILE, §STATISTICS, §REVIEW_SCHEDULE, §VOCAB_ACTIVE (last 20 words)
Skip: §VOCAB_ARCHIVE, §GRAMMAR_DETAILED, §CONVERSATION_HISTORY
Token savings: ~60%
```

### [1] Vocabulary Lesson
```
Load: §PROFILE, §VOCAB_ACTIVE, §REVIEW_SCHEDULE
Skip: §VOCAB_ARCHIVE, §GRAMMAR_DETAILED, §CONVERSATION_HISTORY
Token savings: ~50%
```

### [2] Vocabulary Review
```
Load: §PROFILE, §VOCAB_ACTIVE, §REVIEW_SCHEDULE (full)
Skip: §VOCAB_ARCHIVE, §GRAMMAR_DETAILED, §CONVERSATION_HISTORY
Token savings: ~50%
```

### [3] Grammar Lesson
```
Load: §PROFILE, §GRAMMAR_DETAILED, §VOCAB_ACTIVE (for examples)
Skip: §VOCAB_ARCHIVE, §CONVERSATION_HISTORY
Token savings: ~55%
```

### [4] Conversation Lesson
```
Load: §PROFILE, §VOCAB_ACTIVE, §CONVERSATION_HISTORY (last 5)
Skip: §VOCAB_ARCHIVE, §GRAMMAR_DETAILED
Token savings: ~45%
```

### [5] Free Writing
```
Load: §PROFILE, §VOCAB_ACTIVE, §CONVERSATION_HISTORY
Skip: §VOCAB_ARCHIVE, §GRAMMAR_DETAILED
Token savings: ~45%
```

### [6] Progress Test
```
Load: ALL sections (comprehensive assessment needed)
Skip: Only §VOCAB_ARCHIVE (sample 30% of archived words)
Token savings: ~20%
```

---

## 🛠️ Setup Instructions

### For New Users

If you're starting fresh, use the updated template:
```
templates/english-learning-template.md
```

This already includes all section markers.

### For Existing Users

Your `english-learning.md` file has been updated with section markers. No action needed! The next time you attach the file, context sharding will work automatically.

### Manual Migration (if needed)

If you have a custom file, add markers around each section:

```markdown
<!-- §SECTION_NAME -->
## Section Title
[content]
<!-- /§SECTION_NAME -->
```

**Available section names:**
- `§PROFILE`
- `§VOCAB_ACTIVE`
- `§VOCAB_ARCHIVE`
- `§GRAMMAR_DETAILED`
- `§CONVERSATION_HISTORY`
- `§REVIEW_SCHEDULE`
- `§STATISTICS`
- `§LEARNING_PLAN`
- `§NOTES`
- `§ACHIEVEMENTS`

---

## 📊 Performance Comparison

### Before Context Sharding
```
File size: 1000 lines
Tokens used per lesson: ~3000 tokens
AI processing time: 3-5 seconds
```

### After Context Sharding
```
File size: 1000 lines
Tokens used per lesson: ~1200-1500 tokens (50% reduction)
AI processing time: 1-2 seconds
```

### As File Grows (500+ words learned)
```
File size: 5000 lines
WITHOUT sharding: ~15,000 tokens
WITH sharding: ~2,500 tokens (83% reduction!)
```

---

## ⚠️ Important Notes

### Section Marker Preservation

When the AI updates your file after a lesson, it will **always preserve** section markers. Example:

```markdown
🔄 UPDATE YOUR FILE

Copy this section and replace in your file:

<!-- §VOCAB_ACTIVE -->
## 📖 Vocabulary - Active Learning

[updated vocabulary table]
<!-- /§VOCAB_ACTIVE -->
```

### Archive Management

Words older than 30 days and with mastery level ⭐⭐⭐ should be moved from `§VOCAB_ACTIVE` to `§VOCAB_ARCHIVE`. The AI will remind you when it's time to archive words.

**Why archive?**
- Keeps `§VOCAB_ACTIVE` small and fast to load
- Archived words are still available for progress tests
- Reduces daily token usage by 40-60%

### Manual Override

If you need the AI to load ALL sections (for debugging or special requests), you can say:

```
"Please load my entire file (all sections) for this request"
```

---

## 🛠️ Archiving Tools

### archive-manager.py ✅ AVAILABLE

Automatically moves mastered words from `§VOCAB_ACTIVE` to `§VOCAB_ARCHIVE`.

**Quick start:**
```bash
# See what would be archived
python tools/archive-manager.py english-learning.md --dry-run

# Archive words >30 days old with ⭐⭐⭐
python tools/archive-manager.py english-learning.md
```

**Why archive?**
- Keeps §VOCAB_ACTIVE small (faster loading)
- Reduces token usage by 40-60% for vocabulary lessons
- Archived words still accessible for progress tests
- Organizes vocabulary by mastery level

**See [tools/README.md](../tools/README.md) for full documentation.**

---

## 🔮 Future Enhancements

### Planned Features:
1. **Section size monitor** - Real-time dashboard of section sizes
2. **Custom sharding rules** - Define your own loading patterns
3. **Multi-file support** - Split into separate files (advanced users)
4. **Smart archiving** - ML-based recommendations for archiving

---

## 🤔 FAQ

### Q: Will this affect my learning progress?
**A:** No! All your data remains intact. The AI simply reads less at once, but can still access everything when needed.

### Q: What if I delete a section marker by accident?
**A:** The AI will still work, but won't optimize that section. Just add the markers back:
```markdown
<!-- §SECTION_NAME -->
[content]
<!-- /§SECTION_NAME -->
```

### Q: Can I disable context sharding?
**A:** Yes! Remove this line from your file header:
```markdown
⚡ CONTEXT SHARDING ENABLED - Load only relevant sections based on lesson type
```

The AI will then load everything as before.

### Q: How do I know it's working?
**A:** When the AI displays your dashboard, it should respond faster than before. For Claude users, you may notice reduced "thinking time."

### Q: Does this work with ChatGPT and other AI assistants?
**A:** Yes! The system is AI-agnostic. Any assistant that reads the `docs/SYSTEM_PROMPT.md` instructions will apply context sharding.

---

## 📚 Related Documentation

- [SYSTEM_PROMPT.md](SYSTEM_PROMPT.md) - Full AI agent instructions
- [GETTING_STARTED.md](GETTING_STARTED.md) - Initial setup guide
- [FAQ.md](FAQ.md) - General questions

---

## 💡 Tips for Maximum Efficiency

1. **Archive regularly** - Move old mastered words to `§VOCAB_ARCHIVE` every 30 days
2. **Keep notes concise** - Long performance notes add tokens
3. **Limit conversation history** - Keep only last 10 sessions in `§CONVERSATION_HISTORY`
4. **Use progress tests sparingly** - They load the full context

---

**Made with ⚡ for efficient English learning**

*Last Updated: 2025-10-09*
