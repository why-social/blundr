"use client";

import Link from "next/link";
import { Button } from "./components/Button";

export default function Home() {
  return (
    <main className="flex min-h-screen w-full items-center justify-center">
      <Link href={"/chat"}>
        <Button>Queue for a date</Button>
      </Link>
    </main>
  );
}
