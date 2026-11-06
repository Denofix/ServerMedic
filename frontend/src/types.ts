export type LogLine = { number: number; text: string };
export type LogDocument = {
  filename: string;
  size_bytes: number;
  line_count: number;
  redaction_count: number;
  lines: LogLine[];
};
export type Finding = {
  title: string;
  severity: "low" | "medium" | "high" | "critical";
  observation: string;
  hypothesis: string;
  evidence_lines: number[];
  evidence: { line: number; text: string }[];
  recommended_checks: string[];
};
export type AnalysisResponse = {
  document: LogDocument;
  analysis: {
    summary: string;
    findings: Finding[];
    limitations: string[];
    missing_context: string[];
  };
  markdown: string;
  provider: string;
  model: string;
};
export type Example = { id: string; title: string; description: string };
export type Health = {
  status: string;
  analysis_configured: boolean;
  provider: string;
  model: string;
};
