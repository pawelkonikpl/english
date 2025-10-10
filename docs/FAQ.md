# Frequently Asked Questions

## General

### What is this?
A free, AI-powered English learning system using markdown files.

### Is it really free?
Yes! Completely free and open-source forever.

### What levels are supported?
All levels: A1 (Beginner) to C2 (Proficient).

### Which AI should I use?
Claude or ChatGPT-4 work best. Both have free tiers.

---

## Technical

### Do I need internet?
Yes, to access AI. But your file works offline.

### Can I use on mobile?
Yes! Both Claude and ChatGPT have mobile apps.

### How do I backup my file?
Save to Google Drive, Dropbox, or use Git.

---

## Learning

### How many words per day?
- Beginners: 3-5 words
- Intermediate: 5-7 words
- Advanced: 7-10 words

### What if I miss a day?
No problem! Just continue where you left off.

### Can I skip reviews?
Not recommended! Reviews are crucial for retention.

---

## System

### Why markdown instead of app?
- No installation
- Works with any AI
- You own your data
- Free forever
- Easy to backup

### Can I customize?
Yes! Edit system prompt, adjust schedule, add custom goals.

---

## Context Sharding ⚡

### What is context sharding?
A technique that reduces AI token usage by 50-60% by loading only relevant sections of your file based on lesson type.

### Do I need to enable it?
New files have it enabled automatically. Existing files can add section markers (see [CONTEXT_SHARDING.md](CONTEXT_SHARDING.md)).

### How do I know it's working?
Run the validator:
```bash
python tools/context-sharding-validator.py english-learning.md
```

### Will it break my existing file?
No! Context sharding is backward compatible. If markers are missing, AI loads the full file as before.

### What are section markers?
HTML comments that mark sections:
```markdown
<!-- §PROFILE -->
## 👤 Learner Profile
...
<!-- /§PROFILE -->
```

### When should I archive words?
Move words to §VOCAB_ARCHIVE after:
- 30+ days since learning
- Mastery level ⭐⭐⭐
- Consistent correct usage

The validator warns when §VOCAB_ACTIVE has >50 words.

**Use the archive-manager tool:**
```bash
# Preview what would be archived
python tools/archive-manager.py english-learning.md --dry-run

# Actually archive
python tools/archive-manager.py english-learning.md
```

### Does this work with ChatGPT?
Yes! Context sharding works with any AI that reads the system prompt (Claude, ChatGPT, etc.).

### How much does it save?
- Daily dashboard: ~60% token reduction
- Vocabulary lessons: ~50% reduction
- Grammar lessons: ~55% reduction
- Files with 500+ words: up to 83% reduction

---

## Still have questions?

- Check [Documentation](.)
- Read [CONTEXT_SHARDING.md](CONTEXT_SHARDING.md)
- Open an [Issue](https://github.com/yourusername/english-learning-ai/issues)
- Join [Discussions](https://github.com/yourusername/english-learning-ai/discussions)
