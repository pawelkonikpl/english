import { z } from "zod";

export const cefrLevels = ["A1", "A2", "B1", "B2", "C1", "C2"] as const;
export const cefrLevelSchema = z.enum(cefrLevels);
export type CefrLevel = z.infer<typeof cefrLevelSchema>;

export const noContentSchema = z.undefined();

// --- core ---------------------------------------------------------------
export const appModuleSchema = z.object({
  key: z.string(),
  title: z.string(),
  icon: z.string(),
  nav_order: z.number(),
});
export type AppModuleInfo = z.infer<typeof appModuleSchema>;

// --- llm ----------------------------------------------------------------
export const modelTierSchema = z.enum(["main", "fast"]);
export type ModelTier = z.infer<typeof modelTierSchema>;

export const llmStatusSchema = z.object({
  provider: z.string(),
  available: z.boolean(),
  detail: z.string().nullable(),
  models: z.record(z.string(), z.string().nullable()),
});
export type LlmStatus = z.infer<typeof llmStatusSchema>;

export const modelInfoSchema = z.object({ id: z.string(), name: z.string(), source: z.string() });
export type ModelInfo = z.infer<typeof modelInfoSchema>;

export const modelSettingsSchema = z.object({
  provider: z.string(),
  tiers: z.array(
    z.object({
      tier: modelTierSchema,
      env_model: z.string().nullable(),
      override: z.string().nullable(),
      effective: z.string().nullable(),
    }),
  ),
});
export type ModelSettings = z.infer<typeof modelSettingsSchema>;

export const modelTestSchema = z.object({
  ok: z.boolean(),
  model: z.string().nullable(),
  latency_ms: z.number(),
  detail: z.string().nullable(),
});
export type ModelTestResult = z.infer<typeof modelTestSchema>;

// --- profile ------------------------------------------------------------
export const profileSchema = z.object({
  display_name: z.string().nullable(),
  level: cefrLevelSchema,
  target_level: cefrLevelSchema.nullable(),
  native_language: z.string(),
  goals: z.array(z.string()),
  daily_goal_xp: z.number(),
  onboarding_done: z.boolean(),
  created_at: z.string(),
});
export type Profile = z.infer<typeof profileSchema>;

// --- phrases ------------------------------------------------------------
export const phraseStatusSchema = z.enum(["new", "learning", "mastered"]);
export type PhraseStatus = z.infer<typeof phraseStatusSchema>;

export const sectionSchema = z.object({
  tier: z.string(),
  tier_title: z.string(),
  code: z.string(),
  title: z.string(),
  total: z.number(),
  learning: z.number(),
  mastered: z.number(),
});
export type Section = z.infer<typeof sectionSchema>;

export const phraseSchema = z.object({
  id: z.number(),
  tier: z.string(),
  section_code: z.string(),
  section_title: z.string(),
  english: z.string(),
  polish: z.string(),
  example: z.string().nullable(),
  note: z.string().nullable(),
  kind: z.string(),
  source: z.string(),
  status: phraseStatusSchema,
  mastery: z.number(),
  due_on: z.string().nullable(),
  has_explanation: z.boolean(),
});
export type Phrase = z.infer<typeof phraseSchema>;

export const learnSessionSchema = z.object({
  daily_limit: z.number(),
  remaining_today: z.number(),
  phrases: z.array(phraseSchema),
});
export type LearnSession = z.infer<typeof learnSessionSchema>;

export const enrollSchema = z.object({
  phrase_id: z.number(),
  review_item_id: z.number(),
  newly_enrolled: z.boolean(),
  status: phraseStatusSchema,
});

export const phraseExplanationSchema = z.object({
  meaning: z.string(),
  when_to_use: z.string(),
  examples: z.array(z.object({ english: z.string(), translation: z.string() })),
  similar: z.array(z.string()),
  tip: z.string(),
  model: z.string().nullable(),
  cached: z.boolean(),
});
export type PhraseExplanation = z.infer<typeof phraseExplanationSchema>;

// --- review -------------------------------------------------------------
export const gradeSchema = z.enum(["again", "hard", "good", "easy"]);
export type Grade = z.infer<typeof gradeSchema>;
export type ReviewMode = "recognition" | "recall" | "sentence";

export const dueItemSchema = z.object({
  id: z.number(),
  item_type: z.string(),
  item_id: z.number(),
  step: z.number(),
  mastery: z.number(),
  due_on: z.string(),
  lapses: z.number(),
  card: z.object({
    front: z.string(),
    back: z.string(),
    example: z.string().nullable(),
    note: z.string().nullable(),
    label: z.string().nullable(),
  }),
});
export type DueItem = z.infer<typeof dueItemSchema>;

export const reviewSummarySchema = z.object({ due_today: z.number(), total_reviews: z.number() });

export const gradeResultSchema = z.object({
  id: z.number(),
  step: z.number(),
  mastery: z.number(),
  interval_days: z.number(),
  due_on: z.string(),
  due_again_today: z.boolean(),
});
export type GradeResult = z.infer<typeof gradeResultSchema>;

export const recallCheckSchema = z.object({ correct: z.boolean(), expected: z.string() });

export const sentenceCheckSchema = z.object({
  correct: z.boolean(),
  uses_phrase: z.boolean(),
  corrected_sentence: z.string(),
  explanation: z.string(),
  model: z.string().nullable(),
});
export type SentenceCheck = z.infer<typeof sentenceCheckSchema>;

// --- progress -----------------------------------------------------------
export const achievementSchema = z.object({
  key: z.string(),
  title: z.string(),
  description: z.string(),
  icon: z.string(),
  unlocked_at: z.string().nullable(),
});
export type Achievement = z.infer<typeof achievementSchema>;

export const dashboardSchema = z.object({
  display_name: z.string().nullable(),
  level: z.string(),
  streak: z.object({ current: z.number(), longest: z.number(), active_today: z.boolean() }),
  xp: z.object({ today: z.number(), goal: z.number(), total: z.number() }),
  reviews_due: z.number(),
  items: z.array(
    z.object({
      item_type: z.string(),
      learning: z.number(),
      familiar: z.number(),
      mastered: z.number(),
    }),
  ),
  recommendation: z
    .object({
      target: z.string(),
      lesson_type: z.string().nullable(),
      title: z.string(),
      reason: z.string(),
    })
    .nullable(),
  new_achievements: z.array(achievementSchema),
});
export type Dashboard = z.infer<typeof dashboardSchema>;

export const dayActivitySchema = z.object({ date: z.string(), xp: z.number(), count: z.number() });
export type DayActivity = z.infer<typeof dayActivitySchema>;
