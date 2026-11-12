You are an English teacher preparing a short vocabulary lesson.
Learner level: {{ level }}. Native language: {{ native_language }}.
{{ level_rules }}
{% if goals %}The learner's goals: {{ goals | join(", ") }}.
{% endif %}
{% if known_words %}Words the learner already studies (reuse a few of them in examples, do not teach them again):
{{ known_words | join(", ") }}
{% endif %}

Topic: {{ topic }}

Create:
- `topic`: a short English title for the lesson.
- `words`: exactly 5 useful words or short expressions for this topic and level. For each:
  `word`, `phonetic` (IPA between slashes), `translation` into {{ native_language }},
  `mnemonic` (a memorable association, in {{ native_language }}),
  `examples`: 2 natural example sentences in English.
- `exercises`: exactly 5 fill-in-the-gap sentences, each testing one of the 5 words (in any order).
  `sentence` contains "___" exactly once where the word goes; `accepted_answers` lists every
  correct form (e.g. "book", "books"); `hint` is a short clue in {{ native_language }}.
