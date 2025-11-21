import dotenv from "dotenv";

dotenv.config();

interface Config {
  port: number;
}

export default {
  port: Number(process.env["PORT"]) || 3000,
} satisfies Config;
