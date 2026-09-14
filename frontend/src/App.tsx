import { useEffect, useState } from "react";

interface Summary {
  companies: number;
  contacts: number;
  opportunities: number;
  activity_log_entries: number;
}

type LoadState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; summary: Summary };

export default function App() {
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;

    fetch("/api/summary")
      .then((res) => {
        if (!res.ok) throw new Error(`Request failed: ${res.status}`);
        return res.json() as Promise<Summary>;
      })
      .then((summary) => {
        if (!cancelled) setState({ status: "ready", summary });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setState({
            status: "error",
            message: err instanceof Error ? err.message : "Unknown error",
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", padding: "2rem" }}>
      <h1>Exhibition Sales CRM</h1>
      {state.status === "loading" && <p>Loading imported archive summary…</p>}
      {state.status === "error" && (
        <p style={{ color: "crimson" }}>Failed to reach the API: {state.message}</p>
      )}
      {state.status === "ready" && (
        <ul>
          <li>Companies: {state.summary.companies}</li>
          <li>Contacts: {state.summary.contacts}</li>
          <li>Opportunities: {state.summary.opportunities}</li>
          <li>Activity log entries: {state.summary.activity_log_entries}</li>
        </ul>
      )}
    </main>
  );
}
