import cors from "cors";

export default cors({
  origin: function (origin, callback) {
    if (origin?.match(/^http:\/\/localhost:\d+$/)) {
      return callback(null, true);
    }

    // TODO: Add production URLs

    return callback(new Error("Not allowed by CORS."), false);
  },
});
