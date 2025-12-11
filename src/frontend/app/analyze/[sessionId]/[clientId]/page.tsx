"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { Button } from "@/app/components/Button";
import { useEffect, useState } from "react";
import { analysisRequest } from "@/app/api/request";

const RETRY_INTERVAL = 5000;
interface AnalysisResponse {
  session_id: string;
  requested_by: string;
  analysis: string;
}

export default function Analyze() {
  const { sessionId, clientId } = useParams();
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId || !clientId) {
      return;
    }

    const fetchAnalysis = async () => {
      try {
        // This will timeout???
        const analysisRequestRes = await analysisRequest<AnalysisResponse>(
          "POST",
          "/analyze",
          JSON.stringify({ sessionId, clientId }),
        );

        if (analysisRequestRes.status === "error") {
          setLoading(true);
        } else {
          setAnalysis(analysisRequestRes.data);
          setLoading(false);
          clearInterval(intervalId);
        }
      } catch (error) {
        setError((error as Error).message || "Something went wrong");
        setLoading(false);
        clearInterval(intervalId);
      }
    };

    fetchAnalysis();
    const intervalId = window.setInterval(fetchAnalysis, RETRY_INTERVAL);

    return () => clearInterval(intervalId);
  }, [sessionId, clientId]);

  return (
    <main className="flex min-h-screen w-full flex-col items-center justify-center gap-4">
      {loading && !analysis && (
        <div className="flex flex-col items-center gap-2">
          <div className="h-8 w-8 animate-spin rounded-full border-t-2 border-b-2 border-blue-500"></div>
          <p>Processing...</p>
          {error && <p className="text-red-500">{error}</p>}
        </div>
      )}

      {analysis && (
        <div>
          <h2>Analysis Result:</h2>
          <pre className="rounded bg-gray-100 p-4">{analysis.analysis}</pre>
        </div>
      )}

      <Link href="/">
        <Button>To home</Button>
      </Link>
    </main>
  );
}
