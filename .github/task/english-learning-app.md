# Aplikacja do nauki angielskiego (FastAPI + SQLite + React, modułowa, z wymiennym LLM)

> Krok 1 (plan) w procesie: plan → implementacja → review → testy → weryfikacja.
> Ten plik jest źródłem prawdy dla kolejnych sesji. Poprawki po review wprowadzamy **tutaj**, zanim zmienimy kod.

---

## 1. Cel

Zamienić obecny system nauki oparty na jednym pliku markdown (`english-learning.md` wklejanym do czatu z AI) na **lokalną aplikację webową**:

- backend **FastAPI**, dane w **SQLite**,
- **modułowa** budowa: każda funkcja (frazy, powtórki, rozmowa, lekcje, dashboard) jest osobnym modułem, który można włączyć lub wyłączyć,
- **abstrakcja providera LLM**: jeden interfejs z określonymi metodami, a konkretny provider (**Claude Code**, **GitHub Copilot**) wybierany w `.env`,
- **nowoczesny, motywujący interfejs** (React), który zachęca do codziennej nauki.

Lista fraz z `resources/communication-phrases-pl.md` staje się **jednym z modułów** („Frazy do komunikacji”).

## 2. Decyzje podjęte z użytkownikiem

| Temat | Decyzja |
|---|---|
| Połączenie z LLM | **Subskrypcje przez CLI/SDK**: Claude Code przez `claude-agent-sdk`, Copilot przez `github-copilot-sdk`. Bez płacenia za tokeny API. *(Odpowiedź użytkownika brzmiała „Cło”, co interpretujemy jako „CLI”. Do potwierdzenia przy review planu.)* |
| Frontend | **React + Vite + TypeScript + Tailwind** (osobny SPA, REST do FastAPI) |
| Użytkownicy | **Jeden użytkownik, lokalnie**, bez logowania |
| Moduły w MVP | **wszystkie cztery**: Frazy + powtórki, Rozmowa z AI, Lekcje AI, Dashboard i motywacja |

## 3. Kontekst w repozytorium (stan obecny)

- `docs/SYSTEM_PROMPT.md` zawiera reguły systemu: test poziomujący (5 pytań), 6 typów lekcji, dostosowanie do poziomu A1–C2, 2 punkty za poprawną odpowiedź, powtórki po 3/7/14/30 dniach i rekomendację „co dziś”. **Te reguły przenosimy do logiki aplikacji i promptów.**
- `resources/communication-phrases-pl.md` to ok. 200 fraz w tabelach (`English | Polski`, czasem z kolumną przykładów), pogrupowanych w poziomy 1–4, sekcje 1.1–3.4 oraz „Pułapki”.
- `tools/*.py` to walidatory pliku markdown. Nie są potrzebne aplikacji i zostają bez zmian.
- W repo nie ma jeszcze żadnej aplikacji ani zależności Pythona lub Node.

## 4. Zakres

### W zakresie (MVP)
1. Szkielet backendu: konfiguracja z `.env`, SQLite + migracje, rejestr modułów, szyna zdarzeń, warstwa LLM z providerami `claude_code`, `copilot` i `fake`.
2. Moduł **phrases** (frazy do komunikacji) z danymi startowymi z pliku md.
3. Moduł **review** (powtórki SRS) wspólny dla fraz i słówek z lekcji.
4. Moduł **conversation** (rozmowa z AI w scenkach, z poprawianiem błędów).
5. Moduł **lessons** (słówka, gramatyka, swobodne pisanie, test poziomujący).
6. Moduł **progress** (dashboard, seria dni, punkty, osiągnięcia, rekomendacja).
7. Profil ucznia i onboarding przy pierwszym uruchomieniu.
8. Frontend React z modułową nawigacją i systemem komponentów.
9. Uruchamianie lokalne: tryb deweloperski (backend i Vite osobno) oraz tryb „jedna komenda” (FastAPI serwuje zbudowany frontend).

### Poza zakresem (kolejne etapy)
- wielu użytkowników i logowanie, wdrożenie na serwer,
- providery oparte na kluczach API (Anthropic API, GitHub Models). Abstrakcja ma je umożliwiać, ale nie implementujemy ich teraz,
- rozpoznawanie mowy (STT) i ocena wymowy. W MVP jest tylko TTS z przeglądarki (Web Speech API, bez backendu),
- aplikacja mobilna i PWA offline,
- import i eksport starego pliku `english-learning.md` (pomysł na później).

## 5. Architektura

### 5.1 Struktura katalogów

