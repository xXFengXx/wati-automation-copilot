import { useEffect, useMemo } from 'react';
import { Background, Controls, Handle, MiniMap, Position, ReactFlow, useReactFlow, useViewportStore, type Node, type NodeProps, type NodeTypes } from '@xyflow/react';
import dagre from '@dagrejs/dagre';
import { ArrowRightLeft, CircleCheck, Clock3, GitBranch, Globe, MessageCircle, MessagesSquare, Users, Zap } from 'lucide-react';
import type { Flow, FlowNode, Simulation } from './types';
import '@xyflow/react/dist/style.css';

export const nodeNames: Record<string, string> = {trigger: 'Trigger', send_message: 'Send message', ask_question: 'Ask question', condition: 'Condition', api_call: 'API call', assign_team: 'Assign to team', wait: 'Wait', end: 'End'};
const icons = {trigger: Zap, send_message: MessageCircle, ask_question: MessagesSquare, condition: GitBranch, api_call: Globe, assign_team: Users, wait: Clock3, end: CircleCheck};
export function NodeIcon({type, size = 16}: {type: string; size?: number}) { const Icon = icons[type as keyof typeof icons] || ArrowRightLeft; return <Icon size={size}/>; }

type CardData = {node: FlowNode; handles: string[]; active: boolean; visited: boolean};
function FlowCard({data}: NodeProps<Node<CardData>>) {
  const n = data.node;
  return <div className={`flow-card kind-${n.type} ${data.active ? 'active' : ''} ${data.visited ? 'visited' : ''}`}>
    {n.type !== 'trigger' && <Handle type="target" position={Position.Top}/>}
    <div className="node-category"><span className="node-icon"><NodeIcon type={n.type}/></span>{nodeNames[n.type]}{data.visited && <CircleCheck className="node-done" size={13}/>}</div>
    <strong>{n.label}</strong>
    {data.handles.map((handle, index) => <Handle key={handle} id={handle} type="source" position={Position.Bottom} style={{left: `${(index + 1) / (data.handles.length + 1) * 100}%`}}/>)}
  </div>;
}
const nodeTypes: NodeTypes = {flowCard: FlowCard};

function FitOnResize() {
  const width = useViewportStore(state => state.width);
  const height = useViewportStore(state => state.height);
  const {fitBounds, getNodesBounds, getNodes} = useReactFlow();
  useEffect(() => {
    if (!width || !height || !getNodes().length) return;
    // fitView queues a node update in React Flow 13. This read-only controlled
    // graph has no node-change handler. Its dimensions are fixed explicitly, so
    // fitBounds can update the viewport without waiting for measured node state.
    const frame = requestAnimationFrame(() => { void fitBounds(getNodesBounds(getNodes()), {padding: 32}); });
    return () => cancelAnimationFrame(frame);
  }, [width, height, fitBounds, getNodesBounds, getNodes]);
  return null;
}

export default function FlowCanvas({flow, simulation, selected, onSelect}: {flow: Flow; simulation: Simulation | null; selected: string | null; onSelect: (id: string) => void}) {
  const {nodes, edges} = useMemo(() => {
    const graph = new dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));
    graph.setGraph({rankdir: 'TB', nodesep: 55, ranksep: 80, marginx: 40, marginy: 40});
    const nodeIds = new Set(flow.nodes.map(n => n.id));
    const validEdges = flow.edges.filter(e => nodeIds.has(e.source) && nodeIds.has(e.target));
    flow.nodes.forEach(n => graph.setNode(n.id, {width: 220, height: 88}));
    validEdges.forEach(e => graph.setEdge(e.source, e.target));
    dagre.layout(graph);
    return {
      nodes: flow.nodes.map(n => ({id: n.id, type: 'flowCard', width: 220, height: 88, position: {x: graph.node(n.id).x - 110, y: graph.node(n.id).y - 44}, selected: n.id === selected, data: {node: n, handles: [...new Set(validEdges.filter(e => e.source === n.id).sort((a, b) => (graph.node(a.target)?.x || 0) - (graph.node(b.target)?.x || 0)).map(e => e.handle))], active: simulation?.current_node_id === n.id, visited: simulation?.visited_node_ids.includes(n.id) || false}})),
      edges: validEdges.map((e, i) => {
        const followed = simulation?.trace.some((t, index, trace) => t.node_id === e.source && trace[index + 1]?.node_id === e.target);
        return {id: `edge-${i}`, source: e.source, target: e.target, sourceHandle: e.handle, label: e.handle === 'next' ? '' : e.handle, type: 'smoothstep', animated: followed, style: {stroke: followed ? '#14946c' : '#bac8c2', strokeWidth: followed ? 2.5 : 1.5}, labelStyle: {fill: '#52685f', fontSize: 11}, labelBgStyle: {fill: '#f6f9f7', fillOpacity: 1}};
      }),
    };
  }, [flow, simulation, selected]);
  // Invalid duplicate IDs can be inspected as JSON; never feed them to the graph renderer.
  if (new Set(flow.nodes.map(n => n.id)).size !== flow.nodes.length) return <div className="empty-state">Duplicate node IDs prevent graph display. Inspect JSON and validation findings.</div>;
  return <ReactFlow style={{position: 'absolute', inset: 0}} key={flow.name + flow.nodes.map(n => n.id).join(',')} nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView fitViewOptions={{padding: 32, maxZoom: 1}} minZoom={.15} maxZoom={1.6} nodesDraggable={false} nodesConnectable={false} edgesReconnectable={false} onNodeClick={(_, n) => onSelect(n.id)} proOptions={{hideAttribution: false}}><FitOnResize/><Background color="#d5e0db" gap={22}/><Controls showInteractive={false} fitViewOptions={{padding: 32}}/><MiniMap pannable zoomable nodeColor="#b8d8c9" maskColor="rgba(245,249,247,.75)"/></ReactFlow>;
}
