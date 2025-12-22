import { Button } from "./Button";

export function ErrorDialog({
  message,
  onReturn,
}: {
  message: string | null;
  onReturn: () => void;
}) {
  return (
    <div className="[pointer-events:all] fixed top-0 left-0 z-50 flex h-full w-full flex-col items-center justify-center bg-black/70 backdrop-blur-sm">
      <p className="mb-4">{message ?? "Something went wrong"}</p>
      <Button onClick={onReturn}>Return Home</Button>
    </div>
  );
}
