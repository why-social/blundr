// Original Author: Razvan Albu
// Source: https://git.chalmers.se/courses/dit826/2025/team2
// License: MIT

"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { analysisRequest } from "@/app/api/request";
import {
  AnalysisContent,
  AnalysisResponse,
} from "../../../components/analysis/types";
import { ErrorDialog } from "@/app/components/ErrorDialog";
import { EmphasisText } from "@/app/components/EmphasisText";
import AmbientCue from "@/app/components/AmbientCue";
import { HighlightReel } from "@/app/components/analysis/highlight/HighlightReel";

const RETRY_INTERVAL = 5000;

export default function Analyze() {
  const router = useRouter();
  const { sessionId, clientId } = useParams();

  const [analysis, setAnalysis] = useState<AnalysisContent | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (
      !sessionId ||
      !clientId ||
      Array.isArray(sessionId) ||
      Array.isArray(clientId)
    ) {
      return;
    }

    const fetchAnalysis = async () => {
      try {
        const analysisRequestRes = await analysisRequest<AnalysisResponse>(
          "GET",
          `analyze?session_id=${sessionId}&user_id=${clientId}`,
        );

        if (analysisRequestRes.status === "ok") {
          setAnalysis(analysisRequestRes.data.analysis);

          clearInterval(intervalId);
        }
      } catch (error) {
        setError((error as Error).message || "Something went wrong");
        clearInterval(intervalId);
      }
    };

    const intervalId = window.setInterval(fetchAnalysis, RETRY_INTERVAL);

    return () => clearInterval(intervalId);
  }, [sessionId, clientId]);

  return (
    <main className="flex min-h-screen w-full flex-col items-center justify-center gap-4">
      {!analysis && (
        <div className="relative flex min-h-screen w-full items-center justify-center">
          <div className="flex flex-col items-center">
            <EmphasisText
              text={"PROCESSING"}
              emphasis="strong"
              className="scale-50 text-6xl font-black italic sm:text-7xl md:text-8xl"
            />
            <h3 className="text-md relative max-w-[70%] text-center leading-tight font-normal text-balance md:text-xl">
              Please be patient, this can take a while!
            </h3>
          </div>
          <AmbientCue
            images={[
              "/blunder.svg",
              "/textbook.svg",
              "/brilliant.svg",
              "/excellent.svg",
              "/great.svg",
              "/mistake.svg",
            ]}
          />
        </div>
      )}

      {analysis && (
        <HighlightReel
          analysis={analysis}
          user={clientId as string}
          classname={"max-w-120 md:max-w-150"}
        />
      )}

      {error && (
        <ErrorDialog
          message={error}
          onReturn={() => router.replace("/")}
        />
      )}
    </main>
  );
}
