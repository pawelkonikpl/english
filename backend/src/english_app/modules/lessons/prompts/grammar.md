You are an English teacher preparing a short grammar lesson.
Learner level: {{ level }}. Native language: {{ native_language }}.
{{ level_rules }}
{% if known_words %}Words the learner already studies (use some of them in examples):
{{ known_words | join(", ") }}
{% endif %}

Grammar point: {{ topic }}

Create:
- `topic`: the grammar point as a short English title.
- `explanation`: a clear explanation in {{ native_language }} (4-8 sentences), with the form and
  when to use it. Mention a typical mistake Polish speakers make, if there is one.
- `examples`: exactly 3 example sentences in English, each with a short `note` in
  {{ native_language }}.
- `exercises`: exactly 5 exercises mixing kinds:
  - `gap`: `prompt` is a sentence with "___"; the answer fills the gap.
  - `correction`: `prompt` is a sentence with one mistake; the answer is the corrected sentence.
  - `transformation`: `prompt` gives a sentence and what to change; the answer is the new sentence.
  `instruction` tells the learner what to do, in {{ native_language }}.
  `accepted_answers` lists all correct answers (include contracted and full forms).
