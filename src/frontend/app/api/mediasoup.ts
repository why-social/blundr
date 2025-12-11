import {
  DtlsParameters,
  IceCandidate,
  IceParameters,
  MediaKind,
  RtpCapabilities,
  RtpParameters,
} from "mediasoup-client/types";
import { chatroomRequest } from "./request";

export type WRTCTransport = {
  id: string;
  iceParameters: IceParameters;
  iceCandidates: IceCandidate[];
  dtlsParameters: DtlsParameters;
};

export type WRTCProducer = {
  producerId: string;
};

export type WRTCConsumer = {
  id: string;
  producerId: string;
  kind: MediaKind;
  rtpParameters: RtpParameters;
};

export async function getRouterRtpCapabilities() {
  return chatroomRequest<RtpCapabilities>("GET", "wrtc/capabilities");
}

export async function createTransport(
  clientId: string,
  direction: "send" | "receive",
) {
  return await chatroomRequest<WRTCTransport>("POST", "wrtc/create", {
    clientId,
    direction,
  });
}

export async function connectTransport(
  transportId: string,
  dtlsParameters: DtlsParameters,
) {
  return chatroomRequest("POST", "wrtc/connect", {
    transportId,
    dtlsParameters,
  });
}

export async function createProducer(
  transportId: string,
  kind: "audio" | "video",
  rtpParameters: RtpParameters,
) {
  return chatroomRequest<WRTCProducer>("POST", "wrtc/produce", {
    transportId,
    kind,
    rtpParameters,
  });
}

export async function createConsumer(
  consumingClientId: string,
  clientId: string,
  kind: MediaKind,
  rtpCapabilities: RtpCapabilities,
) {
  return chatroomRequest<WRTCConsumer>("POST", "wrtc/consume", {
    consumingClientId,
    clientId,
    kind,
    rtpCapabilities,
  });
}

export async function resumeConsumer(consumerId: string) {
  return chatroomRequest("POST", "wrtc/resume", { consumerId });
}
