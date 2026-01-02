// Original Author: Razvan Albu
// Source: https://git.chalmers.se/courses/dit826/2025/team2
// License: MIT

"use client";

import { NavigateOptions } from "next/dist/shared/lib/app-router-context.shared-runtime";
import { useRouter } from "next/navigation";
import {
  createContext,
  useContext,
  useRef,
  useEffect,
  useCallback,
  ReactNode,
} from "react";

type BlockNavigationContextType = {
  /**
   * @param callback called on back event
   */
  blockBack: (callback: () => void) => void;
  unblockBack: () => void;
  /**
   * @param callback Return a message that is presented to
   * the user when refreshing the page (prevent refresh)
   */
  blockRefresh: (message?: string) => void;
  unblockRefresh: () => void;
  // patched router.replace function
  replace: (url: string, options?: NavigateOptions) => void;
};

const BlockNavigationContext = createContext<BlockNavigationContextType | null>(
  null,
);

export function BlockNavigationProvider({ children }: { children: ReactNode }) {
  const router = useRouter();

  const onBackAttempt = useRef<(() => void) | null>(null);
  const onRefreshAttempt = useRef<string | null>(null);

  // back blocking
  useEffect(() => {
    const handlePopState = (event: PopStateEvent) => {
      if (!onBackAttempt.current) {
        return;
      }

      if (!event.state || !event.state.__blockSentinel) {
        onBackAttempt.current();

        history.pushState({ __blockSentinel: true }, "", location.href);
      }
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  // refresh blocking
  useEffect(() => {
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      const message = onRefreshAttempt.current;

      if (message) {
        // needed for old browsers
        event.returnValue = message;

        // needed for Chrome
        return message;
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, []);

  const blockBack = useCallback((callback: () => void) => {
    onBackAttempt.current = callback;

    history.pushState({ __blockSentinel: true }, "", location.href);
  }, []);

  const unblockBack = useCallback(() => {
    onBackAttempt.current = null;

    if (history.state?.__blockSentinel) {
      history.back();
    }
  }, []);

  const blockRefresh = useCallback((message?: string) => {
    onRefreshAttempt.current = message ?? "Are you sure you want to leave?";
  }, []);

  const unblockRefresh = useCallback(() => {
    onRefreshAttempt.current = null;
  }, []);

  const replace = useCallback(
    (url: string, options?: NavigateOptions) => {
      const handlePop = () => {
        window.removeEventListener("popstate", handlePop);
        router.replace(url, options);
      };

      window.addEventListener("popstate", handlePop);
      unblockRefresh();
      unblockBack();
    },
    [router, unblockBack, unblockRefresh],
  );

  return (
    <BlockNavigationContext.Provider
      value={{ blockBack, unblockBack, blockRefresh, unblockRefresh, replace }}
    >
      {children}
    </BlockNavigationContext.Provider>
  );
}

export function useGlobalNavigationBlocker() {
  const context = useContext(BlockNavigationContext);

  if (!context) {
    throw new Error(
      "useGlobalNavigationBlocker must be used within BlockNavigationContext",
    );
  }

  return context;
}
