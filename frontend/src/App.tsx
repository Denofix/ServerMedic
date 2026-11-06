import { useEffect, useRef, useState } from "react";
import {
  Activity,
  ArrowDownToLine,
  ArrowRight,
  Check,
  CheckCheck,
  CircleAlert,
  CircleCheck,
  FileCode2,
  FileText,
  FlaskConical,
  LoaderCircle,
  LockKeyhole,
  ScanLine,
  ShieldCheck,
  Terminal,
  Upload,
  X,
} from "lucide-react";
import { analyze, checked, getExamples, getHealth, preview } from "./api";
import type {
  AnalysisResponse,
  Example,
  Finding,
  Health,
  LogDocument,
} from "./types";

type Phase =
  | "idle"
  | "preparing"
  | "ready"
  | "analyzing"
  | "complete"
  | "error";

function messageFor(error: unknown) {
  if (error instanceof DOMException && error.name === "TimeoutError")
    return "The request timed out. Please try again.";
  if (error instanceof TypeError)
    return "Cannot reach the backend. Check that the service is running.";
  return error instanceof Error
    ? error.message
    : "Something went wrong. Please try again.";
}

function FindingCard({
  finding,
  index,
  onJump,
}: {
  finding: Finding;
  index: number;
  onJump: (n: number) => void;
}) {
  return (
    <article className="finding">
      <div className="finding-heading">
        <span className="finding-index">
          {String(index + 1).padStart(2, "0")}
        </span>
        <h3>{finding.title}</h3>
        <span className={`severity ${finding.severity}`}>
          {finding.severity}
        </span>
      </div>
      <div className="finding-body">
        <p className="field-label">Observed in the log</p>
        <p>{finding.observation}</p>
        <div className="hypothesis">
          <p className="field-label">Possible cause · unconfirmed</p>
          <p>{finding.hypothesis}</p>
        </div>
        <p className="field-label">
          Evidence <span>· extracted from this file</span>
        </p>
        <div className="evidence-list">
          {finding.evidence.map((evidence) => (
            <button
              type="button"
              className="evidence"
              key={evidence.line}
              onClick={() => onJump(evidence.line)}
              aria-label={`Go to line ${evidence.line}`}
            >
              <span>L{evidence.line}</span>
              <code>{evidence.text || "(empty line)"}</code>
              <ArrowRight size={14} />
            </button>
          ))}
        </div>
        <p className="field-label">
          Recommended checks <span>· review before running</span>
        </p>
        <ol className="checks">
          {finding.recommended_checks.map((check, i) => (
            <li key={i}>{check}</li>
          ))}
        </ol>
      </div>
    </article>
  );
}