```
backend/
  pyproject.toml
  alembic.ini
  migrations/
  src/english_app/
    __main__.py              # uruchomienie: python -m english_app (uvicorn)
    main.py                  # create_app(): ładuje włączone moduły, montuje routery, serwuje frontend/dist
    core/
      config.py              # Settings (pydantic-settings) czytane z .env
      db.py                  # silnik SQLModel, zależność get_session
      modules.py             # AppModule (Protocol) + rejestr modułów
      events.py              # prosta szyna zdarzeń w procesie (publish/subscribe)
      clock.py               # wstrzykiwalny zegar (testy SRS i serii dni)
      errors.py              # mapowanie wyjątków domenowych i LLM na odpowiedzi HTTP
    llm/
      base.py                # LLMProvider (ABC), ChatMessage, ProviderStatus, wyjątki
      factory.py             # rejestr providerów + get_llm_provider() na podstawie LLM_PROVIDER
      json_utils.py          # walidacja i naprawa JSON względem modelu Pydantic (fallback)
      providers/
        claude_code.py       # claude-agent-sdk
        copilot.py           # github-copilot-sdk
        fake.py              # deterministyczny, do testów i pracy offline
    modules/
      profile/               # profil ucznia, onboarding
      phrases/               # frazy do komunikacji (+ seed/communication_phrases.json)
      review/                # SRS: kolejka, ocena, harmonogram
      conversation/          # scenki z AI (+ seed/scenarios.json, prompts/)
      lessons/               # lekcje AI (+ prompts/)
      progress/              # dashboard, seria dni, punkty, osiągnięcia
      # każdy moduł: models.py, schemas.py, service.py, router.py, module.py, prompts/ (opcjonalnie)
  tests/
frontend/
  package.json, vite.config.ts, tsconfig.json, index.html
  src/
    app/                     # router, layout, provider-y (QueryClient, motyw)
    shared/                  # klient API, komponenty UI, hooki, i18n (PL)
    modules/
      dashboard/ phrases/ review/ conversation/ lessons/ profile/
      index.ts               # rejestr modułów frontendu (trasy + pozycje menu)
data/                        # english.db (w .gitignore)
.env.example
```

Kod, nazwy, komentarze i commity piszemy **po angielsku**. Teksty w interfejsie są **po polsku**, z prostym słownikiem i18n, żeby dało się dodać inne języki.

### 5.2 Modułowość (backend)

```python
class AppModule(Protocol):
    key: str                                   # "phrases", "review", ...
    title: str                                 # nazwa wyświetlana w UI (PL)
    router: APIRouter                          # montowany pod /api/<key>
    depends_on: tuple[str, ...]                # np. conversation -> ("profile",)
    def register_events(self, bus: EventBus) -> None: ...
    async def on_startup(self, session: Session) -> None: ...   # np. seed danych
```

- `ENABLED_MODULES` w `.env` decyduje, które moduły są ładowane. Jeśli moduł ma niespełnioną zależność, aplikacja **nie startuje** i podaje czytelny błąd.
- Moduły **nie importują** swoich wnętrz nawzajem. Komunikują się:
  - przez **zdarzenia** (`events.py`), np. `ActivityRecorded(kind, points, ref)`, `ReviewGraded(item_id, grade)`, `LessonCompleted(...)`, `ConversationFinished(...)`; moduł `progress` je subskrybuje,
  - przez **publiczny serwis** modułu `review` (`ReviewService.enroll(item_type, item_id)`), który rejestruje pozycję w powtórkach.
- `GET /api/modules` zwraca listę włączonych modułów. Frontend pokazuje tylko te moduły.

### 5.3 Warstwa LLM: abstrakcja providera

To jest centralny element prośby użytkownika. Interfejs w `llm/base.py`:

```python
@dataclass(frozen=True)
class ChatMessage:
    role: Literal["user", "assistant"]
    content: str

@dataclass(frozen=True)
class ProviderStatus:
    provider: str            # "claude_code" | "copilot" | "fake"
    model: str | None
    available: bool          # CLI/runtime dostępne i zalogowane
    detail: str | None       # komunikat dla użytkownika, gdy niedostępne

class LLMProvider(ABC):
    name: ClassVar[str]

    @abstractmethod
    async def complete(self, *, system: str, messages: Sequence[ChatMessage]) -> str:
        """Zwykła odpowiedź tekstowa (rozmowa, wyjaśnienia)."""

    @abstractmethod
    async def complete_structured(
        self, *, system: str, messages: Sequence[ChatMessage], schema: type[T]
    ) -> T:
        """Odpowiedź zgodna ze schematem Pydantic (lekcje, poprawki, oceny)."""

    async def stream(self, *, system: str, messages: Sequence[ChatMessage]) -> AsyncIterator[str]:
        """Domyślnie: jeden fragment z complete(). Provider może nadpisać prawdziwym streamingiem."""

    @abstractmethod
    async def status(self) -> ProviderStatus:
        """Sprawdzenie dostępności (do /api/llm/status i ekranu ustawień)."""

    async def aclose(self) -> None:
        """Zwolnienie zasobów (np. zamknięcie klienta Copilot) przy wyłączaniu aplikacji."""
```

