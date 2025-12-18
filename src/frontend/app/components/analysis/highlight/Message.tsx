import Image from "next/image";
import { twMerge } from "tailwind-merge";
import { Annotation } from "../types";

export function Message({
  message,
  annotation,
  own,
}: {
  message: string;
  annotation?: Annotation;
  own?: boolean;
}) {
  return (
    <div
      className={twMerge(
        "relative w-fit rounded-b-2xl px-4 py-3 text-lg leading-[1.3] font-medium text-black",
        own
          ? "ml-10 [align-self:end] rounded-l-2xl -bg-linear-30"
          : "mr-10 rounded-r-2xl bg-linear-3",
        annotation
          ? "from-pink-200 to-pink-50"
          : "from-[#d9b0c7] to-[#e0d3da] opacity-90",
        !!annotation &&
          "before:pointer-events-none before:absolute before:inset-0 before:-z-10 before:rounded-md before:bg-linear-to-r before:from-pink-600 before:via-fuchsia-400 before:to-red-400 before:opacity-90 before:blur-xl",
      )}
    >
      <div className={twMerge("font-semibold", own ? "flex justify-end" : "")}>
        {own ? (
          <span className="text-lime-800">You</span>
        ) : (
          <div className="flex flex-row items-center gap-1">
            <span className="text-rose-700">Date</span>
            <Image
              src={"/heart.svg"}
              alt="Heart"
              width={100}
              height={100}
              className="mt-[0.06rem] size-4.5"
            />
          </div>
        )}
      </div>
      <p>{message}</p>
      {annotation && (
        <Image
          src={`/${annotation}.svg`}
          width={100}
          height={100}
          alt="Annotation"
          className="absolute -top-6 -right-5 size-10 rotate-12"
        />
      )}
    </div>
  );
}
