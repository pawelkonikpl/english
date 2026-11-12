# 🎓 English Learning AI Agent

> A universal, AI-powered English learning system that works with any AI assistant (Claude, ChatGPT, etc.) using a single markdown file to track your progress.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/yourusername/english-learning-ai/graphs/commit-activity)

---

## 🖥️ Aplikacja webowa (FastAPI + React)

Oprócz systemu opartego na jednym pliku markdown repozytorium zawiera **lokalną aplikację** do nauki:

- **Frazy do komunikacji**: 239 zwrotów z [`resources/communication-phrases-pl.md`](resources/communication-phrases-pl.md), nauka nowych fraz i dzienny limit,
- **Powtórki**: powtórki w odstępach (1, 3, 7, 14, 30… dni), tryby: rozpoznawanie, wpisywanie i zdanie oceniane przez AI,
- **Rozmowa z AI**: scenki (kawiarnia, spotkanie w pracy, lekarz…) z poprawkami po każdej wiadomości, podpowiedziami i podsumowaniem,
- **Lekcje z AI**: słówka, gramatyka, swobodne pisanie, test poziomujący,
- **Postępy**: seria dni, XP, cel dzienny, osiągnięcia, heatmapa aktywności i podpowiedź „Co dziś?”.

### Wymagania

- Python 3.11+ i [uv](https://docs.astral.sh/uv/) (albo zwykły `pip`),
- Node.js 20+,
- zalogowany **Claude Code** albo **GitHub Copilot** na tym samym komputerze (aplikacja korzysta z Twojej subskrypcji przez ich CLI).

### Instalacja i uruchomienie

```bash
cp .env.example .env      # wybierz providera i modele
make install              # zależności backendu (uv) i frontendu (npm)
make run                  # buduje frontend i uruchamia wszystko: http://127.0.0.1:8000
```

Tryb deweloperski (przeładowanie po zmianach): `make dev`, a potem otwórz http://localhost:5173.

Bez `uv`: `python -m venv .venv && source .venv/bin/activate && pip install -e backend`, a potem `python -m english_app`.

### Wybór modelu AI (`.env`)

| Zmienna | Znaczenie |
|---|---|
| `LLM_PROVIDER` | `claude_code` (subskrypcja Claude), `copilot` (subskrypcja GitHub Copilot) albo `fake` (przykładowe odpowiedzi bez AI, do testów) |
| `CLAUDE_CODE_MODEL`, `CLAUDE_CODE_MODEL_FAST` | model główny (rozmowa, lekcje) i szybki (podpowiedzi, oceny zdań, wyjaśnienia) |
| `CLAUDE_CODE_MODELS` | lista modeli do wyboru w ustawieniach aplikacji |
| `COPILOT_MODEL`, `COPILOT_MODEL_FAST` | to samo dla Copilota; listę modeli Copilot podaje sam |

Model zmienisz też w aplikacji: **Ustawienia → Model AI** (bez restartu, z przyciskiem „Testuj”).

**Claude Code:** zainstaluj Claude Code i zaloguj się (uruchom `claude`, przy pierwszym starcie albo poleceniem `/login`).
**GitHub Copilot:** pobierz runtime (`cd backend && uv run python -m copilot download-runtime`) i zaloguj się w Copilot CLI albo ustaw `COPILOT_GITHUB_TOKEN`.
Modele działają **bez narzędzi** i w pustym katalogu tymczasowym: AI może tylko rozmawiać, nie ma dostępu do plików ani terminala.

### Budowa

```
backend/src/english_app/
  core/        konfiguracja, baza (SQLite + Alembic), rejestr modułów, zdarzenia
  llm/         interfejs LLMProvider, fabryka providerów, wybór modelu, LLMService
  modules/     profile, phrases, review, progress, conversation, lessons
frontend/src/
  modules/     ekrany modułów (dashboard, frazy, powtórki, rozmowa, lekcje, ustawienia)
```

- **Nowy provider AI:** klasa dziedzicząca po `LLMProvider` (`backend/src/english_app/llm/base.py`) i jeden wpis w `PROVIDER_FACTORIES` (`llm/factory.py`).
- **Moduły:** zmienna `ENABLED_MODULES` w `.env` włącza i wyłącza moduły; wyłączony moduł znika z API i z menu.
- **Aktualizacja fraz:** po zmianie pliku md uruchom `cd backend && uv run python scripts/build_phrases_seed.py`.
- **Testy:** `make test` (pytest dla backendu, vitest dla frontendu). Testy nie wołają prawdziwego AI: używają providera `fake` i podstawionych SDK.

---

## 📖 Table of Contents

- [Features](#-features)
- [How It Works](#-how-it-works)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [System Architecture](#-system-architecture)
- [Context Sharding](#-context-sharding-new)
- [Examples](#-examples)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

- 🎯 **Automatic Level Assessment** - AI determines your English level (A1-C2) through interactive questions
- 📚 **Personalized Learning** - Lessons adapted to your specific level and goals
- 🔄 **Spaced Repetition System** - Scientific review schedule (3, 7, 14, 30 days)
- 🧠 **Memory Techniques** - Mnemonics and associations for better retention
- 📊 **Progress Tracking** - Detailed statistics and achievement system
- 🔗 **Knowledge Integration** - New lessons incorporate previously learned words
- ⚡ **Context Sharding** - Smart token optimization (50-60% reduction) for faster, cheaper AI interactions
- 💾 **Simple & Portable** - Just one `.md` file, works offline with any AI
- 🌍 **Universal Support** - Works for learners at any level (beginner to advanced)
- 🆓 **Completely Free** - No subscription, no app required

---

## 🔍 How It Works

The system uses a simple yet powerful approach:

1. **Initial Assessment**: AI asks 3-5 questions to determine your level
2. **Personal File Creation**: AI generates your `english-learning.md` file
3. **Daily Learning**: Attach the file to any AI chat, press Enter, and get a personalized lesson menu
4. **Automatic Tracking**: Progress is saved to your file after each lesson
5. **Intelligent Reviews**: AI reminds you when it's time to review learned material

```
┌─────────────────┐
│  User + AI Chat │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ english-learning.md │ ◄──── All your progress stored here
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Personalized       │
│  Lesson Menu        │
│  📚 Vocabulary      │
│  ✏️ Grammar        │
│  💬 Conversation   │
└─────────────────────┘
```

---

## 🚀 Quick Start

### Step 1: Initial Setup (First Time Only)

1. Start a new chat with any AI assistant (Claude, ChatGPT, etc.)
2. Copy and paste this message:

```
I want to start learning English with the AI Learning System.
Please conduct an initial assessment to determine my level.
```

3. Answer 3-5 assessment questions
4. AI will generate your personal `english-learning.md` file
5. Copy the generated content and save it as `english-learning.md`

### Step 2: Daily Learning

1. Open a new AI chat session
2. Attach your `english-learning.md` file
3. Press **Enter** (don't type anything!)
4. AI will display your progress dashboard and lesson menu
5. Choose a lesson (1-6) and start learning!

---

## 📚 Usage

### Lesson Types

After attaching your file, you'll see 6 lesson options:

| Type | Description | Best For |
|------|-------------|----------|
| 📚 **Vocabulary** | Learn 5 new words with memory techniques | Building word bank |
| 🔄 **Review** | Spaced repetition of learned words | Retention |
| ✏️ **Grammar** | Interactive grammar exercises | Structure mastery |
| 💬 **Conversation** | Guided dialogue practice | Practical usage |
| 🗣️ **Free Writing** | Write freely, get feedback | Fluency |
| 🏆 **Progress Test** | Check what you remember | Self-assessment |

### Example Session

```
USER: [Attaches english-learning.md and presses Enter]

AI:   📚 ENGLISH LEARNING SYSTEM
      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

      📊 YOUR PROGRESS:
      ✅ Current Level: B1
      ✅ Words Learned: 15
      ✅ Days Streak: 3
      ✅ Last Lesson: Vocabulary (2025-01-09)

      🔔 REMINDERS:
      ⚠️ 5 words need review today!

      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

      📋 LESSON MENU:

      📚 [1] VOCABULARY
      🔄 [2] VOCABULARY REVIEW (Recommended!)
      ✏️ [3] GRAMMAR
      💬 [4] CONVERSATION
      🗣️ [5] FREE WRITING
      🏆 [6] PROGRESS TEST

      💡 RECOMMENDATION: [2] - You have words to review!

      Choose 1-6:

USER: 2

AI:   [Conducts personalized review session]
```

---

## 🏗️ System Architecture

### File Structure

```
english-learning-ai/
├── README.md                          # This file
├── docs/
│   ├── SYSTEM_PROMPT.md              # Complete AI agent instructions
│   ├── CONTEXT_SHARDING.md           # Context sharding documentation
│   ├── TEMPLATE.md                    # File template for users
│   ├── GETTING_STARTED.md            # Detailed getting started guide
│   ├── FAQ.md                         # Frequently asked questions
│   └── CONTRIBUTING.md                # Contribution guidelines
├── examples/
│   ├── beginner-example.md           # Example A1-A2 learner file
│   ├── intermediate-example.md       # Example B1-B2 learner file
│   └── advanced-example.md           # Example C1-C2 learner file
├── templates/
│   └── english-learning-template.md  # Copy-paste ready template
├── tools/
│   └── file-validator.py             # Validates .md file structure
└── LICENSE
```

### Core Components

1. **AI System Prompt** (`docs/SYSTEM_PROMPT.md`)
   - Instructions embedded in user's learning file
   - Tells AI how to conduct assessments
   - Defines lesson formats and tracking logic

2. **Learning File** (`english-learning.md`)
   - User's personal progress tracker
   - Contains: vocabulary, grammar, statistics, review schedule
   - Updated after each lesson

3. **Assessment Module**
   - 3-5 questions to determine level
   - Tests: self-assessment, translation, grammar, goals
   - Assigns appropriate level (A1-C2)

4. **Lesson Modules**
   - Vocabulary: 5 words with memory techniques
   - Grammar: Level-appropriate exercises
   - Conversation: Scenario-based practice
   - Review: Spaced repetition algorithm

---

## 📖 Examples

### Level-Specific Content

**A1 (Beginner) - Vocabulary Lesson:**
```
Word: CAT /kæt/
Translation: kot
Memory: CAT sounds like "kat" in many languages 🐱
Example: I have a cat. The cat is black.
```

**B2 (Upper-Intermediate) - Vocabulary Lesson:**
```
Word: ACCOMPLISH /əˈkʌmplɪʃ/
Translation: osiągnąć, wykonać
Memory: "a-COM-plish" → COMplete your mission = accomplish it! 🎯
Example: She managed to accomplish all her goals despite facing numerous obstacles.
```

**C1 (Advanced) - Vocabulary Lesson:**
```
Word: NOTWITHSTANDING /ˌnɒtwɪθˈstændɪŋ/
Translation: pomimo, mimo że
Context: Formal/legal language, often used in writing
Example: Notwithstanding the considerable challenges, the project was completed ahead of schedule.
Collocations: notwithstanding the fact that, notwithstanding anything to the contrary
```

---

## ⚡ Context Sharding (NEW)

### Token Optimization for Efficient Learning

The system uses **context sharding** to dramatically reduce AI token usage and improve response times. Instead of loading your entire learning file (which can grow to thousands of lines), the AI loads only relevant sections based on lesson type.

### How It Works:

Your learning file is divided into sections:
```markdown
<!-- §PROFILE --> Your level, goals
<!-- §VOCAB_ACTIVE --> Recent words (last 30 days)
<!-- §VOCAB_ARCHIVE --> Mastered words
<!-- §GRAMMAR_DETAILED --> Grammar progress
<!-- §REVIEW_SCHEDULE --> Spaced repetition calendar
```

**Example - Vocabulary Lesson:**
```
✅ Loads: Profile + Active Vocab + Review Schedule
❌ Skips: Archive + Grammar + Conversations

Token savings: ~50%
```

### Benefits:

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Tokens per lesson | ~3000 | ~1200-1500 | **50-60% reduction** |
| Response time | 3-5 sec | 1-2 sec | **2x faster** |
| File with 500 words | 15,000 tokens | 2,500 tokens | **83% reduction** |

**See [docs/CONTEXT_SHARDING.md](docs/CONTEXT_SHARDING.md) for detailed documentation.**

### Tools Available:

1. **context-sharding-validator.py** - Validate section structure
2. **archive-manager.py** - Auto-archive old words

**Quick start:** [QUICKSTART_TOOLS.md](QUICKSTART_TOOLS.md)

---

## 🎯 Why This System Works

### 1. **Spaced Repetition**
Scientific research shows reviewing material at increasing intervals improves long-term retention:
- First review: 3 days (75% retention)
- Second review: 7 days (85% retention)
- Third review: 14 days (90% retention)
- Final review: 30 days (95% retention)

### 2. **Knowledge Integration**
New lessons incorporate previously learned words, creating a web of interconnected knowledge rather than isolated facts.

### 3. **Adaptive Learning**
Content automatically adjusts to your level:
- **A1-A2**: Simple vocabulary, basic grammar, lots of translations
- **B1-B2**: Balanced approach, phrasal verbs, intermediate grammar
- **C1-C2**: Sophisticated vocabulary, complex structures, nuanced explanations

### 4. **Active Recall**
Instead of passive reading, you actively retrieve information through exercises, dramatically improving memory formation.

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Ideas for Contributions

- 🌍 **Add support for more native languages** in translations
- 🎵 **Audio pronunciation** integration guides
- 🖼️ **Visual vocabulary** (image-based learning)
- 🎮 **Gamification elements** (badges, leaderboards)
- 📱 **Mobile app integration** guides
- 🤖 **Discord/Telegram bot** implementations
- 📚 **Additional lesson templates** (business English, travel, etc.)

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for detailed guidelines.

---

## 🐛 Issues & Support

If you encounter any issues or have questions:

1. Check the [Documentation](docs/)
2. Search [Existing Issues](https://github.com/yourusername/english-learning-ai/issues)
3. Open a [New Issue](https://github.com/yourusername/english-learning-ai/issues/new)

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### What This Means

✅ You can use this system for free
✅ You can modify it for your needs
✅ You can share it with others
✅ You can integrate it into your projects
✅ Commercial use is allowed

Just include the original license and copyright notice.

---

## 🌟 Acknowledgments

- Inspired by spaced repetition systems like Anki
- Built on the power of modern AI assistants (Claude, ChatGPT)
- Thanks to the language learning community for feedback

---

## ⭐ Star History

If you find this project useful, please consider giving it a star! ⭐

---

<div align="center">

**Made with ❤️ for English learners worldwide**

[Get Started](#-quick-start) • [Documentation](docs/) • [Examples](examples/) • [Contribute](#-contributing)

</div>