Wyjątki: `LLMError` jako baza, a pod nią `LLMUnavailableError` (brak CLI lub logowania → HTTP 503), `LLMTimeoutError` (→ 504) i `LLMOutputError` (niepoprawny JSON po ponowieniu → 502). Każdy z tych błędów UI pokazuje jako przyjazny komunikat z instrukcją.

**Zasady wspólne dla providerów:**
- **Aplikacja jest źródłem prawdy o historii rozmowy.** Każde wywołanie dostaje pełną historię (`messages`), a provider sam decyduje, jak ją przekazać (np. jako transkrypt w promptcie). Providery są bezstanowe, więc podmiana providera w `.env` nie psuje istniejących rozmów.
- **Bez narzędzi i bez dostępu do plików.** Oba SDK to agenci z dostępem do powłoki i plików, a tutaj używamy ich wyłącznie jako modeli językowych:
  - Claude: `ClaudeAgentOptions(tools=[], setting_sources=[], max_turns=1, cwd=<pusty katalog tymczasowy>)`,
  - Copilot: `create_session(available_tools=[], on_permission_request=<odmowa wszystkiego>)` i również pusty katalog roboczy.
- `complete_structured`: najpierw natywny tryb strukturalny SDK, a gdy go brakuje lub zawiedzie, parsowanie JSON z tekstu (`json_utils.py`), walidacja Pydantic i **jedno** ponowienie z informacją o błędzie walidacji.
- Limit czasu z `LLM_TIMEOUT_SECONDS` (domyślnie 90 s).
- Logowanie: czas wywołania, provider, model, sukces lub błąd. **Bez treści wiadomości** w logach.

**Provider `claude_code`** (`claude-agent-sdk`, zweryfikowana wersja 0.2.180, CLI dołączone do paczki):
- wywołanie: `query(prompt=..., options=ClaudeAgentOptions(system_prompt=system, model=LLM_MODEL or None, tools=[], max_turns=1, setting_sources=[], cwd=...))`; wynik z `ResultMessage.result`,
- tryb strukturalny: `output_format={"type": "json_schema", "schema": schema.model_json_schema()}`, wynik w `ResultMessage.structured_output`,
- `ResultMessage.is_error` lub brak wyniku → `LLMError`; błąd uruchomienia CLI lub brak logowania → `LLMUnavailableError`,
- uwierzytelnienie: zalogowany Claude Code na maszynie (subskrypcja). Jeśli ustawiono `ANTHROPIC_API_KEY`, SDK użyje klucza; aplikacja tego nie wymaga.

**Provider `copilot`** (`github-copilot-sdk`, zweryfikowana wersja 1.0.31, wymaga Pythona ≥ 3.11):
- jeden `CopilotClient` na cały czas życia aplikacji (start w `lifespan`, zamknięcie w `aclose`),
- na każde wywołanie nowa sesja: `create_session(model=LLM_MODEL, system_message={"mode": "replace", "content": system}, available_tools=[], on_permission_request=...)`, potem `send_and_wait(prompt, timeout=...)`,
- tryb strukturalny: `send_and_wait(..., response_schema=schema)` lub `send_and_wait_typed(prompt, response_type=schema)`,
- uwierzytelnienie: zalogowany użytkownik GitHub CLI lub Copilot albo token w `COPILOT_GITHUB_TOKEN` / `GH_TOKEN` / `GITHUB_TOKEN` (SDK czyta je sam),
- runtime pobierany przez `python -m copilot download-runtime` (opisać w README).

**Provider `fake`:** deterministyczne odpowiedzi zgodne ze schematami (np. stała odpowiedź rozmówcy i przykładowa lekcja). Służy do testów, pracy bez internetu i demonstracji UI. W testach **żaden test nie woła prawdziwego LLM**.

**Rejestr:** `PROVIDERS = {"claude_code": ClaudeCodeProvider, "copilot": CopilotProvider, "fake": FakeProvider}`. Nowy provider (np. API Anthropic w przyszłości) to nowa klasa i jeden wpis w słowniku. Nieznana wartość `LLM_PROVIDER` przerywa start i wypisuje dostępne opcje.

### 5.4 Konfiguracja (`.env`, plik `.env.example` w repo)

