"""
Production GUI/Dashboard - SuperAGI-inspired web interface

Provides a web-based dashboard for monitoring and controlling the agent system.
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import logging
import os
from typing import Optional

from nexusforge.core.nexus import NexusForge


class NexusDashboard:
    """
    Web-based dashboard for NexusForge
    
    Provides real-time monitoring, control, and visualization of the agent system.
    Inspired by SuperAGI's production GUI.
    """
    
    def __init__(self, nexus: NexusForge, host: str = "0.0.0.0", port: int = 8080):
        self.nexus = nexus
        self.host = host
        self.port = port
        
        # Initialize Flask app
        self.app = Flask(__name__, static_folder='static', static_url_path='')
        CORS(self.app)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        self.logger = logging.getLogger("NexusDashboard")
        
        # Set up routes
        self._setup_routes()
        self._setup_socketio_handlers()
    
    def _setup_routes(self):
        """Set up Flask routes"""
        
        @self.app.route('/')
        def index():
            """Serve the main dashboard page"""
            return self._get_dashboard_html()
        
        @self.app.route('/health')
        def health():
            """Health check endpoint"""
            return jsonify({"status": "healthy", "running": self.nexus.running})
        
        @self.app.route('/api/status')
        def get_status():
            """Get system status"""
            return jsonify(self.nexus.get_system_status())
        
        @self.app.route('/api/statistics')
        def get_statistics():
            """Get detailed statistics"""
            return jsonify(self.nexus.get_statistics())
        
        @self.app.route('/api/agents')
        def get_agents():
            """Get all agents"""
            agents = [
                {
                    "agent_id": agent.agent_id,
                    "name": agent.state.name,
                    "role": agent.state.role,
                    "depth": agent.depth,
                    "status": agent.state.status,
                    "goals": agent.state.goals,
                    "children_count": len(agent.children)
                }
                for agent in self.nexus.get_all_agents()
            ]
            return jsonify({"agents": agents})
        
        @self.app.route('/api/agents/<agent_id>')
        def get_agent(agent_id):
            """Get specific agent details"""
            agent = self.nexus.get_agent(agent_id)
            if not agent:
                return jsonify({"error": "Agent not found"}), 404
            
            return jsonify({
                "agent_id": agent.agent_id,
                "name": agent.state.name,
                "role": agent.state.role,
                "depth": agent.depth,
                "status": agent.state.status,
                "goals": agent.state.goals,
                "capabilities": agent.template.capabilities,
                "parent_id": agent.parent_id,
                "children": [child.agent_id for child in agent.children],
                "created_at": agent.state.created_at.isoformat()
            })
        
        @self.app.route('/api/hierarchy')
        def get_hierarchy():
            """Get agent hierarchy"""
            root_id = request.args.get('root_id')
            return jsonify(self.nexus.get_agent_hierarchy(root_id))
        
        @self.app.route('/api/crews')
        def get_crews():
            """Get all crews"""
            crews = [
                {
                    "crew_id": crew.crew_id,
                    "name": crew.name,
                    "leader_id": crew.leader_id,
                    "member_count": len(crew.members),
                    "status": crew.status,
                    "goals": crew.goals
                }
                for crew in self.nexus.crew_manager.get_all_crews()
            ]
            return jsonify({"crews": crews})
        
        @self.app.route('/api/experts')
        def get_experts():
            """Get all experts"""
            experts = [
                {
                    "expert_id": expert.expert_id,
                    "name": expert.name,
                    "modality": expert.modality.value,
                    "specializations": expert.specializations,
                    "capabilities": expert.capabilities
                }
                for expert in self.nexus.expert_system.get_all_experts()
            ]
            return jsonify({"experts": experts})
        
        @self.app.route('/api/messages')
        def get_messages():
            """Get message history"""
            agent_id = request.args.get('agent_id')
            
            if agent_id:
                messages = self.nexus.communication_hub.get_agent_messages(agent_id)
            else:
                messages = self.nexus.communication_hub.message_history[-100:]  # Last 100
            
            return jsonify({
                "messages": [
                    {
                        "message_id": msg.message_id,
                        "from_agent": msg.from_agent,
                        "to_agent": msg.to_agent,
                        "type": msg.message_type.value,
                        "content": str(msg.content)[:200],  # Truncate for display
                        "timestamp": msg.timestamp.isoformat()
                    }
                    for msg in messages
                ]
            })
        
        @self.app.route('/api/bootstrap', methods=['POST'])
        def bootstrap():
            """Bootstrap system from a goal"""
            data = request.json
            goal = data.get('goal')
            
            if not goal:
                return jsonify({"error": "Goal is required"}), 400
            
            # Run bootstrap asynchronously
            import asyncio
            
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                root_agent_id = loop.run_until_complete(
                    self.nexus.bootstrap_from_goal(goal)
                )
                loop.close()
                
                return jsonify({
                    "success": True,
                    "root_agent_id": root_agent_id,
                    "message": "System bootstrapped successfully"
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500
    
    def _setup_socketio_handlers(self):
        """Set up WebSocket handlers for real-time updates"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            self.logger.info("Client connected")
            emit('status', self.nexus.get_system_status())
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            self.logger.info("Client disconnected")
        
        @self.socketio.on('subscribe_updates')
        def handle_subscribe():
            """Subscribe to real-time updates"""
            emit('subscribed', {"message": "Subscribed to updates"})
    
    def _get_dashboard_html(self) -> str:
        """Generate the dashboard HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NexusForge 2.0 Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }
        .header {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header h1 {
            font-size: 28px;
            color: #667eea;
            font-weight: 700;
        }
        .header p {
            color: #666;
            margin-top: 5px;
        }
        .container {
            max-width: 1400px;
            margin: 30px auto;
            padding: 0 20px;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        .card h2 {
            font-size: 18px;
            margin-bottom: 15px;
            color: #667eea;
        }
        .stat {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        .stat:last-child { border-bottom: none; }
        .stat-label {
            color: #666;
            font-size: 14px;
        }
        .stat-value {
            font-size: 24px;
            font-weight: 700;
            color: #667eea;
        }
        .bootstrap-section {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        .bootstrap-section h2 {
            color: #667eea;
            margin-bottom: 20px;
        }
        .input-group {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }
        input[type="text"] {
            flex: 1;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover {
            transform: scale(1.05);
        }
        button:active {
            transform: scale(0.95);
        }
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-active { background: #4caf50; }
        .status-idle { background: #ff9800; }
        .status-stopped { background: #f44336; }
        .message {
            padding: 12px;
            margin-top: 15px;
            border-radius: 8px;
            display: none;
        }
        .message.success {
            background: #e8f5e9;
            color: #2e7d32;
            border: 1px solid #4caf50;
        }
        .message.error {
            background: #ffebee;
            color: #c62828;
            border: 1px solid #f44336;
        }
        .agent-list {
            max-height: 400px;
            overflow-y: auto;
        }
        .agent-item {
            padding: 12px;
            border-left: 3px solid #667eea;
            background: #f8f9fa;
            margin-bottom: 10px;
            border-radius: 4px;
        }
        .agent-name {
            font-weight: 600;
            color: #333;
        }
        .agent-role {
            color: #666;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 NexusForge 2.0</h1>
        <p>AGI-lite Autonomous Agent Framework - Production Dashboard</p>
    </div>
    
    <div class="container">
        <div class="bootstrap-section">
            <h2>Bootstrap from Goal</h2>
            <p style="color: #666; margin-bottom: 15px;">
                Enter a high-level goal and NexusForge will spawn a fractal hierarchy of agents to achieve it.
            </p>
            <div class="input-group">
                <input type="text" id="goalInput" placeholder="Enter your goal (e.g., 'Build a web scraper for news articles')" />
                <button onclick="bootstrapSystem()">Bootstrap System</button>
            </div>
            <div id="bootstrapMessage" class="message"></div>
        </div>
        
        <div class="dashboard-grid">
            <div class="card">
                <h2>System Status</h2>
                <div class="stat">
                    <span class="stat-label">Status</span>
                    <span class="stat-value">
                        <span id="systemStatus" class="status-indicator status-active"></span>
                        <span id="systemStatusText">Active</span>
                    </span>
                </div>
                <div class="stat">
                    <span class="stat-label">Total Agents</span>
                    <span class="stat-value" id="totalAgents">0</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Root Agents</span>
                    <span class="stat-value" id="rootAgents">0</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Messages</span>
                    <span class="stat-value" id="messageCount">0</span>
                </div>
            </div>
            
            <div class="card">
                <h2>Crews</h2>
                <div class="stat">
                    <span class="stat-label">Total Crews</span>
                    <span class="stat-value" id="totalCrews">0</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Active Crews</span>
                    <span class="stat-value" id="activeCrews">0</span>
                </div>
            </div>
            
            <div class="card">
                <h2>Experts</h2>
                <div class="stat">
                    <span class="stat-label">Total Experts</span>
                    <span class="stat-value" id="totalExperts">0</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Modalities</span>
                    <span class="stat-value" id="modalityCount">5</span>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>Active Agents</h2>
            <div id="agentList" class="agent-list">
                <p style="color: #666;">No agents yet. Bootstrap the system with a goal to get started.</p>
            </div>
        </div>
    </div>
    
    <script>
        function updateDashboard() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('totalAgents').textContent = data.total_agents || 0;
                    document.getElementById('rootAgents').textContent = data.root_agents || 0;
                    document.getElementById('messageCount').textContent = data.message_count || 0;
                    document.getElementById('totalCrews').textContent = data.total_crews || 0;
                    
                    const statusText = data.running ? 'Active' : 'Stopped';
                    const statusClass = data.running ? 'status-active' : 'status-stopped';
                    document.getElementById('systemStatusText').textContent = statusText;
                    document.getElementById('systemStatus').className = 'status-indicator ' + statusClass;
                });
            
            fetch('/api/statistics')
                .then(response => response.json())
                .then(data => {
                    if (data.crew_stats) {
                        document.getElementById('activeCrews').textContent = data.crew_stats.active || 0;
                    }
                    if (data.expert_stats) {
                        document.getElementById('totalExperts').textContent = data.expert_stats.total || 0;
                    }
                });
            
            fetch('/api/agents')
                .then(response => response.json())
                .then(data => {
                    const agentList = document.getElementById('agentList');
                    if (data.agents && data.agents.length > 0) {
                        agentList.innerHTML = data.agents.map(agent => `
                            <div class="agent-item">
                                <div class="agent-name">${agent.name}</div>
                                <div class="agent-role">${agent.role} • Depth: ${agent.depth} • Status: ${agent.status}</div>
                            </div>
                        `).join('');
                    } else {
                        agentList.innerHTML = '<p style="color: #666;">No agents yet. Bootstrap the system with a goal to get started.</p>';
                    }
                });
        }
        
        function bootstrapSystem() {
            const goal = document.getElementById('goalInput').value;
            const messageDiv = document.getElementById('bootstrapMessage');
            
            if (!goal) {
                showMessage('Please enter a goal', 'error');
                return;
            }
            
            showMessage('Bootstrapping system...', 'success');
            
            fetch('/api/bootstrap', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ goal: goal })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showMessage('System bootstrapped successfully! Agent hierarchy created.', 'success');
                    document.getElementById('goalInput').value = '';
                    updateDashboard();
                } else {
                    showMessage('Error: ' + (data.error || 'Unknown error'), 'error');
                }
            })
            .catch(error => {
                showMessage('Error: ' + error.message, 'error');
            });
        }
        
        function showMessage(text, type) {
            const messageDiv = document.getElementById('bootstrapMessage');
            messageDiv.textContent = text;
            messageDiv.className = 'message ' + type;
            messageDiv.style.display = 'block';
            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 5000);
        }
        
        // Update dashboard every 3 seconds
        updateDashboard();
        setInterval(updateDashboard, 3000);
        
        // Allow Enter key to bootstrap
        document.getElementById('goalInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                bootstrapSystem();
            }
        });
    </script>
</body>
</html>
        """
    
    def run(self):
        """Run the dashboard server"""
        self.logger.info(f"Starting dashboard on {self.host}:{self.port}")
        self.socketio.run(self.app, host=self.host, port=self.port, debug=False)
