import React, { useState, useCallback, useEffect } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Panel,
} from '@xyflow/react';
import axios from 'axios';
import '@xyflow/react/dist/style.css';
import './App.css';

// Debug Panel Component
const DebugPanel = ({ debugInfo, isVisible, onToggle }) => {
  if (!isVisible) {
    return (
      <button 
        onClick={onToggle}
        style={{
          position: 'fixed',
          top: '10px',
          right: '10px',
          zIndex: 1000,
          padding: '8px',
          backgroundColor: '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '4px'
        }}
      >
        Show Debug
      </button>
    );
  }

  return (
    <div style={{
      position: 'fixed',
      top: '10px',
      right: '10px',
      width: '300px',
      maxHeight: '400px',
      backgroundColor: 'rgba(0,0,0,0.9)',
      color: '#00ff00',
      padding: '10px',
      borderRadius: '8px',
      fontFamily: 'monospace',
      fontSize: '12px',
      overflow: 'auto',
      zIndex: 1000
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
        <strong>Debug Info</strong>
        <button onClick={onToggle} style={{ 
          background: 'none', 
          border: 'none', 
          color: '#ff6b6b', 
          cursor: 'pointer' 
        }}>
          ✕
        </button>
      </div>
      <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
        {JSON.stringify(debugInfo, null, 2)}
      </pre>
    </div>
  );
};

// Phase Node Component - The "Fat Node" with dual button rows
const PhaseNode = ({ data, id }) => {
  const [loading, setLoading] = useState(false);
  const [showReport, setShowReport] = useState(false);

  const handlePhaseAction = async (actionType) => {
    setLoading(true);
    
    try {
      // Generate context-aware action for this phase
      const nodeSpecificContext = {
        role: data.role || 'General User',
        context: data.context || '',
        current_node_content: data.content || '',
        node_title: data.phase || 'Research',
        parent_content: data.parentContent || '',
        node_type: data.phase.toLowerCase(),
        completed_actions: data.completedActions || [],
        previous_actions: [],
        phase: data.phase,
        action_type: actionType
      };

      // Get AI-generated action for this phase
      const menuResponse = await axios.post('http://localhost:8000/api/generate-menu', nodeSpecificContext);
      
      if (menuResponse.data.menu_items && menuResponse.data.menu_items.length > 0) {
        // Execute the first suggested action automatically
        const selectedAction = menuResponse.data.menu_items[0];
        
        const actionResponse = await axios.post('http://localhost:8000/api/execute-action', {
          action_id: 'generated',
          context: {
            role: data.role,
            action_prompt: selectedAction.prompt,
            context: data.context,
            parent_content: data.content,
            phase: data.phase
          },
          user_input: ''
        });

        // Add result to this node's content (internal accumulation)
        if (data.onContentUpdate) {
          const newResult = `\n\n--- ${selectedAction.title} ---\n${actionResponse.data.result}`;
          data.onContentUpdate(id, newResult);
        }
      }
    } catch (error) {
      console.error('Phase action failed:', error);
      alert('Failed to execute phase action. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  const handleNextPhase = () => {
    if (data.onNextPhase) {
      data.onNextPhase(id, data.phase);
    }
  };

  const handleAddMaterials = () => {
    const userInput = prompt(`Add materials/context for ${data.phase} phase:`);
    if (userInput && data.onContentUpdate) {
      const materialNote = `\n\n--- User Materials ---\n${userInput}`;
      data.onContentUpdate(id, materialNote);
    }
  };

  const getPhaseColor = () => {
    switch (data.phase) {
      case 'Research': return '#e8f4f8';
      case 'Analysis': return '#f0f8e8';
      case 'Strategy': return '#f8f4e8';
      case 'Implementation': return '#f8e8f4';
      default: return '#f0f0f0';
    }
  };

  const getPhaseActions = () => {
    switch (data.phase) {
      case 'Research':
        return [
          { label: 'More Market Research', action: 'market_research' },
          { label: 'Competitor Analysis', action: 'competitor_analysis' },
          { label: 'Customer Insights', action: 'customer_research' }
        ];
      case 'Analysis':
        return [
          { label: 'Synthesize Findings', action: 'synthesis' },
          { label: 'Identify Patterns', action: 'pattern_analysis' },
          { label: 'Draw Insights', action: 'insight_generation' }
        ];
      case 'Strategy':
        return [
          { label: 'Develop Approach', action: 'strategy_development' },
          { label: 'Create Framework', action: 'framework_creation' },
          { label: 'Plan Execution', action: 'execution_planning' }
        ];
      case 'Implementation':
        return [
          { label: 'Create Deliverables', action: 'deliverable_creation' },
          { label: 'Build Assets', action: 'asset_creation' },
          { label: 'Execute Plan', action: 'plan_execution' }
        ];
      default:
        return [];
    }
  };

  const getNextPhase = () => {
    const phases = ['Research', 'Analysis', 'Strategy', 'Implementation'];
    const currentIndex = phases.indexOf(data.phase);
    return currentIndex < phases.length - 1 ? phases[currentIndex + 1] : 'Complete';
  };

  return (
    <div 
      style={{
        padding: '20px',
        border: '3px solid #333',
        borderRadius: '12px',
        background: getPhaseColor(),
        minWidth: '400px',
        maxWidth: '500px',
        position: 'relative',
        boxShadow: '0 4px 16px rgba(0,0,0,0.15)'
      }}
    >
      {/* Phase Header */}
      <div style={{ 
        marginBottom: '15px', 
        textAlign: 'center',
        borderBottom: '2px solid #333',
        paddingBottom: '10px'
      }}>
        <strong style={{ fontSize: '18px', color: '#333' }}>
          {data.phase} Phase
        </strong>
      </div>

      {/* Top Button Row - Phase Actions */}
      <div style={{ 
        display: 'flex', 
        gap: '8px', 
        marginBottom: '15px',
        flexWrap: 'wrap'
      }}>
        {getPhaseActions().map((action, index) => (
          <button
            key={index}
            onClick={() => handlePhaseAction(action.action)}
            disabled={loading}
            style={{
              flex: 1,
              minWidth: '120px',
              padding: '8px 12px',
              background: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '12px',
              fontWeight: 'bold',
              opacity: loading ? 0.6 : 1
            }}
          >
            {action.label}
          </button>
        ))}
      </div>

      {/* Content Area */}
      <div style={{ 
        marginBottom: '15px',
        minHeight: '200px',
        maxHeight: '400px',
        overflow: 'auto',
        padding: '12px',
        background: '#f9f9f9',
        borderRadius: '6px',
        border: '1px solid #ddd',
        fontSize: '12px',
        lineHeight: '1.4',
        whiteSpace: 'pre-wrap',
        userSelect: 'text',
        cursor: 'text'
      }}>
        {data.content || `${data.phase} phase ready. Use the buttons above to generate content.`}
      </div>

      {/* Bottom Button Row - Management Actions */}
      <div style={{ 
        display: 'flex', 
        gap: '10px',
        borderTop: '1px solid #ddd',
        paddingTop: '15px'
      }}>
        <button
          onClick={handleAddMaterials}
          style={{
            flex: 1,
            padding: '10px',
            background: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '13px',
            fontWeight: 'bold'
          }}
        >
          Add Materials
        </button>
        
        <button
          onClick={() => setShowReport(!showReport)}
          style={{
            flex: 1,
            padding: '10px',
            background: '#17a2b8',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '13px',
            fontWeight: 'bold'
          }}
        >
          {showReport ? 'Hide Report' : 'View Report'}
        </button>
        
        <button
          onClick={handleNextPhase}
          disabled={data.phase === 'Implementation'}
          style={{
            flex: 1,
            padding: '10px',
            background: data.phase === 'Implementation' ? '#6c757d' : '#ffc107',
            color: data.phase === 'Implementation' ? 'white' : '#333',
            border: 'none',
            borderRadius: '6px',
            cursor: data.phase === 'Implementation' ? 'not-allowed' : 'pointer',
            fontSize: '13px',
            fontWeight: 'bold'
          }}
        >
          {data.phase === 'Implementation' ? 'Complete' : `→ ${getNextPhase()}`}
        </button>
      </div>

      {/* Loading Overlay */}
      {loading && (
        <div style={{ 
          position: 'absolute', 
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(255,255,255,0.9)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: '12px',
          fontSize: '14px',
          fontWeight: 'bold',
          color: '#333'
        }}>
          AI Processing {data.phase}...
        </div>
      )}

      {/* Report Modal */}
      {showReport && (
        <div style={{
          position: 'fixed',
          top: '10%',
          left: '10%',
          width: '80%',
          height: '80%',
          background: 'white',
          border: '2px solid #333',
          borderRadius: '12px',
          padding: '20px',
          zIndex: 2000,
          boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
          overflow: 'auto'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
            <h3>Phase Report: {data.phase}</h3>
            <button onClick={() => setShowReport(false)} style={{
              background: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              padding: '8px 12px',
              cursor: 'pointer'
            }}>
              Close
            </button>
          </div>
          <pre style={{ 
            whiteSpace: 'pre-wrap', 
            fontSize: '12px', 
            lineHeight: '1.5',
            userSelect: 'text',
            background: '#f8f9fa',
            padding: '15px',
            borderRadius: '6px',
            border: '1px solid #dee2e6'
          }}>
            {data.content || 'No content generated yet.'}
          </pre>
        </div>
      )}
    </div>
  );
};

// Node types for ReactFlow
const nodeTypes = {
  phaseNode: PhaseNode,
};

function App() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [role, setRole] = useState('Marketing Director');
  const [context, setContext] = useState('');
  const [backendStatus, setBackendStatus] = useState('unknown');
  const [debugInfo, setDebugInfo] = useState({});
  const [showDebug, setShowDebug] = useState(false);

  // Check backend connection
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/health');
        setBackendStatus(response.data.status === 'healthy' ? 'connected' : 'error');
      } catch (error) {
        setBackendStatus('disconnected');
      }
    };

    checkBackend();
    const interval = setInterval(checkBackend, 30000);
    return () => clearInterval(interval);
  }, []);

  const onConnect = useCallback((params) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

  // Handle content updates within nodes (internal accumulation)
  const handleContentUpdate = useCallback((nodeId, newContent) => {
    setNodes((currentNodes) =>
      currentNodes.map((node) => {
        if (node.id === nodeId) {
          return {
            ...node,
            data: {
              ...node.data,
              content: (node.data.content || '') + newContent
            }
          };
        }
        return node;
      })
    );

    // Update debug info
    setDebugInfo(prev => ({
      ...prev,
      lastContentUpdate: {
        nodeId,
        contentLength: newContent.length,
        timestamp: new Date().toISOString()
      }
    }));
  }, [setNodes]);

  // Handle phase progression
  const handleNextPhase = useCallback((currentNodeId, currentPhase) => {
  const phases = ['Research', 'Analysis', 'Strategy', 'Implementation'];
  const currentIndex = phases.indexOf(currentPhase);
  
  if (currentIndex >= phases.length - 1) {
    alert('Workflow complete!');
    return;
  }

  const nextPhase = phases[currentIndex + 1];
  
  // Use setNodes callback to get current nodes state
  setNodes((currentNodes) => {
    const currentNode = currentNodes.find(n => n.id === currentNodeId);
    
    if (!currentNode) {
      console.error('Current node not found:', currentNodeId, 'Available nodes:', currentNodes.map(n => n.id));
      return currentNodes; // Return unchanged if node not found
    }

    // Create next phase node
    const newNodeId = `${nextPhase.toLowerCase()}-node`;
    const newNode = {
      id: newNodeId,
      type: 'phaseNode',
      position: { 
        x: currentNode.position.x + 550, 
        y: currentNode.position.y 
      },
      data: {
        phase: nextPhase,
        content: `Context from ${currentPhase}:\n${currentNode.data.content || 'No content'}\n\n--- ${nextPhase} Phase ---\n`,
        role: role,
        context: context,
        parentContent: currentNode.data.content,
        completedActions: [],
        onContentUpdate: handleContentUpdate,
        onNextPhase: handleNextPhase
      }
    };

    return [...currentNodes, newNode];
  });

  // Create edge separately
  const newNodeId = `${nextPhase.toLowerCase()}-node`;
  const newEdge = {
    id: `edge-${currentNodeId}-${newNodeId}`,
    source: currentNodeId,
    target: newNodeId,
    type: 'smoothstep',
    animated: true,
    style: { strokeWidth: 3, stroke: '#333' }
  };

  setEdges(currentEdges => [...currentEdges, newEdge]);

}, [role, context, handleContentUpdate, setNodes, setEdges]);

  const startNewWorkflow = () => {
    if (!context.trim()) {
      alert('Please enter a context for your workflow');
      return;
    }

    // Create research phase node
    const researchNode = {
      id: 'research-node',
      type: 'phaseNode',
      position: { x: 100, y: 100 },
      data: {
        phase: 'Research',
        content: `Initial Context:\nRole: ${role}\nContext: ${context}\n\n--- Research Phase ---\n`,
        role: role,
        context: context,
        parentContent: '',
        completedActions: [],
        onContentUpdate: handleContentUpdate,
        onNextPhase: handleNextPhase
      }
    };

    setNodes([researchNode]);
    setEdges([]);
    
    // Clear debug info for new workflow
    setDebugInfo({
      workflowStarted: new Date().toISOString(),
      role: role,
      context: context,
      currentPhase: 'Research'
    });
  };

  const clearWorkflow = () => {
    setNodes([]);
    setEdges([]);
    setDebugInfo({});
  };

  return (
    <div className="App" style={{ width: '100vw', height: '100vh' }}>
      <div style={{ height: '100%' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
          defaultViewport={{ x: 0, y: 0, zoom: 0.7 }}
        >
          <Controls />
          <MiniMap nodeStrokeWidth={3} />
          <Background variant="dots" gap={16} size={1} />
          
          <Panel position="top-left">
            <div style={{
              background: 'white',
              padding: '20px',
              borderRadius: '12px',
              boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
              minWidth: '320px',
              maxWidth: '400px'
            }}>
              <h3 style={{ margin: '0 0 18px 0', color: '#333' }}>MenuBot 4-Phase Workflow</h3>
              
              <div style={{ marginBottom: '12px' }}>
                <label style={{ display: 'block', marginBottom: '6px', fontWeight: 'bold', fontSize: '13px' }}>
                  Role:
                </label>
                <input
                  type="text"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  placeholder="e.g., Marketing Director"
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid #ddd',
                    borderRadius: '6px',
                    fontSize: '13px'
                  }}
                />
              </div>

              <div style={{ marginBottom: '18px' }}>
                <label style={{ display: 'block', marginBottom: '6px', fontWeight: 'bold', fontSize: '13px' }}>
                  Context:
                </label>
                <textarea
                  value={context}
                  onChange={(e) => setContext(e.target.value)}
                  placeholder="e.g., Planning campaign for premium lingerie"
                  rows="3"
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid #ddd',
                    borderRadius: '6px',
                    resize: 'vertical',
                    fontSize: '13px',
                    lineHeight: '1.4'
                  }}
                />
              </div>

              <div style={{ display: 'flex', gap: '12px', marginBottom: '15px' }}>
                <button
                  onClick={startNewWorkflow}
                  style={{
                    flex: 1,
                    padding: '12px',
                    background: '#007bff',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontWeight: 'bold',
                    fontSize: '13px'
                  }}
                >
                  Start Workflow
                </button>
                
                <button
                  onClick={clearWorkflow}
                  style={{
                    flex: 1,
                    padding: '12px',
                    background: '#dc3545',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontWeight: 'bold',
                    fontSize: '13px'
                  }}
                >
                  Clear
                </button>
              </div>

              <div style={{ 
                fontSize: '12px', 
                color: backendStatus === 'connected' ? '#28a745' : '#dc3545',
                fontWeight: 'bold',
                marginBottom: '12px'
              }}>
                Backend: {backendStatus}
              </div>

              <div style={{ 
                marginTop: '12px', 
                fontSize: '11px', 
                color: '#666',
                borderTop: '1px solid #eee',
                paddingTop: '12px',
                lineHeight: '1.4'
              }}>
                <strong>4-Phase Workflow:</strong><br/>
                Research → Analysis → Strategy → Implementation<br/>
                Each phase accumulates content internally.<br/>
                Use phase buttons to generate content.<br/>
                Progress when ready for next phase.
              </div>
            </div>
          </Panel>
        </ReactFlow>
      </div>
      
      <DebugPanel 
        debugInfo={debugInfo}
        isVisible={showDebug}
        onToggle={() => setShowDebug(!showDebug)}
      />
    </div>
  );
}

export default App;