```dotenv
# LLM
LLM_PROVIDER=claude_code        # claude_code | copilot | fake
LLM_MODEL=                      # opcjonalnie; puste = domyślny model providera (np. claude-opus-5-5 dla claude_code)
LLM_TIMEOUT_SECONDS=90
CLAUDE_CODE_CLI_PATH=           # opcjonalnie, własna ścieżka do CLI claude
# Copilot: COPILOT_CLI_PATH / COPILOT_GITHUB_TOKEN są czytane bezpośrednio przez SDK

# App
DATABASE_URL=sqlite:///./data/english.db
ENABLED_MODULES=profile,phrases,review,conversation,lessons,progress
APP_TIMEZONE=Europe/Warsaw      # liczenie serii dni i „dzisiejszych” powtórek
DAILY_NEW_PHRASES=10
HOST=127.0.0.1
PORT=8000
```

### 5.5 Model danych (SQLite, SQLModel + Alembic)

| Tabela | Najważniejsze pola | Uwagi |
|---|---|---|
| `learner_profile` | id (=1), display_name, level (A1–C2), target_level, native_language, goals (JSON), daily_goal_xp, onboarding_done, created_at | jeden wiersz |
| `phrase` | id, tier (1–4 lub `pitfalls`), section_code (np. `1.1`), section_title, english, polish, example, note, kind (`phrase`, `phrasal_verb`, `word`, `false_friend`, `common_error`), source (`seed`, `ai`, `user`), ai_explanation (JSON, cache) | unikalność (section_code, english) |
| `review_item` | id, item_type (`phrase`, `lesson_word`), item_id, step, ease, interval_days, due_on (date), mastery (0–3), lapses, last_reviewed_at, created_at | stan SRS oddzielony od treści |
| `review_log` | id, review_item_id, grade (`again`, `hard`, `good`, `easy`), mode, reviewed_at | historia do statystyk |
| `lesson` | id, type (`vocabulary`, `grammar`, `writing`, `placement`), topic, level, content (JSON z LLM), status, score, max_score, created_at, completed_at | |
| `lesson_answer` | id, lesson_id, exercise_index, answer, is_correct, feedback (JSON) | |
| `lesson_word` | id, lesson_id, word, phonetic, translation, mnemonic, examples (JSON) | wpisywane do SRS |
| `conversation` | id, scenario_key, title, level, status, target_phrase_ids (JSON), score, summary (JSON), started_at, finished_at | |
| `conversation_message` | id, conversation_id, role, content, feedback (JSON: poprawki i sugestie), created_at | |
| `activity` | id, kind, points, ref_type, ref_id, occurred_at | źródło serii dni, punktów i wykresu |
| `achievement_unlock` | id, achievement_key, unlocked_at | |

Migracje Alembic od pierwszej wersji. Plik bazy tworzy się automatycznie przy pierwszym starcie.

### 5.6 Algorytm powtórek (moduł `review`)

Deterministyczny, zgodny z dotychczasowym systemem (3/7/14/30 dni):
- drabina interwałów: `[1, 3, 7, 14, 30, 60, 120]` dni,
- `good`: o jeden stopień w górę; `easy`: o dwa stopnie; `hard`: ten sam interwał (minimum 1 dzień); `again`: powrót na stopień 0, `lapses += 1` i pozycja wraca jeszcze w tej samej sesji,
- `mastery`: 0 = nowe, 1 = stopnie 0–1, 2 = stopnie 2–3, 3 = stopień ≥ 4 (interwał ≥ 30 dni, czyli „opanowane ⭐⭐⭐”),
- „dzisiaj” liczone w strefie `APP_TIMEZONE`; zegar wstrzykiwany (`core/clock.py`).

### 5.7 Moduły: zachowanie

**profile:** pierwsze uruchomienie (gdy `onboarding_done = false`) przekierowuje na onboarding. Kroki: imię (opcjonalne), język ojczysty (domyślnie polski), cele (wielokrotny wybór), dzienny cel XP, a potem **test poziomujący** (z modułu lessons) albo samoocena A1–C2.

**phrases (Frazy do komunikacji):**
- dane startowe: `modules/phrases/seed/communication_phrases.json`, wygenerowane **jednorazowo** skryptem z tabel w `resources/communication-phrases-pl.md`. Skrypt `backend/scripts/build_phrases_seed.py` zostaje w repo, żeby dało się odświeżyć dane po zmianie md. Seed wykonuje się idempotentnie przy starcie,
- przegląd poziomów i sekcji z paskiem postępu (ile fraz w nauce lub opanowanych),
- **sesja „Ucz się nowych”**: do `DAILY_NEW_PHRASES` fraz dziennie, w kolejności poziomów. Karta pokazuje EN, PL, przykład, uwagę i przycisk 🔊 (TTS z przeglądarki). Do wyboru „Znam to” (wpis do SRS od razu na stopniu 2) albo „Uczę się” (wpis do SRS na stopniu 0),
- „🤖 Wyjaśnij / więcej przykładów” przy frazie: wywołanie LLM, wynik zapisany w `ai_explanation`, więc kolejne otwarcie nie woła LLM,
- „💬 Przećwicz w rozmowie” przy sekcji: start rozmowy (moduł conversation) z frazami z sekcji jako `target_phrase_ids`.