export default function App() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [file, setFile] = useState<File | null>(null);
  const [doc, setDoc] = useState<LogDocument | null>(null);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState("");
  const [examples, setExamples] = useState<Example[]>([]);
  const [examplesError, setExamplesError] = useState(false);
  const [health, setHealth] = useState<Health | null>(null);
  const [backendError, setBackendError] = useState(false);
  const [activeLine, setActiveLine] = useState<number | null>(null);
  const [dragging, setDragging] = useState(false);
  const job = useRef<AbortController | null>(null);
  const input = useRef<HTMLInputElement>(null);
  const busy = phase === "preparing" || phase === "analyzing";

  useEffect(() => {
    let active = true;
    getExamples()
      .then((data) => {
        if (active) setExamples(data);
      })
      .catch(() => {
        if (active) setExamplesError(true);
      });
    getHealth()
      .then((data) => {
        if (active) setHealth(data);
      })
      .catch(() => {
        if (active) setBackendError(true);
      });
    return () => {
      active = false;
      job.current?.abort();
    };
  }, []);

  function reset() {
    job.current?.abort();
    setPhase("idle");
    setFile(null);
    setDoc(null);
    setResult(null);
    setError("");
    setActiveLine(null);
    if (input.current) input.current.value = "";
  }

  function begin() {
    job.current?.abort();
    const controller = new AbortController();
    job.current = controller;
    setError("");
    setResult(null);
    setDoc(null);
    setFile(null);
    setActiveLine(null);
    setPhase("preparing");
    return controller;
  }

  async function prepareFile(selected: File, controller: AbortController) {
    if (!/\.(log|txt)$/i.test(selected.name))
      throw new Error("Choose one .log or .txt file.");
    if (selected.size > 65536)
      throw new Error("The file exceeds 64 KiB (65,536 bytes).");
    setFile(selected);
    const data = await preview(
      selected,
      AbortSignal.any([controller.signal, AbortSignal.timeout(20000)]),
    );
    if (!controller.signal.aborted) {
      setDoc(data);
      setPhase("ready");
    }
  }

  async function selectFiles(files: File[]) {
    const controller = begin();
    try {
      if (files.length !== 1)
        throw new Error("Select exactly one file per analysis.");
      await prepareFile(files[0], controller);
    } catch (error) {
      if (!controller.signal.aborted) {
        setError(messageFor(error));
        setPhase("error");
      }
    }
  }

  async function loadExample(example: Example) {
    const controller = begin();
    try {
      const response = await checked(
        await fetch(`/api/examples/${example.id}`, {
          signal: AbortSignal.any([
            controller.signal,
            AbortSignal.timeout(20000),
          ]),
        }),
      );
      const blob = await response.blob();
      if (!controller.signal.aborted)
        await prepareFile(
          new File([blob], `${example.id}.log`, { type: "text/plain" }),
          controller,
        );
    } catch (error) {
      if (!controller.signal.aborted) {
        setError(messageFor(error));
        setPhase("error");
      }
    }
  }

  async function runAnalysis() {
    if (!file || !doc || busy) return;
    job.current?.abort();
    const controller = new AbortController();
    job.current = controller;
    setPhase("analyzing");
    setError("");
    setResult(null);
    setActiveLine(null);
    try {
      const data = await analyze(
        file,
        AbortSignal.any([controller.signal, AbortSignal.timeout(195000)]),
      );
      if (!controller.signal.aborted) {
        setDoc(data.document);
        setResult(data);
        setPhase("complete");
      }
    } catch (error) {
      if (!controller.signal.aborted) {
        setError(messageFor(error));
        setPhase("error");
      }
    }
  }

  function jumpToLine(n: number) {
    setActiveLine(n);
    const line = document.getElementById(`log-line-${n}`);
    line?.scrollIntoView({ behavior: "smooth", block: "center" });
    line?.focus({ preventScroll: true });
  }

  function download() {
    if (!result) return;
    const url = URL.createObjectURL(
      new Blob([result.markdown], { type: "text/markdown;charset=utf-8" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = `${result.document.filename.replace(/\.[^.]+$/, "").replace(/[^a-z0-9_-]/gi, "_")}-servermedic.md`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="ServerMedic home">
          <span className="brand-icon">
            <Activity size={23} />
          </span>
          ServerMedic<span className="version">MVP / 0.1</span>
        </a>
        <div className="header-right">
          <span className="open-source">Open source log diagnostics</span>
          <span className="local-badge">
            <span /> Session only
          </span>
        </div>
      </header>
      <div className="workspace">
        <aside className="sidebar">
          <div className="section-eyebrow">
            WORKSPACE <span>01</span>
          </div>
          <div className="sidebar-title">
            <FileText size={19} />
            <h2>Log source</h2>
          </div>
          <p className="sidebar-description">
            Start with a small slice of what happened.
          </p>
          <label
            className={`dropzone ${dragging ? "dragging" : ""} ${busy ? "disabled" : ""}`}
            onDragOver={(event) => {
              event.preventDefault();
              if (!busy) setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(event) => {
              event.preventDefault();
              setDragging(false);
              if (!busy) void selectFiles(Array.from(event.dataTransfer.files));
            }}
          >
            <input
              ref={input}
              type="file"
              accept=".log,.txt"
              aria-label="Upload log file"
              disabled={busy}
              onChange={(event) => {
                if (event.target.files?.length)
                  void selectFiles(Array.from(event.target.files));
                event.target.value = "";
              }}
            />
            <span className="upload-icon">
              <Upload size={21} />
            </span>
            <strong>
              {file ? "Choose another file" : "Drop your log here"}
            </strong>
            <span>
              or <u>browse files</u>
            </span>
            <small>.log or .txt · UTF-8</small>
          </label>
          <div className="limits">
            <span>1 file</span>
            <span>64 KiB max</span>
            <span>500 lines max</span>
          </div>
          {file && (
            <div className="selected-file">
              <FileCode2 size={19} />
              <div>
                <strong>{doc?.filename || "Selected file"}</strong>
                <small>
                  {(file.size / 1024).toFixed(1)} KiB
                  {doc ? ` · ${doc.line_count} lines` : ""}
                </small>
              </div>
              <button
                type="button"
                className="icon-button"
                onClick={reset}
                aria-label="Remove file"
              >
                <X size={16} />
              </button>
            </div>
          )}
          <button
            type="button"
            className="analyze-button"
            disabled={!doc || busy}
            onClick={() => void runAnalysis()}
          >
            {busy ? (
              <LoaderCircle size={18} className="spin" />
            ) : (
              <ScanLine size={18} />
            )}
            {phase === "preparing"
              ? "Preparing log…"
              : phase === "analyzing"
                ? "Analyzing log…"
                : phase === "error" && doc
                  ? "Try analysis again"
                  : "Analyze log"}
            {!busy && <ArrowRight size={17} />}
          </button>
          <div className="sample-heading">
            <FlaskConical size={15} />
            <h3>Try a sample</h3>
            <span>4</span>
          </div>
          <div className="sample-list">
            {examples.map((example, i) => (
              <button
                key={example.id}
                type="button"
                onClick={() => void loadExample(example)}
                disabled={busy}
                aria-label={`Load ${example.title} sample`}
              >
                <span
                  className={`sample-marker ${example.id === "healthy" ? "healthy-marker" : ""}`}
                >
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span>
                  <strong>{example.title}</strong>
                  <small>{example.description}</small>
                </span>
                <ArrowRight size={14} />
              </button>
            ))}
          </div>
          {examplesError && (
            <p className="small-error">
              Samples unavailable. Check the backend and reload.
            </p>
          )}
          <div className="privacy-note">
            <LockKeyhole size={17} />
            <div>
              <strong>Review before you send</strong>
              <p>
                Common secret patterns are masked before analysis. Masking is
                best-effort; preview the processed log first.
              </p>
            </div>
          </div>
          <div className="sidebar-bottom">
            <Terminal size={14} />
            <span>Built for the debugging loop.</span>
          </div>
        </aside>
        <main className="main">
          <div className="page-heading">
            <div>
              <div className="section-eyebrow">APPLICATION DIAGNOSTICS</div>
              <h1>A clearer next step.</h1>
              <p>From noisy logs to evidence you can inspect.</p>
            </div>
            <div className="workspace-status">
              <span className={`status-dot ${busy ? "working" : ""}`} />
              {busy
                ? "Working"
                : result
                  ? "Analysis complete"
                  : "Ready for a log"}
            </div>
          </div>
          <div className="pipeline" aria-label="Analysis progress">
            <div className={doc ? "done" : "current"}>
              <span>{doc ? <Check size={13} /> : "1"}</span>Load & mask
            </div>
            <i />
            <div className={result ? "done" : doc ? "current" : ""}>
              <span>{result ? <Check size={13} /> : "2"}</span>Analyze evidence
            </div>
            <i />
            <div className={result ? "current" : ""}>
              <span>3</span>Review & export
            </div>
          </div>
          {health?.provider === "test" && (
            <div className="notice test-notice">
              <FlaskConical size={17} />
              <span>
                Test analyzer · {health.model} · no OpenAI call. Results are
                deterministic fixtures.
              </span>
            </div>
          )}
          {health && !health.analysis_configured && (
            <div className="notice">
              <CircleAlert size={17} />
              <span>
                Preview is available. Set OPENAI_API_KEY and LLM_MODEL on the
                backend to enable AI analysis.
              </span>
            </div>
          )}
          {backendError && (
            <div className="notice">
              <CircleAlert size={17} />
              <span>
                Backend unavailable. Start the service and reload this page.
              </span>
            </div>
          )}
          {error && (
            <div className="error-banner" role="alert">
              <CircleAlert size={20} />
              <div>
                <strong>Could not complete this step</strong>
                <p>{error}</p>
              </div>
              <button
                className="icon-button"
                onClick={() => setError("")}
                aria-label="Dismiss error"
              >
                <X size={16} />
              </button>
            </div>
          )}
          {!doc ? (
            <section className="empty-state" aria-live="polite">
              <div className="empty-grid" aria-hidden="true">
                <div className="empty-terminal">
                  <div>
                    <span />
                    <span />
                    <span />
                  </div>
                  <code>
                    <b>01</b> INFO Application starting
                    <br />
                    <b>02</b> <em>ERROR Something needs a closer look</em>
                    <br />
                    <b>03</b> <span className="terminal-cursor">_</span>
                  </code>
                  <div className="scan-cross">
                    <ScanLine size={28} />
                  </div>
                </div>
              </div>
              <span className="eyebrow-pill">
                LESS GUESSWORK. MORE EVIDENCE.
              </span>
              <h2>
                {phase === "preparing"
                  ? "Preparing your log…"
                  : "Every log tells a story."}
              </h2>
              <p>
                {phase === "preparing"
                  ? "Checking limits and masking common secret patterns."
                  : "Find the signal, inspect the lines, and decide what to check next. Upload a log or explore one of the samples."}
              </p>
              <button
                type="button"
                className="text-button"
                disabled={busy || !examples.length}
                onClick={() => examples[0] && void loadExample(examples[0])}
              >
                Explore a sample log <ArrowRight size={16} />
              </button>
              <div className="empty-features">
                <span>
                  <ShieldCheck size={16} /> Secrets masked
                </span>
                <span>
                  <CheckCheck size={16} /> Evidence linked
                </span>
                <span>
                  <ArrowDownToLine size={16} /> Markdown export
                </span>
              </div>
            </section>
          ) : (
            <div className="analysis-grid">
              <section className="log-panel" aria-label="Processed log viewer">
                <div className="panel-heading">
                  <div>
                    <Terminal size={17} />
                    <h2>Processed log</h2>
                  </div>
                  <span>{doc.line_count} lines</span>
                </div>
                <div className="log-meta">
                  <span title={doc.filename}>{doc.filename}</span>
                  <span>
                    <ShieldCheck size={13} />
                    {doc.redaction_count} masked
                  </span>
                </div>
                <div className="log-viewer" tabIndex={0} aria-label="Log lines">
                  {doc.lines.map((line) => (
                    <div
                      id={`log-line-${line.number}`}
                      key={line.number}
                      tabIndex={-1}
                      data-testid={`log-line-${line.number}`}
                      className={`log-line ${activeLine === line.number ? "active" : ""} ${/\b(ERROR|FATAL)\b/.test(line.text) ? "error-line" : ""}`}
                    >
                      <span className="line-number">{line.number}</span>
                      <code>{line.text || "\u00a0"}</code>
                    </div>
                  ))}
                </div>
                <div className="log-footer">
                  <LockKeyhole size={12} />
                  Full accepted file · original line numbers
                </div>
              </section>
              <section
                className="results-panel"
                aria-label="Analysis results"
                aria-live="polite"
                aria-busy={phase === "analyzing"}
              >
                <div className="panel-heading">
                  <div>
                    <Activity size={17} />
                    <h2>Analysis</h2>
                  </div>
                  {result && (
                    <button
                      type="button"
                      className="export-button"
                      onClick={download}
                    >
                      <ArrowDownToLine size={14} />
                      Download Markdown
                    </button>
                  )}
                </div>
                {!result ? (
                  <div className="result-placeholder">
                    {phase === "analyzing" ? (
                      <LoaderCircle className="spin" size={32} />
                    ) : (
                      <ScanLine size={32} />
                    )}
                    <h3>
                      {phase === "analyzing"
                        ? "Reading between the lines."
                        : "Your next step starts here."}
                    </h3>
                    <p>
                      {phase === "analyzing"
                        ? "Analyzing the full processed log and checking the response. This may take a minute."
                        : "Review the processed log, then run analysis to see observations, possible causes, and suggested checks."}
                    </p>
                    <span>
                      {phase === "analyzing"
                        ? "One request · no commands executed"
                        : "Click Analyze log when you’re ready"}
                    </span>
                  </div>
                ) : (
                  <>
                    <div className="result-summary">
                      <div className="result-kicker">
                        {result.analysis.findings.length ? (
                          <CircleAlert size={16} />
                        ) : (
                          <CircleCheck size={16} />
                        )}
                        {result.analysis.findings.length
                          ? `${result.analysis.findings.length} finding${result.analysis.findings.length === 1 ? "" : "s"} to investigate`
                          : "No problems identified"}
                      </div>
                      <p>{result.analysis.summary}</p>
                      <span>
                        {result.provider} / {result.model}
                      </span>
                    </div>
                    {!result.analysis.findings.length && (
                      <div className="healthy-result">
                        <CircleCheck size={23} />
                        <div>
                          <strong>A clean sample.</strong>
                          <p>
                            No problems were identified in this file. This does
                            not prove the entire system is healthy.
                          </p>
                        </div>
                      </div>
                    )}
                    {result.analysis.findings.map((finding, i) => (
                      <FindingCard
                        key={i}
                        finding={finding}
                        index={i}
                        onJump={jumpToLine}
                      />
                    ))}
                    <div className="context-panel">
                      <h3>What this analysis can’t tell you</h3>
                      <ul>
                        {result.analysis.limitations.map((limitation, i) => (
                          <li key={i}>{limitation}</li>
                        ))}
                      </ul>
                      <h3>Missing context</h3>
                      {result.analysis.missing_context.length ? (
                        <ul>
                          {result.analysis.missing_context.map((context, i) => (
                            <li key={i}>{context}</li>
                          ))}
                        </ul>
                      ) : (
                        <p>None specified by the analyzer.</p>
                      )}
                    </div>
                  </>
                )}
              </section>
            </div>
          )}
          <footer className="main-footer">
            <span>
              <ShieldCheck size={14} /> Observations first. Hypotheses second.
            </span>
            <span>No commands executed · No saved history</span>
          </footer>
        </main>
      </div>
    </div>
  );
}
