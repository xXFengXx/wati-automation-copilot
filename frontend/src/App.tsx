import { useEffect, useRef, useState } from 'react';
import { ArrowDown, ArrowRight, Check, CheckCheck, ChevronRight, CircleAlert, CircleCheck, Code2, Download, GitBranch, Info, LoaderCircle, MessageCircle, Play, Plus, RotateCcw, Send, ShieldCheck, Sparkles, Workflow, X, Zap } from 'lucide-react';
import FlowCanvas, { NodeIcon, nodeNames } from './FlowCanvas';
import { api, type FlowRecord, type GenerationResult, type Health, type Simulation } from './types';

const examples = [
  {label: 'Qualify & route', category: 'Sales', prompt: 'When a new contact messages us, ask whether they are a buyer or seller, with buyer and seller as the allowed answers. Route buyers to the Sales team. Send sellers our help article at https://example.com/help. Then end the conversation.'},
  {label: 'Follow up gently', category: 'Engagement', prompt: 'When a new contact messages us, ask if they would like a product demo, with yes and no as the allowed answers. If yes, wait 30 minutes, then send a friendly demo reminder. If no, send a polite thank-you. If they do not answer within 1 hour, send a gentle follow-up and end. End after each path.'},
  {label: 'Handle API failures', category: 'Support', prompt: 'When a contact asks about an order, ask for their order ID as free text. Query GET https://example.com/orders/{order_id}. For the simulated success response, use status="in transit" and tell the customer the status. If the API fails, apologize and assign the conversation to the Support team. Then end.'},
];

function duration(seconds: number) {
  if (seconds >= 3600) return `${+(seconds / 3600).toFixed(1)}h`;
  if (seconds >= 60) return `${+(seconds / 60).toFixed(1)}m`;
  return `${seconds}s`;
}

