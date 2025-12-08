"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { Button } from "@/app/components/Button";

export default function Analyze() {
  const { sessionId } = useParams();

  return (
    <main className="flex min-h-screen w-full flex-col items-center justify-center">
      Session ID: {sessionId}
      <Link href={"/"}>
        <Button>To home</Button>
      </Link>
    </main>
  );
}