**review (Powtórki):**
- wspólna kolejka zaległych pozycji (frazy i słówka z lekcji), sortowana po `due_on`,
- tryby kart: **rozpoznawanie** (EN → odwróć → PL), **przypominanie** (PL → wpisz EN; dopasowanie tolerancyjne: wielkość liter, interpunkcja, drobne literówki według odległości Levenshteina ≤ 1 dla słów > 4 znaków), **użyj w zdaniu** (ocena LLM: `{correct, corrected_sentence, explanation_pl}`),
- ocena czterema przyciskami (`Again`, `Hard`, `Good`, `Easy`), skróty klawiszowe (spacja: odwróć; 1–4: ocena),
- podsumowanie sesji: ile pozycji, ile poprawnych, zdobyte XP.

**conversation (Rozmowa z AI):**
- katalog scenek w `seed/scenarios.json`: kawiarnia, small talk, spotkanie online w pracy, u lekarza, hotel, pytanie o drogę, rozmowa o pracę oraz „Temat dowolny”,
- start: AI wypowiada pierwszą kwestię zgodnie ze scenką i poziomem z profilu (reguły A1–C2 z `SYSTEM_PROMPT.md`),
- każda wiadomość użytkownika daje odpowiedź strukturalną: `{reply, corrections: [{original, corrected, explanation_pl}], better_alternatives: [..], used_target_phrases: [..]}`. UI pokazuje odpowiedź rozmówcy, a pod wiadomością użytkownika dyskretne „💡 poprawki”,
- przycisk **„Podpowiedź”**: 3 propozycje odpowiedzi na różnym poziomie trudności,
- **„Zakończ”**: podsumowanie `{score_0_10, strengths, mistakes, new_phrases: [{english, polish}]}`; nowe frazy można dodać do powtórek jednym kliknięciem (jako `phrase` z `source = ai`),
- wskaźnik „pisze…” na czas oczekiwania. Streaming (SSE) jest opcjonalny w MVP; endpoint zwraca całą odpowiedź.

**lessons (Lekcje AI)**, zgodnie z formatami z `docs/SYSTEM_PROMPT.md`:
- **słówka**: 5 słów (wymowa, tłumaczenie, technika zapamiętywania, 2 przykłady) i 5 zdań z lukami. Słowa trafiają do `lesson_word` i do SRS,
- **gramatyka**: temat dobrany do poziomu (listy tematów z `TEMPLATE.md`), wyjaśnienie, 3 przykłady i 5 ćwiczeń (luka, poprawianie, przekształcanie),
- **swobodne pisanie**: temat, tekst użytkownika i ocena `{score_0_10, errors: [{fragment, correction, explanation_pl}], corrected_text, strengths}`,
- **test poziomujący**: 5 pytań z `SYSTEM_PROMPT.md` (samoocena, tłumaczenie, poprawianie błędu, cele, język) i wynik w postaci poziomu zapisanego w profilu,
- ocena ćwiczeń zamkniętych **deterministyczna** (lista akceptowanych odpowiedzi z LLM, normalizacja tekstu), ocena otwartych przez LLM. **2 punkty za poprawną odpowiedź.**

**progress (Dashboard i motywacja):**
- **seria dni**: liczba kolejnych dni z co najmniej jedną aktywnością, liczona w strefie `APP_TIMEZONE`; dzisiejszy dzień bez aktywności nie przerywa serii do północy,
- **XP**: powtórka `good` lub `easy` = 1, `hard` = 0,5 (zaokrąglane w dół przy sumowaniu dnia), poprawna odpowiedź w lekcji = 2, zakończona rozmowa = wynik 0–10, nowa fraza = 1. Dzienny cel XP widoczny jako pierścień postępu,
- **statystyki**: frazy w nauce i opanowane (ogółem i na poziom), zaległe powtórki dziś, wykres aktywności z 12 tygodni (heatmapa),
- **rekomendacja „Co dziś?”** (reguły z `SYSTEM_PROMPT.md`): są zaległe powtórki → powtórki; ostatnia lekcja to słówka → gramatyka; ostatnia to gramatyka → słówka; brak aktywności od 2+ dni → powtórki; 3+ lekcje tego samego typu z rzędu → inny typ; brak nowych fraz dziś → frazy,
- **osiągnięcia** (definicje w kodzie): pierwsza lekcja, 10/50/100/200 fraz, seria 3/7/30 dni, pierwsza rozmowa, ukończony Poziom 1 fraz (wszystkie frazy z sekcji 1.x mają mastery ≥ 1), 100 powtórek. Odblokowanie wywołuje animację w UI.

