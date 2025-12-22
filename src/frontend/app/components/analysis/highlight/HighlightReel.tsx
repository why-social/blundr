import Image from "next/image";
import { AnalysisContent } from "../types";
import { Message } from "./Message";
import { twMerge } from "tailwind-merge";
import { EmphasisText } from "../../EmphasisText";

const ANNOTATION_DESCRIPTIONS = {
  great:
    "A moment that felt smooth and enjoyable, like a fun conversation or shared laugh.",
  excellent:
    "A standout event, like a deep, meaningful connection or a perfect date.",
  mistake:
    "An event where something didn't go as planned, like an awkward silence or misstep.",
  blunder:
    "A major faux pas, like a conversation that went off the rails or a huge misjudgment.",
  textbook:
    "A moment where you felt there's potential to explore more, like agreeing to a second date.",
  brilliant:
    "A memorable event that exceeded expectations, like an incredible, unforgettable experience together.",
};

const GLOW_TEXT_CLASS =
  "inline-block font-semibold bg-linear-50 from-purple-700 via-pink-700 to-red-700 bg-clip-text text-transparent capitalize";

export function HighlightReel({
  analysis,
  classname,
  user,
}: {
  analysis: AnalysisContent;
  classname?: string;
  user: string;
}) {
  return (
    <>
      <div
        className={twMerge(
          "flex flex-col items-center gap-5 px-10 py-20",
          classname,
        )}
        style={{
          transform: "translateY(50px)",
          opacity: 0,
          animation: "slideIn 1s ease-out forwards",
        }}
      >
        <EmphasisText
          text="SPOTLIGHT"
          emphasis="strong"
          className="sticky pb-10 text-3xl font-black sm:text-5xl md:text-7xl"
        />

        {analysis.highlights.map((highlight, index) => {
          return (
            <div
              className="relative flex w-full flex-col gap-8"
              key={highlight.description + index}
            >
              <div className="flex w-full flex-col gap-4">
                {highlight.context_block.map((context, index) => {
                  return (
                    <Message
                      annotation={
                        highlight.main_message == context.message &&
                        context.user === highlight.main_user
                          ? highlight.annotation
                          : undefined
                      }
                      message={context.message}
                      own={context.user === user}
                      key={index}
                    />
                  );
                })}
              </div>

              <div
                className={twMerge(
                  "flex flex-col gap-4 rounded-2xl p-4 text-lg leading-[1.3] font-medium",
                  "text-black shadow-[inset_0_2px_10px_#fccee8] [text-shadow:0px_0px_20px_white]",
                  "bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.9)_0%,rgba(255,255,255,0.8)_70%,rgba(255,255,255,0.6)_130%)]",
                  "outline-2 outline-pink-200",
                )}
              >
                <div className="group flex flex-col">
                  <div className="z-10 flex flex-row items-center gap-2 select-none">
                    <Image
                      src={`/${highlight.annotation}.svg`}
                      alt="Heart"
                      width={100}
                      height={100}
                      className="size-8"
                    />

                    <div className={GLOW_TEXT_CLASS}>
                      {highlight.annotation}
                    </div>
                  </div>

                  <div className="-mt-1 grid grid-rows-[0fr] opacity-0 transition-[grid-template-rows,opacity] duration-300 ease-in-out group-hover:grid-rows-[1fr] group-hover:opacity-100">
                    <div className="ml-3.5 overflow-hidden border-l-4 border-l-gray-400 pt-2 pl-3 italic">
                      {ANNOTATION_DESCRIPTIONS[highlight.annotation]}
                    </div>
                  </div>
                </div>

                <p>{highlight.description}</p>
              </div>

              <hr
                className={twMerge(
                  "h-3 -translate-y-1.5 border-0 bg-center bg-repeat-x opacity-30",
                  'bg-[url("data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCA0MCAxMiIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiBmaWxsPSJub25lIj4KICA8cGF0aCBkPSJNMCA2IEM4IDIsIDEyIDIsIDIwIDYgQzI4IDEwLCAzMiAxMCwgNDAgNiIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIiBmaWxsPSJub25lIi8+Cjwvc3ZnPg==")]',
                )}
              />
            </div>
          );
        })}

        <div
          className={twMerge(
            "relative flex flex-col gap-4 rounded-2xl p-4 text-lg leading-[1.3] font-medium",
            "text-black shadow-[inset_0_2px_10px_#fccee8] [text-shadow:0px_0px_20px_white]",
            "bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.9)_0%,rgba(255,255,255,0.8)_70%,rgba(255,255,255,0.6)_130%)]",
            "outline-2 outline-pink-200",
            "before:pointer-events-none before:absolute before:inset-0 before:-z-10 before:rounded-md before:bg-linear-to-r before:from-pink-600 before:via-fuchsia-400 before:to-red-400 before:opacity-90 before:blur-xl",
          )}
        >
          <div className="flex w-full flex-row items-center gap-3">
            <Image
              src={"/mr_blundr.png"}
              alt="Heart"
              width={100}
              height={100}
              className="size-12"
            />

            <p className={GLOW_TEXT_CLASS}>Mr. Blundr</p>
          </div>

          {analysis.strengths.length == 0 &&
          analysis.improvements.length == 0 ? (
            <>Great job!</>
          ) : (
            <>
              {analysis.strengths.length > 0 && (
                <div className="flex flex-col gap-2">
                  <h3 className="italic">Strengths</h3>
                  <ul className="ml-4 list-disc space-y-1">
                    {analysis.strengths.map((strength, index) => {
                      return <li key={index}>{strength}</li>;
                    })}
                  </ul>
                </div>
              )}

              {analysis.improvements.length > 0 && (
                <div className="flex flex-col gap-2">
                  <h3 className="italic">Improvements</h3>
                  <ul className="ml-4 list-disc space-y-1">
                    {analysis.improvements.map((improvement, index) => {
                      return <li key={index}>{improvement}</li>;
                    })}
                  </ul>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      <style jsx>{`
        @keyframes slideIn {
          0% {
            transform: translateY(3rem);
            opacity: 0;
          }
          100% {
            transform: translateY(0);
            opacity: 1;
          }
        }
      `}</style>
    </>
  );
}
