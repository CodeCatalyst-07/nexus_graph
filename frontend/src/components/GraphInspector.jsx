import React from 'react';
import { Database, Code2, Network, ArrowRight } from 'lucide-react';

export default function GraphInspector({ graphData, lastCypher, isProcessing }) {
  const nodes = graphData?.nodes || [];
  const edges = graphData?.edges || [];

  // Categorize nodes for structured SVG positioning
  const customerNode = nodes.find(n => n.label === 'Customer');
  const productNode = nodes.find(n => n.label === 'Product');
  const ticketNode = nodes.find(n => n.label === 'SupportTicket');
  const issueNode = nodes.find(n => n.label === 'Issue');
  const resolutionNodes = nodes.filter(n => n.label === 'Resolution');
  const outcomeNodes = nodes.filter(n => n.label === 'Outcome');

  // Node position map (SVG coordinate space 600x320)
  const nodePositions = {
    customer: { x: 120, y: 50 },
    product: { x: 480, y: 50 },
    ticket: { x: 300, y: 130 },
    issue: { x: 120, y: 220 },
    res1: { x: 330, y: 220 },
    out1: { x: 330, y: 290 },
    res2: { x: 490, y: 220 },
    out2: { x: 490, y: 290 },
  };

  // Node color helpers
  const getNodeColor = (node) => {
    switch (node.label) {
      case 'Customer':
        return { bg: '#1e3a8a', border: '#3b82f6', text: '#93c5fd' };
      case 'Product':
        return { bg: '#312e81', border: '#6366f1', text: '#c7d2fe' };
      case 'SupportTicket':
        if (node.properties?.status === 'ESCALATED') {
          return { bg: '#7c2d12', border: '#f97316', text: '#fed7aa' };
        }
        if (node.properties?.status === 'RESOLVED') {
          return { bg: '#064e3b', border: '#10b981', text: '#a7f3d0' };
        }
        return { bg: '#713f12', border: '#eab308', text: '#fef08a' };
      case 'Issue':
        return { bg: '#581c87', border: '#a855f7', text: '#e9d5ff' };
      case 'Resolution':
        return { bg: '#1e293b', border: '#64748b', text: '#cbd5e1' };
      case 'Outcome':
        if (node.properties?.status === 'FAILED') {
          return { bg: '#881337', border: '#f43f5e', text: '#fecdd3' };
        }
        if (node.properties?.status === 'SUCCESS') {
          return { bg: '#064e3b', border: '#10b981', text: '#a7f3d0' };
        }
        return { bg: '#334155', border: '#94a3b8', text: '#e2e8f0' };
      default:
        return { bg: '#1e293b', border: '#475569', text: '#e2e8f0' };
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg flex flex-col flex-1 overflow-hidden shadow-sm">
      {/* Header */}
      <div className="px-4 py-2.5 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Network className="w-4 h-4 text-indigo-400" />
          <span className="text-xs font-semibold text-slate-300">Live Neo4j Graph Inspector</span>
        </div>
        <div className="flex items-center gap-3 text-[11px] text-slate-500 font-mono">
          <span>{nodes.length} Nodes</span>
          <span>•</span>
          <span>{edges.length} Edges</span>
        </div>
      </div>

      {/* SVG Canvas Area */}
      <div className="relative flex-1 bg-slate-950/60 p-2 flex items-center justify-center min-h-[280px]">
        {nodes.length === 0 ? (
          <div className="text-center text-slate-500 text-xs">
            <Database className="w-8 h-8 text-slate-700 mx-auto mb-2" />
            <p>Graph canvas empty. Click '[1. Seed Customer]' to initialize nodes.</p>
          </div>
        ) : (
          <svg viewBox="0 0 620 330" className="w-full h-full max-h-[330px]">
            <defs>
              <marker
                id="arrow"
                viewBox="0 0 10 10"
                refX="8"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 1 L 9 5 L 0 9 z" fill="#475569" />
              </marker>
              <marker
                id="arrow-failed"
                viewBox="0 0 10 10"
                refX="8"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 1 L 9 5 L 0 9 z" fill="#f43f5e" />
              </marker>
            </defs>

            {/* Edge Lines */}
            {/* Customer -> Product */}
            {customerNode && productNode && (
              <g>
                <line x1="180" y1="50" x2="420" y2="50" stroke="#334155" strokeWidth="1.5" markerEnd="url(#arrow)" />
                <text x="300" y="44" fill="#64748b" fontSize="9" textAnchor="middle" fontFamily="monospace">PURCHASED</text>
              </g>
            )}

            {/* Customer -> Ticket */}
            {customerNode && ticketNode && (
              <g>
                <line x1="150" y1="75" x2="260" y2="120" stroke="#334155" strokeWidth="1.5" markerEnd="url(#arrow)" />
                <text x="195" y="105" fill="#64748b" fontSize="9" textAnchor="middle" fontFamily="monospace">OPENED_TICKET</text>
              </g>
            )}

            {/* Ticket -> Product */}
            {ticketNode && productNode && (
              <g>
                <line x1="350" y1="120" x2="450" y2="75" stroke="#334155" strokeWidth="1.5" markerEnd="url(#arrow)" />
                <text x="410" y="105" fill="#64748b" fontSize="9" textAnchor="middle" fontFamily="monospace">TARGETS</text>
              </g>
            )}

            {/* Ticket -> Issue */}
            {ticketNode && issueNode && (
              <g>
                <line x1="260" y1="145" x2="160" y2="205" stroke="#334155" strokeWidth="1.5" markerEnd="url(#arrow)" />
                <text x="195" y="180" fill="#64748b" fontSize="9" textAnchor="middle" fontFamily="monospace">EXHIBITS</text>
              </g>
            )}

            {/* Ticket -> Resolution 1 */}
            {ticketNode && resolutionNodes[0] && (
              <g>
                <line x1="300" y1="155" x2="330" y2="200" stroke="#334155" strokeWidth="1.5" markerEnd="url(#arrow)" />
                <text x="330" y="180" fill="#64748b" fontSize="9" textAnchor="middle" fontFamily="monospace">ATTEMPTED</text>
              </g>
            )}

            {/* Resolution 1 -> Outcome 1 */}
            {resolutionNodes[0] && outcomeNodes[0] && (
              <g>
                <line
                  x1="330" y1="240" x2="330" y2="275"
                  stroke={outcomeNodes[0].properties?.status === 'FAILED' ? '#f43f5e' : '#334155'}
                  strokeWidth={outcomeNodes[0].properties?.status === 'FAILED' ? "2" : "1.5"}
                  markerEnd={outcomeNodes[0].properties?.status === 'FAILED' ? "url(#arrow-failed)" : "url(#arrow)"}
                />
                <text x="355" y="260" fill={outcomeNodes[0].properties?.status === 'FAILED' ? '#f43f5e' : '#64748b'} fontSize="8" fontFamily="monospace">HAS_OUTCOME</text>
              </g>
            )}

            {/* Ticket -> Resolution 2 (Tier 2 Escalation) */}
            {ticketNode && resolutionNodes[1] && (
              <g>
                <line x1="350" y1="145" x2="450" y2="205" stroke="#f97316" strokeWidth="2" strokeDasharray="3 3" markerEnd="url(#arrow)" />
                <text x="415" y="180" fill="#f97316" fontSize="9" textAnchor="middle" fontFamily="monospace">ATTEMPTED</text>
              </g>
            )}

            {/* Resolution 2 -> Outcome 2 */}
            {resolutionNodes[1] && outcomeNodes[1] && (
              <g>
                <line x1="490" y1="240" x2="490" y2="275" stroke="#334155" strokeWidth="1.5" markerEnd="url(#arrow)" />
                <text x="515" y="260" fill="#64748b" fontSize="8" fontFamily="monospace">HAS_OUTCOME</text>
              </g>
            )}

            {/* Render Nodes */}
            {/* 1. Customer */}
            {customerNode && (
              <g transform={`translate(${nodePositions.customer.x}, ${nodePositions.customer.y})`}>
                <circle r="26" fill={getNodeColor(customerNode).bg} stroke={getNodeColor(customerNode).border} strokeWidth="2" />
                <text y="-4" fill="#f8fafc" fontSize="10" fontWeight="bold" textAnchor="middle">Alice</text>
                <text y="9" fill={getNodeColor(customerNode).text} fontSize="8" textAnchor="middle" fontFamily="monospace">:Customer</text>
              </g>
            )}

            {/* 2. Product */}
            {productNode && (
              <g transform={`translate(${nodePositions.product.x}, ${nodePositions.product.y})`}>
                <rect x="-65" y="-22" width="130" height="44" rx="8" fill={getNodeColor(productNode).bg} stroke={getNodeColor(productNode).border} strokeWidth="2" />
                <text y="-4" fill="#f8fafc" fontSize="10" fontWeight="bold" textAnchor="middle">GDS Workspace</text>
                <text y="10" fill={getNodeColor(productNode).text} fontSize="8" textAnchor="middle" fontFamily="monospace">:Product (PROD-GDS-01)</text>
              </g>
            )}

            {/* 3. Ticket */}
            {ticketNode && (
              <g transform={`translate(${nodePositions.ticket.x}, ${nodePositions.ticket.y})`}>
                <rect x="-55" y="-22" width="110" height="44" rx="8" fill={getNodeColor(ticketNode).bg} stroke={getNodeColor(ticketNode).border} strokeWidth="2" />
                <text y="-4" fill="#f8fafc" fontSize="10" fontWeight="bold" textAnchor="middle">
                  Ticket #{ticketNode.properties?.id || 'TK-101'}
                </text>
                <text y="10" fill={getNodeColor(ticketNode).text} fontSize="9" fontWeight="bold" textAnchor="middle" fontFamily="monospace">
                  [{ticketNode.properties?.status}]
                </text>
              </g>
            )}

            {/* 4. Issue */}
            {issueNode && (
              <g transform={`translate(${nodePositions.issue.x}, ${nodePositions.issue.y})`}>
                <rect x="-50" y="-20" width="100" height="40" rx="6" fill={getNodeColor(issueNode).bg} stroke={getNodeColor(issueNode).border} strokeWidth="1.5" />
                <text y="-3" fill="#f8fafc" fontSize="10" fontWeight="bold" textAnchor="middle">Error 403</text>
                <text y="10" fill={getNodeColor(issueNode).text} fontSize="8" textAnchor="middle" fontFamily="monospace">:Issue</text>
              </g>
            )}

            {/* 5. Resolution 1 */}
            {resolutionNodes[0] && (
              <g transform={`translate(${nodePositions.res1.x}, ${nodePositions.res1.y})`}>
                <rect x="-55" y="-18" width="110" height="36" rx="6" fill={getNodeColor(resolutionNodes[0]).bg} stroke={getNodeColor(resolutionNodes[0]).border} strokeWidth="1.5" />
                <text y="-2" fill="#f8fafc" fontSize="9" fontWeight="bold" textAnchor="middle">Clear SSO Cache</text>
                <text y="10" fill={getNodeColor(resolutionNodes[0]).text} fontSize="8" textAnchor="middle" fontFamily="monospace">Tier-1 Fix</text>
              </g>
            )}

            {/* 6. Outcome 1 */}
            {outcomeNodes[0] && (
              <g transform={`translate(${nodePositions.out1.x}, ${nodePositions.out1.y})`}>
                <rect
                  x="-45" y="-14" width="90" height="28" rx="6"
                  fill={getNodeColor(outcomeNodes[0]).bg}
                  stroke={getNodeColor(outcomeNodes[0]).border}
                  strokeWidth="2"
                />
                <text y="4" fill={getNodeColor(outcomeNodes[0]).text} fontSize="9" fontWeight="bold" textAnchor="middle" fontFamily="monospace">
                  {outcomeNodes[0].properties?.status === 'FAILED' ? 'FAILED ❌' : 'PENDING ⏳'}
                </text>
              </g>
            )}

            {/* 7. Resolution 2 (Tier 2 Escalation) */}
            {resolutionNodes[1] && (
              <g transform={`translate(${nodePositions.res2.x}, ${nodePositions.res2.y})`}>
                <rect x="-60" y="-18" width="120" height="36" rx="6" fill={getNodeColor(resolutionNodes[1]).bg} stroke={getNodeColor(resolutionNodes[1]).border} strokeWidth="2" />
                <text y="-2" fill="#f8fafc" fontSize="9" fontWeight="bold" textAnchor="middle">Tier-2 Escalation</text>
                <text y="10" fill={getNodeColor(resolutionNodes[1]).text} fontSize="8" textAnchor="middle" fontFamily="monospace">License Refresh</text>
              </g>
            )}

            {/* 8. Outcome 2 */}
            {outcomeNodes[1] && (
              <g transform={`translate(${nodePositions.out2.x}, ${nodePositions.out2.y})`}>
                <rect x="-45" y="-14" width="90" height="28" rx="6" fill={getNodeColor(outcomeNodes[1]).bg} stroke={getNodeColor(outcomeNodes[1]).border} strokeWidth="1.5" />
                <text y="4" fill={getNodeColor(outcomeNodes[1]).text} fontSize="9" fontWeight="bold" textAnchor="middle" fontFamily="monospace">
                  QUEUED ⏳
                </text>
              </g>
            )}
          </svg>
        )}
      </div>

      {/* Executed Cypher Query Box */}
      <div className="bg-slate-900 border-t border-slate-800 p-3">
        <div className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-400 mb-1">
          <Code2 className="w-3.5 h-3.5 text-indigo-400" />
          <span>Last Executed Parameterized Cypher:</span>
        </div>
        <pre className="bg-slate-950 p-2.5 rounded border border-slate-800 text-[11px] font-mono text-emerald-400 overflow-x-auto whitespace-pre-wrap max-h-20 select-all">
          {lastCypher || "MATCH (c:Customer {email: 'alice@techcorp.io'}) RETURN c;"}
        </pre>
      </div>
    </div>
  );
}