### 5.8 API (prefiks `/api`)

| Metoda i ścieżka | Opis |
|---|---|
| `GET /health` | status aplikacji |
| `GET /modules` | włączone moduły (klucz, tytuł) |
| `GET /llm/status` | `ProviderStatus` |
| `GET /profile`, `PUT /profile` | profil ucznia |
| `GET /phrases/sections` | poziomy i sekcje z liczbami (wszystkie, w nauce, opanowane) |
| `GET /phrases?section=&status=` | lista fraz ze stanem SRS |
| `GET /phrases/learn-session` | następne nowe frazy do nauki dziś (z uwzględnieniem limitu) |
| `POST /phrases/{id}/enroll` | `{known: bool}`: wpis do SRS |
| `POST /phrases/{id}/explain` | wyjaśnienie AI (cache w bazie) |
| `GET /review/due?limit=` | zaległe pozycje z treścią do kart |
| `POST /review/items/{id}/grade` | `{grade, mode}` → nowy stan SRS i zdobyte XP |
| `POST /review/items/{id}/check-sentence` | `{sentence}` → ocena LLM |
| `GET /conversation/scenarios` | katalog scenek |
| `POST /conversation` | `{scenario_key, target_phrase_ids?}` → rozmowa z pierwszą kwestią AI |
| `GET /conversation/{id}` | rozmowa z wiadomościami |
| `POST /conversation/{id}/messages` | `{content}` → odpowiedź AI i poprawki |
| `POST /conversation/{id}/hint` | 3 propozycje odpowiedzi |
| `POST /conversation/{id}/finish` | podsumowanie i wynik |
| `POST /lessons` | `{type, topic?}` → wygenerowana lekcja |
| `GET /lessons`, `GET /lessons/{id}` | historia i szczegóły |
| `POST /lessons/{id}/answers` | odpowiedź na ćwiczenie → ocena |
| `POST /lessons/{id}/complete` | zakończenie, punkty, zapis słówek do SRS |
| `GET /progress/dashboard` | dane dashboardu (seria, XP dziś i cel, statystyki, rekomendacja) |
| `GET /progress/activity?days=` | dane heatmapy |
| `GET /progress/achievements` | lista osiągnięć z datami odblokowania |

Błędy mają jednolity format `{error: {code, message}}`, gdzie `message` jest po polsku i gotowy do pokazania w UI.

### 5.9 Prompty

- Szablony w `modules/<moduł>/prompts/*.md` (Jinja2), osobno od kodu, żeby dało się je łatwo dopracowywać.
- Treść promptów po angielsku, z poleceniem, żeby **wyjaśnienia dla ucznia były w jego języku ojczystym** (z profilu).
- Każdy prompt dostaje poziom ucznia i ostatnie słówka lub frazy (zasada „knowledge integration” z `SYSTEM_PROMPT.md`: przykłady wykorzystują już poznane słowa).

### 5.10 Frontend

- **Stos:** React + TypeScript + Vite, Tailwind CSS, komponenty w stylu shadcn/ui (Radix), animacje `motion` (Framer Motion), TanStack Query (dane i cache), React Router, ikony `lucide-react`, `canvas-confetti` (świętowanie), Recharts (wykres i heatmapa).
- **Modułowość:** `src/modules/<moduł>/` eksportuje trasy i pozycję menu; `src/modules/index.ts` je rejestruje, a menu pokazuje tylko moduły zwrócone przez `GET /api/modules`.
- **Wygląd, który zachęca do nauki:**
  - jasny i ciemny motyw (domyślnie według systemu), wyrazisty gradientowy akcent, duże zaokrąglone karty, czytelna typografia (np. Inter),
  - **dashboard**: płomień serii dni, pierścień dziennego celu XP, duży przycisk „Co dziś?” z rekomendacją, kafelki modułów z postępem, heatmapa aktywności,
  - **mikrointerakcje**: animacja odwracania karty, „+XP” wyskakujące po odpowiedzi, konfetti przy celu dnia i osiągnięciu, płynne przejścia między ekranami,
  - **rozmowa**: interfejs jak w komunikatorze, wskaźnik „pisze…”, poprawki rozwijane pod wiadomością, przycisk podpowiedzi,
  - responsywność od telefonu po desktop; obsługa klawiatury; szanowanie `prefers-reduced-motion`; widoczne stany fokusu,
  - **stany błędów LLM**: gdy provider jest niedostępny, baner z instrukcją (np. „Zaloguj się w Claude Code: `claude login`”), a moduły bez LLM (frazy, powtórki z oceną własną, dashboard) **działają dalej**.
