import {
  DtlsParameters,
  IceCandidate,
  IceParameters,
  MediaKind,
  RtpCapabilities,
  RtpParameters,
} from "mediasoup-client/types";
import { apiRequest } from "./request";

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
  return apiRequest<RtpCapabilities>("GET", "wrtc/capabilities");
}

export async function createTransport(
  clientId: string,
  direction: "send" | "receive",
) {
  return apiRequest<WRTCTransport>("POST", "wrtc/create", {
    clientId,
    direction,
  });
}

export async function connectTransport(
  transportId: string,
  dtlsParameters: DtlsParameters,
) {
  return apiRequest("POST", "wrtc/connect", {
    transportId,
    dtlsParameters,
  });
}

export async function createProducer(
  transportId: string,
  kind: "audio" | "video",
  rtpParameters: RtpParameters,
) {
  return apiRequest<WRTCProducer>("POST", "wrtc/produce", {
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
  return apiRequest<WRTCConsumer>("POST", "wrtc/consume", {
    consumingClientId,
    clientId,
    kind,
    rtpCapabilities,
  });
}

export async function resumeConsumer(consumerId: string) {
  return apiRequest("POST", "wrtc/resume", { consumerId });
}
