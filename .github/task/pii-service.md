# Osobny serwis PII z fabryką detektorów

## Cel

Osobny serwis HTTP (`services/pii-service/`), który wykrywa i maskuje dane osobowe (PII)
w tekście. Model detekcji wybierany jest przez fabrykę na podstawie konfiguracji,
więc zmiana modelu to zmiana jednej zmiennej środowiskowej, bez zmian w kodzie
i bez zmiany kontraktu API dla klientów.

## Research: który model

Punkt wyjścia: `openai/privacy-filter` (zgodnie z prośbą). Porównanie na benchmarku
[PIIMB](https://huggingface.co/datasets/piimb/pii-masking-benchmark-results)
(piimb 0.3.0, character-level masking F2, wyższy = lepszy):

| Model | Parametry | ai4privacy-en | ai4privacy-multi | gretel | mapa-eur-lex | nemotron | privy | **Średnia** | Polski |
|---|---|---|---|---|---|---|---|---|---|
| `bardsai/eu-pii-anonimization-multilang-v3` ¹ | 307M | 0.991 | 0.992 | 0.991 | 0.633 | 0.959 | 0.993 | **0.927** | tak (24 języki UE) |
| `OpenMed/privacy-filter-multilingual-v2` | 1.4B MoE | 0.975 | 0.970 | 0.973 | 0.373 | 0.907 | 0.818 | 0.836 | nie (16 języków bez PL) |
| `OpenMed/privacy-filter-nemotron-v2` | 1.4B MoE | 0.978 | 0.976 | 0.983 | 0.384 | 0.941 | 0.593 | 0.809 | tak |
| `fastino/gliner2-privacy-filter-PII-multi` | 205M | 0.914 | 0.904 | 0.936 | 0.545 | 0.854 | 0.646 | 0.800 | nie |
| `openai/privacy-filter` | 1.4B MoE (50M aktywnych) | 0.843 | 0.805 | 0.869 | 0.313 | 0.607 | 0.536 | 0.662 | nie („primarily English”) |

¹ Wyniki v3 podane przez autorów w karcie modelu (nieopublikowane jeszcze w zbiorze
wyników PIIMB); wyniki pozostałych modeli pochodzą bezpośrednio ze zbioru wyników PIIMB.

Zastrzeżenia: modele fine-tunowane (bardsai, OpenMed) trenowały na splitach treningowych
tych samych zbiorów, więc mają przewagę „in-distribution”; `openai/privacy-filter` jako
jedyny nie widział tych rozkładów. Mimo to przewaga jest duża, a autorzy bardsai
raportują też F1 0.980 na ręcznie oznaczonym, realnym tekście (strony WWW, PDF, maile).

**Decyzja:** domyślnie `bardsai/eu-pii-anonimization-multilang-v3`:

- najlepszy wynik na PIIMB, natywnie trenowany na polskim (użytkownicy tego projektu
  piszą po angielsku z polskimi wtrąceniami, imionami, adresami),
- 4.5× mniejszy niż `openai/privacy-filter` (307M vs 1.4B), szybki na CPU,
- standardowa architektura ModernBERT — bez `trust_remote_code`,
- licencja Apache 2.0.

`openai/privacy-filter` zostaje dostępny jako drugi backend w fabryce
(`PII_BACKEND=openai-privacy-filter`), np. gdy liczy się wykrywanie sekretów
(`secret`) albo kontekst do 128k tokenów.

## Zakres

1. Szkielet serwisu FastAPI w `services/pii-service/` (`pyproject.toml`, `app/`,
   `Dockerfile`, `.env.example`).
2. Kontrakt detektora (`PiiDetector` Protocol) i wspólny zestaw kategorii
   (`PiiCategory`: PERSON, EMAIL, PHONE, ADDRESS, LOCATION, URL, DATE,
   ACCOUNT_NUMBER, ID_NUMBER, SECRET, OTHER). Oryginalna etykieta modelu jest
   zachowana w `source_label`.
3. Fabryka `DetectorFactory` z rejestrem backendów:
   - `bardsai-eu-pii` (domyślny) — `bardsai/eu-pii-anonimization-multilang-v3`,
   - `openai-privacy-filter` — `openai/privacy-filter`,
   - `regex` — deterministyczny, bez ML (e-mail, URL, telefon, IBAN z sumą kontrolną);
     do developmentu i testów bez pobierania modeli.
4. Detektor oparty o `transformers` wspólny dla obu modeli: okna tokenów z nakładaniem
   (brak ucinania długiego tekstu), dekodowanie BIO i BIOES, rozszerzanie spanów do
   granic słów (żeby nie zostawiać fragmentów typu `Kowal[PERSON]`), przycinanie białych znaków.
   - Token z części wspólnej dwóch okien bierze predykcję z okna, w którym leży dalej
     od krawędzi (ma więcej kontekstu), a nie tę z wyższym score — inaczej nazwisko
     ucięte na granicy okna rozpadało się na dwa spany.
   - Tokeny złożone z samych białych znaków są pomijane przy dekodowaniu: nie niosą PII,
     a oznaczone jako `O` rozcinały wielowyrazowe nazwiska.
5. Endpointy:
   - `POST /api/v1/pii/detect` → lista encji (`category`, `source_label`, `start`, `end`, `text`, `score`),
   - `POST /api/v1/pii/redact` → `redacted_text` z placeholderami `[CATEGORY]` + lista encji,
   - `GET /health` → status i nazwa aktywnego backendu.
   Oba endpointy POST przyjmują opcjonalnie `categories` (filtr) i `min_score`.
6. Konfiguracja przez zmienne środowiskowe z prefiksem `PII_` (pydantic-settings),
   m.in. `PII_BACKEND`, `PII_MODEL_ID`, `PII_MODEL_REVISION`, `PII_DEVICE`, `PII_MIN_SCORE`.
7. Zależności ML (`torch`, `transformers`) jako opcjonalny extra `[ml]` — backend `regex`
   i API działają bez nich.

## Decyzje po review

1. **Dostęp:** serwis jest wewnętrzny — bez uwierzytelniania. Nie wystawiamy portu
   poza sieć wewnętrzną (odpowiedź zawiera znalezione dane osobowe).
2. **Niezależność:** serwis działa samodzielnie i nie jest dopasowany do plików nauki.
   Bez `categories` w żądaniu maskuje wszystkie kategorie, łącznie z `DATE` i `OTHER`;
   klient, który chce zachować daty, podaje `categories`.
3. **Próg pewności:** tylko globalny `PII_MIN_SCORE` (domyślnie 0.5) w konfiguracji,
   nadpisywalny per żądanie polem `min_score`. Bez progów per kategoria i bez
   konfigurowalnej listy domyślnych kategorii.
4. **Docelowe miejsce:** serwis ma żyć w `pawelkonikpl/agent-factory`, gdzie istnieje już
   pozycja backlogu (Faza 22, „Anonymise personal data before a cloud AI provider gets it”).
   Pozycja została dostosowana do tego researchu i decyzji; ten katalog zostaje jako
   implementacja referencyjna do przeniesienia, bez merge'a do `english`.

## Poza zakresem

- Testy automatyczne (krok 4 dev-flow, osobna sesja).
- Integracja z istniejącymi narzędziami w `tools/` i README serwisu (do decyzji po review).
- Backend ONNX/onnxruntime, dekoder Viterbi z pakietu `opf`, łączenie kilku detektorów,
  inne strategie anonimizacji (hash, fake data).

## Kryteria akceptacji

1. `PII_BACKEND=regex uvicorn app.main:create_app --factory` startuje bez `torch`/`transformers`.
2. `POST /api/v1/pii/redact` z tekstem `"Write to jan.kowalski@example.pl or call +48 600 123 456"`
   na backendzie `regex` zwraca `"Write to [EMAIL] or call [PHONE]"`.
3. Encje mają offsety względem oryginalnego tekstu: `text[start:end] == entity.text`.
4. Filtr `categories: ["EMAIL"]` maskuje tylko e-maile; `min_score` odrzuca encje o niższym score.
5. Nakładające się encje nie zostawiają w `redacted_text` żadnego fragmentu PII.
6. Nieznana nazwa backendu (`PII_BACKEND=foo`) zatrzymuje start z komunikatem
   wymieniającym dostępne backendy.
7. Backend ML bez zainstalowanego extra `[ml]` zatrzymuje start z komunikatem,
   jak doinstalować zależności.
8. Detektor `transformers` poprawnie składa spany z etykiet BIO (bardsai) i BIOES (OpenAI),
   a tekst dłuższy niż jedno okno modelu jest przetwarzany w całości.
9. Pusty tekst lub tekst powyżej limitu długości → `422`.
10. `GET /health` zwraca `{"status": "ok", "backend": "<nazwa>"}`.

## Pliki

- `services/pii-service/pyproject.toml`, `Dockerfile`, `.env.example`, `.dockerignore`, `.gitignore`
- `services/pii-service/app/main.py`, `config.py`, `errors.py`, `dependencies.py`
- `services/pii-service/app/api/v1/pii.py`, `app/api/health.py`
- `services/pii-service/app/schemas/pii.py`
- `services/pii-service/app/services/pii_service.py`
- `services/pii-service/app/detectors/base.py`, `factory.py`, `regex_detector.py`,
  `transformers_detector.py`, `span_decoding.py`, `label_maps.py`
