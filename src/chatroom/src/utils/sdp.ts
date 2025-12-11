import { Consumer, MediaKind, RtpParameters } from "mediasoup/types";

// based on https://github.com/ethand91/mediasoup3-record-demo/blob/180973063f1aecdc02b91d8e909f21ceb40ce53b/server/src/sdp.js#L4
export function generateSDP(consumer: Consumer, rtpPort: number) {
  const { kind, rtpParameters } = consumer;
  const codecInfo = getCodecInfoFromRtpParameters(kind, rtpParameters);

  return [
    "v=0",
    "o=- 0 0 IN IP4 127.0.0.1",
    "s=mediasoup",
    "c=IN IP4 127.0.0.1",
    "t=0 0",
    `m=${kind} ${rtpPort} RTP/AVP ${codecInfo.payloadType}`,
    `a=rtpmap:${codecInfo.payloadType} ${codecInfo.codecName}/${
      codecInfo.clockRate
    }${codecInfo.channels ? "/" + codecInfo.channels : ""}`,
    "a=sendonly",
  ].join("\n");
}

function getCodecInfoFromRtpParameters(
  kind: MediaKind,
  rtpParameters: RtpParameters
) {
  return {
    payloadType: rtpParameters.codecs[0].payloadType,
    codecName: rtpParameters.codecs[0].mimeType.replace(`${kind}/`, ""),
    clockRate: rtpParameters.codecs[0].clockRate,
    channels: kind === "audio" ? rtpParameters.codecs[0].channels : undefined,
  };
}
