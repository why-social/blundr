import { Router } from "express";

import wrtcRouter from "./wrtc/routes.js";

const router = Router();

router.use("/api/v1/wrtc", wrtcRouter);
router.use((_req, res) => {
  res.status(404).json({
    error: "Not Found",
  });
});

export default router;
