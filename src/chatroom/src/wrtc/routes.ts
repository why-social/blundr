// Original Author: Razvan Albu
// Source: https://git.chalmers.se/courses/dit826/2025/team2
// License: MIT

import { Router } from "express";
import {
  getCapabilities,
  create,
  connect,
  produce,
  consume,
  resume,
} from "./controller.js";

const router = Router();

router.get("/capabilities", getCapabilities);

router.post("/create", create);
router.post("/connect", connect);
router.post("/produce", produce);
router.post("/consume", consume);
router.post("/resume", resume);

export default router;
