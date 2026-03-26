"use client";

import type { UserSummary, SessionDetailResponse } from "@/lib/api";
import {
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion";
import { SessionList } from "./session-list";

interface UserAccordionProps {
  user: UserSummary;
  sessionDetails: Map<string, SessionDetailResponse>;
  loadingSessions: Set<string>;
  onSessionToggle: (handle: string, sessionId: string) => void;
}

export function UserAccordion({
  user,
  sessionDetails,
  loadingSessions,
  onSessionToggle,
}: UserAccordionProps) {
  return (
    <AccordionItem value={user.handle}>
      <AccordionTrigger className="py-3 hover:no-underline">
        <div className="flex items-center gap-2">
          <span className="font-medium">@{user.handle}</span>
          <span className="text-xs text-muted-foreground">
            {user.session_count} {user.session_count === 1 ? "session" : "sessions"}
          </span>
        </div>
      </AccordionTrigger>
      <AccordionContent>
        <SessionList
          handle={user.handle}
          sessions={user.sessions}
          sessionDetails={sessionDetails}
          loadingSessions={loadingSessions}
          onSessionToggle={onSessionToggle}
        />
      </AccordionContent>
    </AccordionItem>
  );
}
