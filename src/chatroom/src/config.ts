// Original Author: Razvan Albu
// Source: https://git.chalmers.se/courses/dit826/2025/team2
// License: MIT

import dotenv from "dotenv";

dotenv.config();

interface Config {
  port: number;
}

export default {
  port: Number(process.env["PORT"]) || 3000,
} satisfies Config;
