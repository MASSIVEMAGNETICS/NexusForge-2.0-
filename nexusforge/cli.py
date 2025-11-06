"""
Command Line Interface for NexusForge

Provides CLI commands to bootstrap, monitor, and control the agent system.
"""

import asyncio
import argparse
import sys
import json
from typing import Optional

from nexusforge.core.nexus import NexusForge
from nexusforge.core.fractal_agent import AgentTemplate
from nexusforge.gui.dashboard import NexusDashboard


class NexusCLI:
    """Command Line Interface for NexusForge"""
    
    def __init__(self):
        self.nexus: Optional[NexusForge] = None
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser"""
        parser = argparse.ArgumentParser(
            description='NexusForge 2.0 - AGI-lite Autonomous Agent Framework',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Bootstrap from a goal
  python -m nexusforge bootstrap "Build a web scraper for news articles"
  
  # Start the GUI dashboard
  python -m nexusforge gui
  
  # Show system status
  python -m nexusforge status
  
  # List all agents
  python -m nexusforge list agents
  
  # Get agent hierarchy
  python -m nexusforge hierarchy
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Command to execute')
        
        # Bootstrap command
        bootstrap_parser = subparsers.add_parser(
            'bootstrap',
            help='Bootstrap the system from a high-level goal'
        )
        bootstrap_parser.add_argument('goal', type=str, help='High-level goal to achieve')
        bootstrap_parser.add_argument(
            '--max-depth',
            type=int,
            default=5,
            help='Maximum depth of agent hierarchy (default: 5)'
        )
        bootstrap_parser.add_argument(
            '--with-gui',
            action='store_true',
            help='Start GUI dashboard after bootstrapping'
        )
        
        # GUI command
        gui_parser = subparsers.add_parser('gui', help='Start the web dashboard')
        gui_parser.add_argument(
            '--host',
            type=str,
            default='0.0.0.0',
            help='Host to bind to (default: 0.0.0.0)'
        )
        gui_parser.add_argument(
            '--port',
            type=int,
            default=8080,
            help='Port to bind to (default: 8080)'
        )
        
        # Status command
        subparsers.add_parser('status', help='Show system status')
        
        # List command
        list_parser = subparsers.add_parser('list', help='List system components')
        list_parser.add_argument(
            'component',
            choices=['agents', 'crews', 'experts', 'messages'],
            help='Component to list'
        )
        
        # Hierarchy command
        subparsers.add_parser('hierarchy', help='Show agent hierarchy')
        
        # Statistics command
        subparsers.add_parser('stats', help='Show detailed statistics')
        
        return parser
    
    def initialize_nexus(self):
        """Initialize NexusForge system"""
        if not self.nexus:
            self.nexus = NexusForge()
            asyncio.run(self.nexus.start())
    
    async def cmd_bootstrap(self, args):
        """Bootstrap command"""
        self.initialize_nexus()
        
        print(f"🚀 Bootstrapping NexusForge from goal: {args.goal}")
        print(f"   Max depth: {args.max_depth}")
        print()
        
        root_agent_id = await self.nexus.bootstrap_from_goal(args.goal)
        
        print(f"✅ Bootstrap complete!")
        print(f"   Root agent ID: {root_agent_id}")
        print()
        
        # Show hierarchy
        hierarchy = self.nexus.get_agent_hierarchy(root_agent_id)
        self._print_hierarchy(hierarchy)
        
        if args.with_gui:
            print("\n🌐 Starting web dashboard...")
            dashboard = NexusDashboard(self.nexus)
            dashboard.run()
    
    def cmd_gui(self, args):
        """GUI command"""
        self.initialize_nexus()
        
        print(f"🌐 Starting NexusForge Dashboard")
        print(f"   URL: http://{args.host}:{args.port}")
        print(f"   Press Ctrl+C to stop")
        print()
        
        dashboard = NexusDashboard(self.nexus, host=args.host, port=args.port)
        dashboard.run()
    
    def cmd_status(self, args):
        """Status command"""
        self.initialize_nexus()
        
        status = self.nexus.get_system_status()
        
        print("📊 NexusForge System Status")
        print("=" * 50)
        print(f"Running:       {status['running']}")
        print(f"Start Time:    {status['start_time'] or 'Not started'}")
        print(f"Total Agents:  {status['total_agents']}")
        print(f"Root Agents:   {status['root_agents']}")
        print(f"Total Crews:   {status['total_crews']}")
        print(f"Total Experts: {status['total_experts']}")
        print(f"Messages:      {status['message_count']}")
        print()
        print("Agents by Status:")
        for status_name, count in status['agents_by_status'].items():
            print(f"  {status_name}: {count}")
    
    def cmd_list(self, args):
        """List command"""
        self.initialize_nexus()
        
        if args.component == 'agents':
            agents = self.nexus.get_all_agents()
            print(f"📋 Total Agents: {len(agents)}")
            print("=" * 80)
            for agent in agents:
                print(f"ID: {agent.agent_id}")
                print(f"  Name:   {agent.state.name}")
                print(f"  Role:   {agent.state.role}")
                print(f"  Depth:  {agent.depth}")
                print(f"  Status: {agent.state.status}")
                print(f"  Goals:  {', '.join(agent.state.goals) if agent.state.goals else 'None'}")
                print()
        
        elif args.component == 'crews':
            crews = self.nexus.crew_manager.get_all_crews()
            print(f"👥 Total Crews: {len(crews)}")
            print("=" * 80)
            for crew in crews:
                print(f"ID: {crew.crew_id}")
                print(f"  Name:    {crew.name}")
                print(f"  Leader:  {crew.leader_id or 'None'}")
                print(f"  Members: {len(crew.members)}")
                print(f"  Status:  {crew.status}")
                print(f"  Goals:   {', '.join(crew.goals) if crew.goals else 'None'}")
                print()
        
        elif args.component == 'experts':
            experts = self.nexus.expert_system.get_all_experts()
            print(f"🎓 Total Experts: {len(experts)}")
            print("=" * 80)
            for expert in experts:
                print(f"ID: {expert.expert_id}")
                print(f"  Name:       {expert.name}")
                print(f"  Modality:   {expert.modality.value}")
                print(f"  Specializations: {', '.join(expert.specializations)}")
                print(f"  Capabilities:    {', '.join(expert.capabilities)}")
                print()
        
        elif args.component == 'messages':
            messages = self.nexus.communication_hub.message_history[-20:]  # Last 20
            print(f"💬 Recent Messages (last 20)")
            print("=" * 80)
            for msg in messages:
                print(f"[{msg.timestamp.strftime('%H:%M:%S')}] {msg.from_agent} → {msg.to_agent or 'ALL'}")
                print(f"  Type: {msg.message_type.value}")
                print(f"  Content: {str(msg.content)[:100]}")
                print()
    
    def cmd_hierarchy(self, args):
        """Hierarchy command"""
        self.initialize_nexus()
        
        hierarchy = self.nexus.get_agent_hierarchy()
        
        print("🌳 Agent Hierarchy")
        print("=" * 80)
        
        if 'hierarchies' in hierarchy:
            for root_hierarchy in hierarchy['hierarchies']:
                self._print_hierarchy(root_hierarchy)
        else:
            print("No agent hierarchies found. Bootstrap the system first.")
    
    def cmd_stats(self, args):
        """Statistics command"""
        self.initialize_nexus()
        
        stats = self.nexus.get_statistics()
        
        print("📈 NexusForge Statistics")
        print("=" * 80)
        print()
        
        print("System Status:")
        for key, value in stats['system_status'].items():
            print(f"  {key}: {value}")
        print()
        
        print("Agent Statistics:")
        print(f"  Total: {stats['agent_stats']['total']}")
        print("  By Depth:")
        for depth, count in sorted(stats['agent_stats']['by_depth'].items()):
            print(f"    Depth {depth}: {count}")
        print("  By Role:")
        for role, count in stats['agent_stats']['by_role'].items():
            print(f"    {role}: {count}")
        print()
        
        print("Crew Statistics:")
        for key, value in stats['crew_stats'].items():
            print(f"  {key}: {value}")
        print()
        
        print("Expert Statistics:")
        print(f"  Total: {stats['expert_stats']['total']}")
        print("  By Modality:")
        for modality, count in stats['expert_stats']['by_modality'].items():
            print(f"    {modality}: {count}")
        print()
        
        print("Communication Statistics:")
        for key, value in stats['communication_stats'].items():
            print(f"  {key}: {value}")
    
    def _print_hierarchy(self, node, indent=0):
        """Print agent hierarchy tree"""
        prefix = "  " * indent + ("└─ " if indent > 0 else "")
        print(f"{prefix}{node['name']} ({node['role']}) [Depth: {node['depth']}, Status: {node['status']}]")
        if node.get('goals'):
            print(f"{'  ' * (indent + 1)}Goals: {', '.join(node['goals'])}")
        
        for child in node.get('children', []):
            self._print_hierarchy(child, indent + 1)
    
    def run(self):
        """Run the CLI"""
        args = self.parser.parse_args()
        
        if not args.command:
            self.parser.print_help()
            return
        
        try:
            if args.command == 'bootstrap':
                asyncio.run(self.cmd_bootstrap(args))
            elif args.command == 'gui':
                self.cmd_gui(args)
            elif args.command == 'status':
                self.cmd_status(args)
            elif args.command == 'list':
                self.cmd_list(args)
            elif args.command == 'hierarchy':
                self.cmd_hierarchy(args)
            elif args.command == 'stats':
                self.cmd_stats(args)
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            if self.nexus:
                asyncio.run(self.nexus.stop())
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


def main():
    """Main entry point"""
    cli = NexusCLI()
    cli.run()


if __name__ == '__main__':
    main()
