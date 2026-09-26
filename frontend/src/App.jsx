import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import ChatPanel from './components/ChatPanel';
import DemoControls from './components/DemoControls';
import MemoryStatus from './components/MemoryStatus';
import GraphInspector from './components/GraphInspector';
import {
  sendChatMessage,
  fetchCustomerGraph,
  seedDemoCustomer,
  resetDemoState
} from './api/client';

export default function App() {
  const [messages, setMessages] = useState([]);
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [lastCypher, setLastCypher] = useState("MATCH (c:Customer {email: 'alice@techcorp.io'}) RETURN c;");
  const [activeContext, setActiveContext] = useState(null);
  const [ticketStatus, setTicketStatus] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [sessionBreakActive, setSessionBreakActive] = useState(false);
  const [showBaseline, setShowBaseline] = useState(false);

  const customerEmail = 'alice@techcorp.io';

  const refreshGraph = async () => {
    try {
      const data = await fetchCustomerGraph(customerEmail);
      setGraphData(data);
    } catch (e) {
      console.error('Failed to refresh graph:', e);
    }
  };

  useEffect(() => {
    refreshGraph();
  }, []);

  // --- Handlers for 1-Click Demo Buttons ---

  // Step 1: Seed
  const handleSeed = async () => {
    setIsProcessing(true);
    try {
      const res = await seedDemoCustomer(customerEmail);
      setLastCypher("MERGE (c:Customer {email: 'alice@techcorp.io'})... MERGE (p:Product {id: 'PROD-GDS-01'})");
      await refreshGraph();
      setCurrentStep(2);
    } catch (e) {
      alert(`Error seeding customer: ${e.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  // Step 2: Send Session 1
  const handleSendSession1 = async () => {
    const s1Text = "Hi, my Graph Data Science workspace is failing with Error 403 on launch.";
    await handleUserMessage(s1Text, 'session-1');
    setCurrentStep(3);
  };

  // Step 3: Simulate Session Break
  const handleSimulateBreak = () => {
    setMessages([]);
    setSessionBreakActive(true);
    setCurrentStep(4);
  };

  // Step 4: Send Session 2 Return
  const handleSendSession2 = async () => {
    setSessionBreakActive(false);
    const s2Text = "It's still not working.";
    await handleUserMessage(s2Text, 'session-2');
    setCurrentStep(5);
  };

  // Step 5: Reset Demo
  const handleReset = async () => {
    setIsProcessing(true);
    try {
      await resetDemoState(customerEmail);
      setMessages([]);
      setActiveContext(null);
      setTicketStatus(null);
      setSessionBreakActive(false);
      setCurrentStep(1);
      setLastCypher("MATCH (c:Customer {email: 'alice@techcorp.io'}) OPTIONAL MATCH ... DETACH DELETE t, i, r, o, int;");
      await refreshGraph();
    } catch (e) {
      alert(`Error resetting demo: ${e.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  // General message sender (for input form or demo triggers)
  const handleUserMessage = async (text, sessionId = 'session-1') => {
    setIsProcessing(true);
    setMessages((prev) => [...prev, { sender: 'user', text }]);

    try {
      const res = await sendChatMessage(customerEmail, text, sessionId);
      setMessages((prev) => [
        ...prev,
        {
          sender: 'agent',
          text: res.reply,
          action: res.action_taken
        }
      ]);
      if (res.executed_cypher_summary) {
        setLastCypher(res.executed_cypher_summary);
      }
      if (res.retrieved_context) {
        setActiveContext(res.retrieved_context);
      }
      if (res.ticket_status) {
        setTicketStatus(res.ticket_status);
      }
      await refreshGraph();
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'agent',
          text: `Error processing message: ${e.message}`,
          action: 'ERROR_OCCURRED'
        }
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* App Header */}
      <Header
        onReset={handleReset}
        isProcessing={isProcessing}
        showBaseline={showBaseline}
        setShowBaseline={setShowBaseline}
      />

      {/* Main Dual-Pane Body */}
      <div className="flex-1 grid grid-cols-12 overflow-hidden">
        {/* Left Pane: Customer Chat (5 cols) */}
        <div className="col-span-5 h-full overflow-hidden">
          <ChatPanel
            messages={messages}
            onSendMessage={(text) => handleUserMessage(text, currentStep >= 4 ? 'session-2' : 'session-1')}
            isProcessing={isProcessing}
            showBaseline={showBaseline}
            sessionBreakActive={sessionBreakActive}
          />
        </div>

        {/* Right Pane: Live Memory & Graph Inspector (7 cols) */}
        <div className="col-span-7 h-full flex flex-col p-3 gap-3 overflow-y-auto bg-slate-950">
          {/* Demo Controls Bar */}
          <DemoControls
            onSeed={handleSeed}
            onSendSession1={handleSendSession1}
            onSimulateBreak={handleSimulateBreak}
            onSendSession2={handleSendSession2}
            onReset={handleReset}
            isProcessing={isProcessing}
            currentStep={currentStep}
          />

          {/* Active Memory Status Indicator */}
          <MemoryStatus
            context={activeContext}
            ticketStatus={ticketStatus}
          />

          {/* Real-time SVG Graph Inspector & Cypher Log */}
          <GraphInspector
            graphData={graphData}
            lastCypher={lastCypher}
            isProcessing={isProcessing}
          />
        </div>
      </div>
    </div>
  );
}
