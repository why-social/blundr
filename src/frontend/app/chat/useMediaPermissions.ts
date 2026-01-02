// Original Author: Razvan Albu
// Source: https://git.chalmers.se/courses/dit826/2025/team2
// License: MIT

export async function checkMediaPermissions() {
  if (!navigator.permissions) return "no-permissions-api";

  try {
    const mic = await navigator.permissions.query({
      name: "microphone" as PermissionName,
    });
    const cam = await navigator.permissions.query({
      name: "camera" as PermissionName,
    });

    if (mic.state === "denied" || cam.state === "denied") return "denied";
    if (mic.state === "prompt" || cam.state === "prompt") return "prompt";

    return "granted";
  } catch {
    return "no-permissions-api";
  }
}