- Vite proxy `/api` → `http://127.0.0.1:8000` w trybie deweloperskim.

### 5.11 Uruchamianie

- **Tryb deweloperski:** `make dev` (lub dwa polecenia opisane w README) uruchamia `uvicorn` z przeładowaniem oraz `npm run dev`.
- **Tryb „jedna komenda”:** `npm run build` w `frontend/`, potem `python -m english_app`. FastAPI serwuje `frontend/dist` pod `/`, z fallbackiem SPA do `index.html`, a API pod `/api`.
- Zależności Pythona w `backend/pyproject.toml` (fastapi, uvicorn, sqlmodel, alembic, pydantic-settings, jinja2, claude-agent-sdk, github-copilot-sdk); dev: pytest, httpx, ruff. Python ≥ 3.11 (wymóg `github-copilot-sdk`).
- README: sekcja „Aplikacja” z instalacją, konfiguracją `.env`, logowaniem do Claude Code lub Copilot i uruchomieniem.

## 6. Etapy implementacji (kolejne sesje kroku 2)

Każdy etap kończy się działającą aplikacją i osobnym commitem.

| Etap | Zakres | Wynik |
|---|---|---|
| A | Szkielet backendu: `core/*`, migracje, rejestr modułów, szyna zdarzeń, `llm/*` z 3 providerami, `/health`, `/modules`, `/llm/status`, `.env.example` | `python -m english_app` startuje; `/api/llm/status` raportuje stan providera |
| B | Moduły `profile`, `phrases` (+ skrypt i seed), `review` | API fraz i powtórek działa na providerze `fake` |
| C | Moduł `progress` (zdarzenia, XP, seria, osiągnięcia, rekomendacja) | dashboard API zwraca poprawne dane |
| D | Frontend: szkielet, system komponentów, motyw, onboarding, dashboard, frazy, powtórki | pełny przepływ „nauka nowych fraz → powtórka → XP na dashboardzie” w przeglądarce |
| E | Moduł `conversation` (backend + frontend) | rozmowa w scence z poprawkami i podsumowaniem |
| F | Moduł `lessons` (4 typy) + test poziomujący w onboardingu (backend + frontend) | lekcje generowane, oceniane i zapisywane |
| G | Tryb „jedna komenda”, README, porządki | aplikacja uruchamia się jedną komendą zgodnie z README |

## 7. Kryteria akceptacji

### Konfiguracja i LLM
- [ ] Zmiana `LLM_PROVIDER` w `.env` między `claude_code`, `copilot` i `fake` (i restart) przełącza providera **bez zmian w kodzie**. `GET /api/llm/status` pokazuje aktywnego providera i model.
- [ ] Nieznana wartość `LLM_PROVIDER` zatrzymuje start z komunikatem wymieniającym dostępne providery.
- [ ] Wszystkie moduły korzystają z LLM **wyłącznie** przez interfejs `LLMProvider` (żaden moduł nie importuje `claude_agent_sdk` ani `copilot`).
- [ ] Oba prawdziwe providery uruchamiają model **bez narzędzi**: Claude z `tools=[]`, Copilot z `available_tools=[]` i odmową uprawnień, oba w pustym katalogu roboczym. Po rozmowie z AI w katalogu projektu nie przybywa żadnych plików.
- [ ] Gdy CLI nie jest zainstalowane lub zalogowane, endpointy LLM zwracają 503 z polskim komunikatem i instrukcją, a frazy, powtórki z oceną własną i dashboard działają dalej.
- [ ] `complete_structured` zwraca obiekt zgodny ze schematem; przy niepoprawnym JSON wykonuje dokładnie jedno ponowienie, a potem zwraca 502.
- [ ] Logi nie zawierają treści wiadomości użytkownika ani odpowiedzi modelu.

### Modułowość
- [ ] Usunięcie modułu z `ENABLED_MODULES` (np. `lessons`) ukrywa go w API (404 dla jego tras) i w menu frontendu, a reszta działa.
- [ ] Włączenie modułu bez jego zależności (np. `conversation` bez `profile`) zatrzymuje start z czytelnym błędem.

