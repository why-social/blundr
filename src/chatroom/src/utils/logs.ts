const COLORS = {
  reset: "\x1b[0m",
  red: "\x1b[31m",
  yellow: "\x1b[33m",
  cyan: "\x1b[36m",
  magenta: "\x1b[35m",
};

export function logInfo(...args: any[]) {
  console.log(`${COLORS.cyan}[INFO]`, ...args, COLORS.reset);
}
export function logWarn(...args: any[]) {
  console.warn(`${COLORS.yellow}[WARN]`, ...args, COLORS.reset);
}
export function logError(...args: any[]) {
  console.error(`${COLORS.red}[ERROR]`, ...args, COLORS.reset);
}
export function logFFmpeg(
  kind: string,
  sessionId: string,
  clientId: string,
  data: any
) {
  console.log(
    `${COLORS.magenta}[FFmpeg ${kind} session ${sessionId} client ${clientId}]`,
    data.toString(),
    COLORS.reset
  );
}
