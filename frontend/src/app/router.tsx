import { lazy, Suspense } from "react";
import { createBrowserRouter } from "react-router";

import { EmptyState, Spinner } from "@/shared/ui/states";

import { AppLayout, ModuleGate } from "./layout";

// Pages load on demand so the first screen downloads only what it needs.
const ChatPage = lazy(() => import("@/modules/conversation/chat-page").then((m) => ({ default: m.ChatPage })));
const ConversationPage = lazy(() => import("@/modules/conversation/conversation-page").then((m) => ({ default: m.ConversationPage })));
const DashboardPage = lazy(() => import("@/modules/dashboard/dashboard-page").then((m) => ({ default: m.DashboardPage })));
const LessonPage = lazy(() => import("@/modules/lessons/lesson-page").then((m) => ({ default: m.LessonPage })));
const LessonsPage = lazy(() => import("@/modules/lessons/lessons-page").then((m) => ({ default: m.LessonsPage })));
const PlacementPage = lazy(() => import("@/modules/lessons/placement-page").then((m) => ({ default: m.PlacementPage })));
const OnboardingPage = lazy(() => import("@/modules/onboarding/onboarding-page").then((m) => ({ default: m.OnboardingPage })));
const LearnPage = lazy(() => import("@/modules/phrases/learn-page").then((m) => ({ default: m.LearnPage })));
const PhrasesPage = lazy(() => import("@/modules/phrases/phrases-page").then((m) => ({ default: m.PhrasesPage })));
const SectionPage = lazy(() => import("@/modules/phrases/section-page").then((m) => ({ default: m.SectionPage })));
const ReviewPage = lazy(() => import("@/modules/review/review-page").then((m) => ({ default: m.ReviewPage })));
const SettingsPage = lazy(() => import("@/modules/settings/settings-page").then((m) => ({ default: m.SettingsPage })));

export const router = createBrowserRouter([
  {
    path: "/onboarding",
    element: (
      <Suspense fallback={<Spinner />}>
        <OnboardingPage />
      </Suspense>
    ),
  },
  {
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: (
          <ModuleGate moduleKey="progress">
            <DashboardPage />
          </ModuleGate>
        ),
      },
      {
        path: "phrases",
        element: (
          <ModuleGate moduleKey="phrases">
            <PhrasesPage />
          </ModuleGate>
        ),
      },
      {
        path: "phrases/learn",
        element: (
          <ModuleGate moduleKey="phrases">
            <LearnPage />
          </ModuleGate>
        ),
      },
      {
        path: "phrases/:code",
        element: (
          <ModuleGate moduleKey="phrases">
            <SectionPage />
          </ModuleGate>
        ),
      },
      {
        path: "review",
        element: (
          <ModuleGate moduleKey="review">
            <ReviewPage />
          </ModuleGate>
        ),
      },
      {
        path: "conversation",
        element: (
          <ModuleGate moduleKey="conversation">
            <ConversationPage />
          </ModuleGate>
        ),
      },
      {
        path: "conversation/:id",
        element: (
          <ModuleGate moduleKey="conversation">
            <ChatPage />
          </ModuleGate>
        ),
      },
      {
        path: "lessons",
        element: (
          <ModuleGate moduleKey="lessons">
            <LessonsPage />
          </ModuleGate>
        ),
      },
      {
        path: "lessons/placement",
        element: (
          <ModuleGate moduleKey="lessons">
            <PlacementPage />
          </ModuleGate>
        ),
      },
      {
        path: "lessons/:id",
        element: (
          <ModuleGate moduleKey="lessons">
            <LessonPage />
          </ModuleGate>
        ),
      },
      { path: "settings", element: <SettingsPage /> },
      {
        path: "*",
        element: <EmptyState icon="🧭" title="Nie ma takiej strony" />,
      },
    ],
  },
]);
