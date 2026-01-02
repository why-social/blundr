// Original Author: Razvan Albu
// Source: https://git.chalmers.se/courses/dit826/2025/team2
// License: MIT

import cors from "cors";

export default cors({
  origin: function (_origin, callback) {
	// TODO: Add production URLs

    // if (origin?.match(/^http:\/\/localhost:\d+$/)) {
    //   return callback(null, true);
    // }

    // return callback(new Error("Not allowed by CORS."), false);

	return callback(null, true);
  },
});
