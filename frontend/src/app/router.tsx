import { createBrowserRouter } from "react-router";

import { ChatPage } from "@/modules/conversation/chat-page";
import { ConversationPage } from "@/modules/conversation/conversation-page";
import { DashboardPage } from "@/modules/dashboard/dashboard-page";
import { OnboardingPage } from "@/modules/onboarding/onboarding-page";
import { LearnPage } from "@/modules/phrases/learn-page";
import { PhrasesPage } from "@/modules/phrases/phrases-page";
import { SectionPage } from "@/modules/phrases/section-page";
import { ReviewPage } from "@/modules/review/review-page";
import { SettingsPage } from "@/modules/settings/settings-page";
import { EmptyState } from "@/shared/ui/states";

import { AppLayout, ModuleGate } from "./layout";

export const router = createBrowserRouter([
  { path: "/onboarding", element: <OnboardingPage /> },
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
      { path: "settings", element: <SettingsPage /> },
      {
        path: "*",
        element: <EmptyState icon="🧭" title="Nie ma takiej strony" />,
      },
    ],
  },
]);
