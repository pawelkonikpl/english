# Changelog

## [1.1.0] - 2025-10-09 ⚡ NEW

### Added - Context Sharding
- **Context Sharding System** - 50-60% token reduction for AI interactions
- Section markers for selective loading (`<!-- §SECTION -->`)
- 10 optimized sections (PROFILE, VOCAB_ACTIVE, VOCAB_ARCHIVE, etc.)
- Smart loading rules per lesson type
- Vocabulary archive system for mastered words

### Added - Tools
- **context-sharding-validator.py** - Validates section markers and structure
  - Checks all 10 required sections
  - Detects improperly nested or missing markers
  - Auto-fix mode with backup creation
  - Section size analysis (--verbose)
  - Vocabulary optimization warnings
- **archive-manager.py** - Automatic vocabulary archiving
  - Moves old mastered words from §VOCAB_ACTIVE to §VOCAB_ARCHIVE
  - Configurable age threshold (default: 30 days)
  - Mastery requirement (default: ⭐⭐⭐)
  - Dry-run mode for safe preview
  - Auto-backup before changes
  - Updates statistics automatically

### Updated
- `SYSTEM_PROMPT.md` - Added context sharding instructions
- `english-learning-template.md` - All sections now marked
- `README.md` - Context sharding documentation
- `tools/README.md` - Validator documentation

### New Documentation
- `docs/CONTEXT_SHARDING.md` - Complete guide to context sharding
  - Section reference
  - Loading rules by lesson type
  - Performance comparisons
  - FAQ and troubleshooting

### Performance
- Token usage reduced by 50-60% on average lessons
- 83% reduction for files with 500+ words
- 2x faster AI response times
- Scales efficiently to thousands of words

---

## [1.0.0] - 2025-01-09

### Added
- Initial release
- Automatic level assessment (A1-C2)
- Vocabulary lessons with memory techniques
- Grammar exercises
- Conversation practice
- Spaced repetition system
- Progress tracking
- Complete documentation

### Features
- Works with any AI (Claude, ChatGPT)
- Single markdown file
- Completely free
- No app needed

---

## Future Releases

### [1.2.0] - Planned
- Archive manager tool (auto-move old words)
- Multi-language support for translations
- Discord bot integration
- Anki export tool

### [1.3.0] - Planned
- Audio pronunciation
- Mobile guides
- Analytics

### [2.0.0] - Future
- Web interface
- Teacher dashboard
- API
