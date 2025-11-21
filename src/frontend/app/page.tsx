"use client";

import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen w-full items-center justify-center">
      <Link href={"/chat"}>
        <button className="rounded-4xl border border-amber-100 px-2 py-0.5 transition-all duration-300 hover:cursor-pointer hover:bg-amber-950">
          Queue for a date
        </button>
      </Link>
    </main>
  );
}
