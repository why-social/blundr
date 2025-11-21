import { Request, Response, NextFunction } from "express";
import * as mediasoup from "./mediasoup.js";

export const getCapabilities = async (
  _req: Request,
  res: Response,
  next: NextFunction
) => {
  try {
    res.json(mediasoup.getCapabilities());
  } catch (err) {
    next(err);
  }
};

export const create = async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  try {
    const { clientId, direction } = req.body;

    res.json(await mediasoup.create(clientId, direction));
  } catch (err) {
    next(err);
  }
};

export const connect = async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  try {
    const { transportId, dtlsParameters } = req.body;

    res.json(await mediasoup.connect(transportId, dtlsParameters));
  } catch (err) {
    next(err);
  }
};

export const produce = async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  try {
    const { transportId, kind, rtpParameters } = req.body;

    res.json(await mediasoup.produce(transportId, kind, rtpParameters));
  } catch (err) {
    next(err);
  }
};

export const consume = async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  try {
    const { consumingClientId, clientId, kind, rtpCapabilities } = req.body;

    res.json(
      await mediasoup.consume(
        consumingClientId,
        clientId,
        kind,
        rtpCapabilities
      )
    );
  } catch (err) {
    next(err);
  }
};

export const resume = async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  try {
    const { consumerId } = req.body;
    await mediasoup.resume(consumerId);

    res.json({ resumed: true });
  } catch (err) {
    next(err);
  }
};
