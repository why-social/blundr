export interface AnalysisResponse {
  session_id: string;
  requested_by: string;
  status: string;
  analysis: AnalysisContent;
}

export interface AnalysisContent {
  highlights: Highlight[];
  strengths: string[];
  improvements: string[];
}

export interface Highlight {
  timestamp: string;
  main_user: string;
  main_message: string;
  description: string;
  annotation: Annotation;
  context_block: ContextBlock[];
}

export type Annotation =
  | "great"
  | "excellent"
  | "mistake"
  | "blunder"
  | "textbook"
  | "brilliant";

export interface ContextBlock {
  timestamp: string;
  user: string;
  message: string;
}
