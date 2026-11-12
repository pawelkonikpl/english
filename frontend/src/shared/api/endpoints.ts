import { z } from "zod";

import { json, request } from "./client";
import {
  lessonListItemSchema,
  lessonSchema,
  placementQuestionsSchema,
  placementResultSchema,
  type CefrLevel,
  type LessonType,
  addPhraseSchema,
  appModuleSchema,
  conversationListItemSchema,
  conversationSchema,
  hintListSchema,
  scenarioSchema,
  sendMessageSchema,
  dashboardSchema,
  dayActivitySchema,
  dueItemSchema,
  enrollSchema,
  gradeResultSchema,
  learnSessionSchema,
  llmStatusSchema,
  modelInfoSchema,
  modelSettingsSchema,
  modelTestSchema,
  noContentSchema,
  phraseExplanationSchema,
  phraseSchema,
  profileSchema,
  recallCheckSchema,
  reviewSummarySchema,
  achievementSchema,
  sectionSchema,
  sentenceCheckSchema,
  type Grade,
  type ModelTier,
  type PhraseStatus,
  type Profile,
  type ReviewMode,
} from "./schemas";

const post = (body: unknown): RequestInit => ({ method: "POST", ...json(body) });
const put = (body: unknown): RequestInit => ({ method: "PUT", ...json(body) });

export const queryKeys = {
  modules: ["modules"] as const,
  llmStatus: ["llm", "status"] as const,
  llmModels: ["llm", "models"] as const,
  llmSettings: ["llm", "settings"] as const,
  profile: ["profile"] as const,
  dashboard: ["progress", "dashboard"] as const,
  activity: (days: number) => ["progress", "activity", days] as const,
  achievements: ["progress", "achievements"] as const,
  sections: ["phrases", "sections"] as const,
  phrases: (section?: string, status?: PhraseStatus) => ["phrases", "list", section, status] as const,
  learnSession: ["phrases", "learn-session"] as const,
  explanation: (id: number) => ["phrases", "explanation", id] as const,
  reviewDue: ["review", "due"] as const,
  reviewSummary: ["review", "summary"] as const,
  scenarios: ["conversation", "scenarios"] as const,
  conversations: ["conversation", "list"] as const,
  conversation: (id: number) => ["conversation", "detail", id] as const,
  lessons: ["lessons", "list"] as const,
  lesson: (id: number) => ["lessons", "detail", id] as const,
  placement: (level: CefrLevel) => ["lessons", "placement", level] as const,
};

export type ModelSettingsUpdate = Partial<Record<ModelTier, string | null>> & {
  allow_custom?: boolean;
};

export const api = {
  modules: () => request("/modules", z.array(appModuleSchema)),

  llmStatus: () => request("/llm/status", llmStatusSchema),
  llmModels: () => request("/llm/models", z.array(modelInfoSchema)),
  llmSettings: () => request("/llm/settings", modelSettingsSchema),
  updateLlmSettings: (update: ModelSettingsUpdate) =>
    request("/llm/settings", modelSettingsSchema, put(update)),
  testModel: (target: { tier: ModelTier } | { model: string }) =>
    request("/llm/test", modelTestSchema, post(target)),

  profile: () => request("/profile", profileSchema),
  updateProfile: (update: Partial<Omit<Profile, "created_at">>) =>
    request("/profile", profileSchema, put(update)),

  dashboard: () => request("/progress/dashboard", dashboardSchema),
  activity: (days: number) => request(`/progress/activity?days=${days}`, z.array(dayActivitySchema)),
  achievements: () => request("/progress/achievements", z.array(achievementSchema)),
  markAchievementsSeen: () =>
    request("/progress/achievements/seen", noContentSchema, { method: "POST" }),

  sections: () => request("/phrases/sections", z.array(sectionSchema)),
  phrases: (section?: string, status?: PhraseStatus) => {
    const params = new URLSearchParams();
    if (section) params.set("section", section);
    if (status) params.set("status", status);
    const query = params.size ? `?${params.toString()}` : "";
    return request(`/phrases${query}`, z.array(phraseSchema));
  },
  learnSession: () => request("/phrases/learn-session", learnSessionSchema),
  enrollPhrase: (id: number, known: boolean) =>
    request(`/phrases/${id}/enroll`, enrollSchema, post({ known })),
  explainPhrase: (id: number, regenerate = false) =>
    request(`/phrases/${id}/explain`, phraseExplanationSchema, post({ regenerate })),

  reviewDue: (limit = 50) => request(`/review/due?limit=${limit}`, z.array(dueItemSchema)),
  reviewSummary: () => request("/review/summary", reviewSummarySchema),
  grade: (id: number, grade: Grade, mode: ReviewMode) =>
    request(`/review/items/${id}/grade`, gradeResultSchema, post({ grade, mode })),
  checkRecall: (id: number, answer: string) =>
    request(`/review/items/${id}/check-recall`, recallCheckSchema, post({ answer })),
  checkSentence: (id: number, sentence: string) =>
    request(`/review/items/${id}/check-sentence`, sentenceCheckSchema, post({ sentence })),

  scenarios: () => request("/conversation/scenarios", z.array(scenarioSchema)),
  conversations: () => request("/conversation", z.array(conversationListItemSchema)),
  conversation: (id: number) => request(`/conversation/${id}`, conversationSchema),
  startConversation: (scenarioKey: string, targetPhraseIds: number[], topic?: string) =>
    request(
      "/conversation",
      conversationSchema,
      post({ scenario_key: scenarioKey, target_phrase_ids: targetPhraseIds, topic }),
    ),
  sendMessage: (id: number, content: string) =>
    request(`/conversation/${id}/messages`, sendMessageSchema, post({ content })),
  hint: (id: number) => request(`/conversation/${id}/hint`, hintListSchema, { method: "POST" }),
  finishConversation: (id: number) =>
    request(`/conversation/${id}/finish`, conversationSchema, { method: "POST" }),
  addConversationPhrase: (id: number, english: string, polish: string) =>
    request(`/conversation/${id}/phrases`, addPhraseSchema, post({ english, polish })),

  lessons: () => request("/lessons", z.array(lessonListItemSchema)),
  lesson: (id: number) => request(`/lessons/${id}`, lessonSchema),
  createLesson: (type: Exclude<LessonType, "placement">, topic?: string) =>
    request("/lessons", lessonSchema, post({ type, topic: topic || undefined })),
  answerExercise: (id: number, exerciseIndex: number, answer: string) =>
    request(`/lessons/${id}/answers`, lessonSchema, post({ exercise_index: exerciseIndex, answer })),
  submitWriting: (id: number, text: string) =>
    request(`/lessons/${id}/writing`, lessonSchema, post({ text })),
  completeLesson: (id: number) =>
    request(`/lessons/${id}/complete`, lessonSchema, { method: "POST" }),
  placementQuestions: (selfLevel: CefrLevel) =>
    request(`/lessons/placement?self_level=${selfLevel}`, placementQuestionsSchema),
  runPlacement: (selfLevel: CefrLevel, translation: string, correction: string) =>
    request(
      "/lessons/placement",
      placementResultSchema,
      post({ self_level: selfLevel, translation, correction }),
    ),
};
