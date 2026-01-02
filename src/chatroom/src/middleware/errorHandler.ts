// Original Author: Razvan Albu
// Source: https://git.chalmers.se/courses/dit826/2025/team2
// License: MIT

import { type Request, type Response, type NextFunction } from "express";
import { logError } from "../utils/logs.js";

export interface AppError extends Error {
  status?: number;
}

export default (
  err: AppError,
  _req: Request,
  res: Response,
  _next: NextFunction
) => {
  logError(err);

  res.status(err.status || 500).json({
    message: err.message || "Internal Server Error",
  });
};