export default function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [connectionError, setConnectionError] = useState('');
  const [prompt, setPrompt] = useState(examples[0].prompt);
  const [record, setRecord] = useState<FlowRecord | null>(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const [clarifications, setClarifications] = useState<string[]>([]);
  const [clarificationContext, setClarificationContext] = useState('');
  const [tab, setTab] = useState<'flow' | 'review' | 'json'>('flow');
  const [selected, setSelected] = useState<string | null>(null);
  const [simulation, setSimulation] = useState<Simulation | null>(null);
  const [scenario, setScenario] = useState('success');
  const [simBusy, setSimBusy] = useState(false);
  const [simError, setSimError] = useState('');
  const [reply, setReply] = useState('');
  const [simTab, setSimTab] = useState<'chat' | 'trace'>('chat');
  const chatEnd = useRef<HTMLDivElement>(null);
  const errors = record?.findings.filter(f => f.severity === 'error') || [];
  const warnings = record?.findings.filter(f => f.severity === 'warning') || [];
  const selectedNode = record?.flow.nodes.find(n => n.id === selected);

  function checkHealth() {
    setConnectionError('');
    api<Health>('/health').then(setHealth).catch(e => {setHealth(null); setConnectionError(e.message);});
  }
  useEffect(checkHealth, []);
  useEffect(() => {chatEnd.current?.scrollIntoView({block: 'nearest', behavior: 'smooth'});}, [simulation, simTab]);

  async function generate() {
    setGenerating(true); setError(''); setClarifications([]); setSelected(null);
    try {
      const result = await api<GenerationResult>('/flows/generate', {prompt});
      setSimulation(null); setSimError(''); setReply('');
      if (result.status === 'needs_clarification') {
        setRecord(null); setClarifications(result.clarification_questions); setClarificationContext(result.explanation);
      } else {
        setRecord(result); setTab(result.valid ? 'flow' : 'review');
      }
    } catch (e) {setError((e as Error).message);} finally {setGenerating(false);}
  }
  async function startSimulation() {
    if (!record) return;
    setSimBusy(true); setSimError(''); setReply('');
    try {setSimulation(await api<Simulation>('/simulations', {flow_id: record.id, scenario})); setSimTab('chat');}
    catch (e) {setSimError((e as Error).message);} finally {setSimBusy(false);}
  }
  async function sendAnswer(text: string, timeout = false) {
    if (!simulation) return;
    setSimBusy(true); setSimError('');
    try {setSimulation(await api<Simulation>(`/simulations/${simulation.id}/answers`, {answer: timeout ? null : text, timeout, expected_revision: simulation.revision})); setReply('');}
    catch (e) {setSimError((e as Error).message);} finally {setSimBusy(false);}
  }
  function download() {
    if (!record) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(record.flow, null, 2)], {type: 'application/json'}));
    const a = document.createElement('a'); a.href = url; a.download = 'automation-flow.json'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  return <div className="app-shell">
    <header className="topbar">
      <a className="brand" href="/" aria-label="Wati Copilot home"><span className="brand-mark"><MessageCircle size={25} strokeWidth={2.5}/></span><span>wati<span className="brand-dot">.</span></span></a>
      <span className="top-divider"/><span className="product-name">Automation Copilot</span><span className="beta">LABS</span>
      <div className="header-right"><button className={`connection ${health?.model_configured ? 'online' : ''}`} onClick={checkHealth} title="Refresh model connection status"><span className="status-dot"/>{health?.model_configured ? 'DeepSeek configured' : 'Connect DeepSeek'}</button><span className="avatar">W</span></div>
    </header>
    <div className="workspace-heading"><div><div className="breadcrumb">Workspace <ChevronRight size={13}/> Automation builder</div><h1>From an idea to a conversation<span>.</span></h1><p>Describe what you need. Build a flow. See it in action.</p></div><div className="workspace-tag"><ShieldCheck size={15}/> Safe simulation workspace</div></div>
    <main className="builder">
      <aside className="composer panel">
        <div className="section-label"><span className="step-number">01</span> THE INTENT</div>
        <h2>What should happen?</h2><p className="muted intro">Tell your copilot how the conversation should go.</p>
        <label htmlFor="intent" className="field-label">Describe your automation</label>
        <div className="prompt-box"><textarea id="intent" value={prompt} onChange={e => setPrompt(e.target.value)} maxLength={6000} disabled={generating} spellCheck={false}/><div className="prompt-foot"><Sparkles size={13}/><span>Natural language, real possibilities</span><span>{prompt.length}/6000</span></div></div>
        <button className="primary generate" onClick={generate} disabled={generating || simBusy || prompt.trim().length < 10 || !health?.model_configured}>{generating ? <LoaderCircle className="spin" size={17}/> : <Sparkles size={17}/>} {generating ? 'Building your flow…' : record ? 'Regenerate flow' : 'Generate flow'}{!generating && <ArrowRight size={16}/>}</button>
        <div className="model-note"><span className="tiny-dot"/> Powered by real DeepSeek inference</div>
        {connectionError && <div className="notice error" role="alert">{connectionError}<button className="text-button" onClick={checkHealth}>Retry connection</button></div>}
        {health && !health.model_configured && <div className="notice setup"><Info size={16}/><div><strong>Connect your model to begin</strong><p>Add your DeepSeek key to the local <code>.env</code> file and restart the backend. Refresh the connection status above.</p></div></div>}
        {error && <div className="notice error" role="alert"><CircleAlert size={16}/><div>{error}{record && <p>The previous flow is still displayed.</p>}</div></div>}
        <div className="examples-title">A LITTLE INSPIRATION</div>
        <div className="examples">{examples.map((example, i) => <button disabled={generating} key={example.label} className={`example ${prompt === example.prompt ? 'chosen' : ''}`} onClick={() => setPrompt(example.prompt)}><span className={`example-icon example-${i}`}>{i === 0 ? <GitBranch size={17}/> : i === 1 ? <MessageCircle size={17}/> : <Zap size={17}/>}</span><span><strong>{example.label}</strong><small>{example.category}</small></span><ChevronRight size={14}/></button>)}</div>
        <div className="composer-tip"><span>✳</span><p>Great flows start with a trigger, a clear question, and a next step for every answer.</p></div>
        <div className="composer-footer"><ShieldCheck size={14}/> Your business actions stay simulated.</div>
      </aside>

      <section className="flow-panel panel" aria-label="Flow workspace">
        <div className="flow-toolbar"><div className="section-label"><span className="step-number">02</span> THE FLOW</div><button className="icon-button" disabled={!record || generating} onClick={download} aria-label="Download flow JSON" title="Download flow JSON"><Download size={16}/></button></div>
        <div className="flow-title"><h2>{record?.flow.name || 'Your next great conversation'}</h2><span className="count-badge">{record ? `${record.flow.nodes.length} nodes` : 'Ready to build'}</span></div>
        <nav className="tabs" aria-label="Flow views"><button className={tab === 'flow' ? 'selected' : ''} onClick={() => setTab('flow')}><Workflow size={15}/> Flow</button><button className={tab === 'review' ? 'selected' : ''} onClick={() => setTab('review')}><ShieldCheck size={15}/> Review{record && <span className={`tab-count ${errors.length ? 'bad' : ''}`}>{record.findings.length || <Check size={10}/>}</span>}</button><button className={tab === 'json' ? 'selected' : ''} onClick={() => setTab('json')}><Code2 size={15}/> JSON</button>{record && <span className={`validation-status ${record.valid ? 'valid' : 'invalid'}`}>{record.valid ? <CircleCheck size={12}/> : <CircleAlert size={12}/>} {record.valid ? 'Validated' : 'Needs attention'}</span>}</nav>
        <div className="flow-content">
          {generating ? <div className="empty-state generating"><div className="empty-symbol"><Sparkles size={30}/></div><h3>Connecting the dots</h3><p>DeepSeek is turning your intent into a structured flow.</p><div className="loading-bar"/><small>Generating nodes · checking structure · explaining the logic</small></div> : clarifications.length ? <div className="clarification"><span className="clarification-icon"><MessageCircle size={25}/></span><h3>A few details will make this work.</h3><p>{clarificationContext}</p><ol>{clarifications.map(q => <li key={q}>{q}</li>)}</ol><div className="notice"><Info size={16}/> Add these details to your description, then generate again.</div></div> : !record ? <div className="empty-state"><div className="empty-illustration"><div className="ghost-node"><Zap size={14}/><span>A conversation begins</span></div><span className="ghost-line"/><div className="ghost-node hero"><Sparkles size={18}/><span>Your idea goes here</span></div><span className="ghost-line"/><div className="ghost-branches"><div><MessageCircle size={14}/></div><div><UsersIcon/></div></div></div><span className="eyebrow">A CLEAR PATH, EVERY TIME</span><h3>Good conversations<br/>start with a simple idea.</h3><p>Describe your automation on the left.<br/>Your connected flow will take shape here.</p></div> : tab === 'flow' ? <FlowCanvas key={record.id} flow={record.flow} simulation={simulation} selected={selected} onSelect={setSelected}/> : tab === 'json' ? <pre className="json-view">{JSON.stringify(record.flow, null, 2)}</pre> : <div className="review-view"><div className={`review-summary ${errors.length ? 'has-errors' : ''}`}><ShieldCheck size={25}/><div><h3>{errors.length ? `${errors.length} blocking issue${errors.length === 1 ? '' : 's'}` : 'Structure looks good'}</h3><p>{errors.length ? 'Update your description and regenerate before simulation.' : `${warnings.length} advisory finding${warnings.length === 1 ? '' : 's'} to review before a real deployment.`}</p></div></div>{record.findings.length === 0 && <p className="muted">No structural issues or configured risk rules were triggered.</p>}{record.findings.map((f, i) => <button className={`finding ${f.severity}`} key={i} onClick={() => {if (f.node_id) {setSelected(f.node_id); setTab('flow');}}}><span>{f.severity === 'error' ? <CircleAlert size={17}/> : <Info size={17}/>}</span><div><strong>{f.code.replaceAll('_', ' ')}</strong><p>{f.message}</p>{f.node_id && <small>Node: {f.node_id} <ArrowRight size={10}/></small>}</div></button>)}</div>}
        </div>
        <div className="explanation"><div className="explanation-heading"><span>{selectedNode ? <NodeIcon type={selectedNode.type}/> : <Sparkles size={15}/>} {selectedNode ? `${nodeNames[selectedNode.type]} · ${selectedNode.label}` : 'THE LOGIC, IN PLAIN ENGLISH'}</span>{selectedNode && <button className="icon-button" aria-label="Close node details" onClick={() => setSelected(null)}><X size={14}/></button>}</div>{selectedNode ? <dl className="node-details">{Object.entries(selectedNode).filter(([key]) => !['type', 'label', 'id'].includes(key)).map(([key, value]) => <div key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</dd></div>)}</dl> : <p>{record?.explanation || 'Once your flow is generated, your copilot will explain the paths, decisions, and timing here.'}</p>}</div>
      </section>

      <aside className="simulator panel" aria-label="Conversation simulator">
        <div className="section-label"><span className="step-number">03</span> THE TEST DRIVE</div><div className="sim-heading"><h2>Try the conversation</h2><span className="mock-badge">SIMULATION</span></div><p className="muted intro">Walk in your customer’s shoes.</p>
        <div className="scenario-row"><label htmlFor="scenario">Business API outcome</label><select id="scenario" value={scenario} onChange={e => setScenario(e.target.value)} disabled={simBusy || generating}><option value="success">Success</option><option value="api_failure">Failure</option></select></div>
        <button className="secondary start-button" disabled={!record?.valid || simBusy || generating} onClick={startSimulation}>{simBusy ? <LoaderCircle className="spin" size={15}/> : simulation ? <RotateCcw size={15}/> : <Play size={15}/>} {simulation ? 'Restart simulation' : 'Start simulation'}</button>
        <div className="chat-top"><div className="chat-avatar"><MessageCircle size={18}/></div><div><strong>Your automation</strong><small><span className="tiny-dot"/>{simulation ? simulation.status === 'waiting' ? 'Waiting for your reply' : simulation.status === 'completed' ? 'Conversation complete' : simulation.status : 'Ready when you are'}</small></div><span className="virtual-clock">+{duration(simulation?.elapsed_seconds || 0)}</span></div>
        <div className="sim-tabs"><button className={simTab === 'chat' ? 'selected' : ''} onClick={() => setSimTab('chat')}>Conversation</button><button className={simTab === 'trace' ? 'selected' : ''} onClick={() => setSimTab('trace')}>Execution trace {simulation && <span>{simulation.steps}</span>}</button></div>
        <div className="chat-body" aria-live="polite">{!simulation ? <div className="chat-empty"><span className="chat-empty-icon"><MessagesIcon/></span><h3>A little rehearsal.<br/>A lot more confidence.</h3><p>Generate a valid flow, then start<br/>a conversation to test its paths.</p></div> : simTab === 'trace' ? <div className="trace-list">{simulation.trace.map((entry, i) => <div className="trace-entry" key={i}><span className="trace-dot"><NodeIcon type={entry.type} size={12}/></span><div><strong>{entry.label}</strong><small>+{duration(entry.at_seconds)} · {nodeNames[entry.type]}</small><p>{entry.detail}</p></div></div>)}<details className="variables"><summary>Collected variables</summary><pre>{JSON.stringify(simulation.variables, null, 2)}</pre></details></div> : <><div className="chat-date">TEST CONVERSATION · {simulation.scenario === 'api_failure' ? 'API FAILURE' : 'API SUCCESS'}</div>{simulation.transcript.map((message, i) => message.role === 'system' ? <div className="system-message" key={i}><Info size={12}/><span>{message.content}</span></div> : <div className={`chat-message ${message.role}`} key={i}><div>{message.content}</div><small>{message.role === 'bot' ? 'Automation' : 'You'} · +{duration(message.at_seconds)}{message.role === 'user' && <CheckCheck size={12}/>}</small></div>)}{simulation.status === 'completed' && <div className="conversation-complete"><CircleCheck size={14}/> Flow completed</div>}{simulation.status === 'failed' && <div className="notice error">{simulation.error}</div>}</>}<div ref={chatEnd}/></div>
        {simError && <div className="sim-error" role="alert">{simError}</div>}
        <div className="reply-area">{simulation?.status === 'waiting' && simulation.question?.choices && simulation.question.choices.length > 0 && <div className="reply-choices">{simulation.question.choices.map(choice => <button key={choice} disabled={simBusy || generating} onClick={() => sendAnswer(choice)}>{choice}</button>)}</div>}<form onSubmit={e => {e.preventDefault(); sendAnswer(reply);}}><input aria-label="Your reply" placeholder={simulation?.status === 'waiting' ? 'Type your reply…' : 'Start a simulation to reply'} value={reply} onChange={e => setReply(e.target.value)} disabled={simulation?.status !== 'waiting' || simBusy || generating} maxLength={2000}/><button aria-label="Send reply" disabled={!reply.trim() || simulation?.status !== 'waiting' || simBusy || generating}><Send size={16}/></button></form>{simulation?.status === 'waiting' && simulation.question?.timeout_seconds && <button className="timeout-button" disabled={simBusy || generating} onClick={() => sendAnswer('', true)}>Simulate no reply for {duration(simulation.question.timeout_seconds)} <ArrowRight size={12}/></button>}</div>
        <div className="simulation-note"><Info size={12}/> API calls, assignments & waits are simulated.</div>
      </aside>
    </main>
    <footer className="page-footer"><span><span className="tiny-dot"/> BUILT FOR BETTER CONVERSATIONS</span><span>Real AI generation. A safe place to experiment.</span></footer>
  </div>;
}

function UsersIcon() {return <GitBranch size={14}/>;}
function MessagesIcon() {return <><MessageCircle size={26}/><Plus size={13}/></>;}
