export type FlowNode = {
  id: string; type: string; label: string;
  event?: string; message?: string; question?: string; variable?: string;
  choices?: string[]; timeout_seconds?: number | null; operator?: string;
  value?: string | number | boolean | null; url?: string; method?: string;
  save_as?: string; mock_response?: Record<string, unknown>; team?: string; duration_seconds?: number;
};
export type Flow = { name: string; description: string; nodes: FlowNode[]; edges: {source: string; target: string; handle: string}[] };
export type Finding = { severity: 'error' | 'warning'; code: string; message: string; node_id: string | null };
export type FlowRecord = {id: string; flow: Flow; prompt: string; explanation: string; findings: Finding[]; valid: boolean; provider: string; model: string};
export type GenerationResult = (FlowRecord & {status: 'generated'}) | {status: 'needs_clarification'; explanation: string; clarification_questions: string[]};
export type Simulation = {
  id: string; flow_id: string; scenario: string; status: 'running' | 'waiting' | 'completed' | 'failed';
  current_node_id: string; variables: Record<string, unknown>; revision: number;
  visited_node_ids: string[]; elapsed_seconds: number; steps: number; error?: string;
  transcript: {role: string; content: string; node_id: string; at_seconds: number}[];
  trace: {node_id: string; label: string; type: string; at_seconds: number; detail: string}[];
  question?: {text: string; choices: string[]; timeout_seconds: number | null} | null;
};
export type Health = {model_configured: boolean; model: string; provider: string};

export async function api<T>(path: string, body?: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch('/api' + path, body === undefined ? undefined : {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
  } catch {
    throw new Error('Cannot reach the backend. Make sure the Python server is running.');
  }
  let result;
  try { result = await response.json(); } catch { throw new Error('The backend returned an unreadable response. Check that the Python server is running.'); }
  if (!response.ok) {
    const detail = result.detail;
    const message = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map((x: {msg: string}) => x.msg).join('; ') : detail?.message;
    throw new Error(message || 'The request failed. Please retry.');
  }
  return result as T;
}