### Frazy i powtórki
- [ ] Po pierwszym starcie w bazie jest tyle fraz, ile wierszy w tabelach `resources/communication-phrases-pl.md` (sekcje 1.1–3.3 i „Pułapki”). Ponowny start nie tworzy duplikatów.
- [ ] Sesja „Ucz się nowych” proponuje frazy w kolejności poziomów i nie przekracza `DAILY_NEW_PHRASES` dziennie.
- [ ] Oceny SRS dają interwały zgodne z drabiną z sekcji 5.6, np. nowa pozycja oceniona `good` trzy razy z rzędu ma interwał 7 dni, a `again` przywraca stopień 0.
- [ ] Wyjaśnienie AI frazy przy drugim otwarciu nie wywołuje LLM (cache).
- [ ] Skróty klawiszowe w powtórkach działają (spacja, 1–4).

### Rozmowa
- [ ] Rozmowę można rozpocząć z każdej scenki; pierwsza kwestia AI pasuje do scenki.
- [ ] Każda odpowiedź zawiera listę poprawek (może być pusta), widoczną pod wiadomością użytkownika.
- [ ] Historia rozmowy zostaje zapisana; po odświeżeniu strony rozmowę można kontynuować.
- [ ] Po zakończeniu widać wynik 0–10 i nowe frazy, które jednym kliknięciem trafiają do powtórek.

### Lekcje
- [ ] Każdy z 4 typów lekcji generuje się, można odpowiedzieć na ćwiczenia, a wynik jest liczony po 2 punkty za poprawną odpowiedź.
- [ ] Słówka z ukończonej lekcji słownictwa pojawiają się w kolejce powtórek.
- [ ] Test poziomujący ustawia poziom w profilu, a kolejne lekcje są generowane dla tego poziomu.

### Dashboard i motywacja
- [ ] Seria dni rośnie po aktywności w kolejnych dniach (strefa `APP_TIMEZONE`) i zeruje się po pełnym dniu bez aktywności.
- [ ] XP dzisiaj, cel dzienny, liczba zaległych powtórek i rekomendacja „Co dziś?” odpowiadają regułom z sekcji 5.7.
- [ ] Odblokowanie osiągnięcia zapisuje je raz (bez duplikatów) i pokazuje animację w UI.

### Interfejs i uruchamianie
- [ ] Onboarding pojawia się tylko przy pierwszym uruchomieniu.
- [ ] Aplikacja jest używalna na szerokości 375 px (telefon) i na desktopie, w jasnym i ciemnym motywie.
- [ ] Przy `prefers-reduced-motion` animacje są wyłączone lub ograniczone.
- [ ] `python -m english_app` po zbudowaniu frontendu serwuje całą aplikację pod `http://127.0.0.1:8000`.
- [ ] README opisuje instalację, konfigurację `.env`, logowanie do providerów i uruchomienie; `.env.example` zawiera wszystkie zmienne z sekcji 5.4.

## 8. Ryzyka i otwarte kwestie

1. **Interpretacja „Cło”** jako CLI/SDK (subskrypcje) wymaga potwierdzenia przy review. Jeśli chodziło o coś innego, zmieniamy sekcję 5.3 przed etapem A.
2. **Opóźnienia:** każde wywołanie uruchamia proces CLI (Claude) lub sesję (Copilot), więc odpowiedź może trwać kilka sekund. UI musi pokazywać stan oczekiwania. Optymalizacja (utrzymywanie sesji per rozmowa) dopiero w razie potrzeby.
3. **Warunki subskrypcji:** przed etapem A sprawdzić aktualne zasady korzystania z subskrypcji Claude przez Agent SDK oraz limity „premium requests” w Copilot (koszt i limity są po stronie użytkownika).
4. **Zmienność SDK:** oba SDK szybko się rozwijają (wersje 0.2.x i 1.0.x). Przypinamy wersje w `pyproject.toml`; kod SDK zamykamy w jednym pliku providera.
5. **Jakość JSON z modelu:** ryzyko ogranicza tryb strukturalny SDK, walidacja Pydantic i jedno ponowienie.
6. **Push do GitHub:** obecna sesja nie ma uprawnień do zapisu w `pawelkonikpl/english` (błąd 403). Commity czekają lokalnie do czasu podłączenia GitHub.

## 9. Następne kroki (proces)

1. **Review planu (użytkownik):** sprawdzić decyzje (sekcja 2), zakres MVP i kryteria. Poprawki wprowadzamy w tym pliku.
2. **Krok 2, implementacja etapami A–G:** nowa sesja zaczyna od „zaimplementuj etap A z `.github/task/english-learning-app.md`”.
3. **Krok 4, testy:** pytest (SRS, seria dni, rekomendacja, seed, API na providerze `fake`, rejestr modułów i providerów) oraz testy komponentów frontendu dla kluczowych ekranów.
4. **Krok 5, weryfikacja:** checklista przed scaleniem na podstawie tego pliku.
