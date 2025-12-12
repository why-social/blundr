"use client";

import Link from "next/link";
import { Button } from "./components/Button";
import { EmphasisText } from "./components/EmphasisText";
import Image from "next/image";

export default function Home() {
  return (
    <main className="flex min-h-screen w-full items-center justify-center">
      <div className="flex w-fit flex-col items-center justify-center gap-10">
        <div className="relative">
          <Image
            src={"/blunder.svg"}
            alt="blunder"
            width={100}
            height={100}
            className="absolute -top-20 left-12 z-100 size-16 -rotate-12 md:-top-16 md:-left-12 md:size-25"
          />
          <EmphasisText
            text="BLUNDR"
            emphasis="strong"
            className="animate-slide-in text-6xl font-black italic sm:text-7xl md:text-8xl"
          />
        </div>

        <h3 className="text-md relative max-w-[70%] text-center leading-tight font-normal text-balance md:text-xl">
          Practice{" "}
          <EmphasisText
            text="real conversations"
            className="font-bold italic"
          />{" "}
          in{" "}
          <EmphasisText
            text="AI-guided"
            className="font-bold italic"
          />{" "}
          video sessions that analyze emotions, tone, and dialogue, giving you{" "}
          <EmphasisText
            text="personalized insights"
            className="font-bold italic"
          />{" "}
          to grow your confidence and dating communication.
        </h3>

        <div className="relative">
          <Image
            src={"/brilliant.svg"}
            alt="blunder"
            width={100}
            height={100}
            className="absolute -right-4 -bottom-20 z-100 size-16 rotate-15 md:-right-16 md:-bottom-20 md:size-25"
          />
          <Link href={"/chat"}>
            <Button
              blurryBorder={true}
              className="rounded-xl"
            >
              Queue for a date
            </Button>
          </Link>
        </div>
      </div>
    </main>
  );
}
