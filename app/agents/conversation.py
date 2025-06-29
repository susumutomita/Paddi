#!/usr/bin/env python3
"""
Conversational Security Advisor

Natural language interface for security consultation and autonomous problem solving.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from .orchestrator import MultiAgentCoordinator

# Optional imports
try:
    import streamlit as st

    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

logger = logging.getLogger(__name__)
console = Console()


class ConversationalInterface:
    """Interactive conversational interface for Paddi."""

    def __init__(self):
        """Initialize conversational interface."""
        self.coordinator = MultiAgentCoordinator()
        self.conversation_history = []
        self.context = {
            "project_id": None,
            "repository": None,
            "findings": [],
            "recommendations": [],
        }

    def start_cli_interface(self):
        """Start command-line conversational interface."""
        self._print_welcome()

        while True:
            try:
                # Get user input
                user_input = console.input("\n[bold cyan]You:[/bold cyan] ")

                if user_input.lower() in ["exit", "quit", "bye", "終了"]:
                    self._print_goodbye()
                    break

                if not user_input.strip():
                    continue

                # Process input
                self._process_user_input(user_input)

            except KeyboardInterrupt:
                self._print_goodbye()
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                logger.error("Error in conversation", exc_info=True)

    def start_web_interface(self):
        """Start Streamlit web interface."""
        if not HAS_STREAMLIT:
            console.print(
                "[red]Streamlit is not installed. Install it with: pip install streamlit[/red]"
            )
            return

        st.set_page_config(
            page_title="Paddi Security AI Assistant",
            page_icon="🔒",
            layout="wide",
        )

        st.title("🤖 Paddi Security AI Assistant")
        st.markdown(
            "I'm your AI-powered security advisor. Ask me anything about your cloud security!"
        )

        # Initialize session state
        if "messages" not in st.session_state:
            st.session_state.messages = []
            st.session_state.context = {}

        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # User input
        if prompt := st.chat_input("Ask about security..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate response
            with st.chat_message("assistant"):
                with st.spinner("Analyzing..."):
                    response = self.coordinator.process_complex_request(prompt)
                    st.markdown(response["message"])

                    # Show details in expander
                    with st.expander("🔍 Details"):
                        st.json(response.get("results", {}))

            # Add assistant message
            st.session_state.messages.append({"role": "assistant", "content": response["message"]})

    def _print_welcome(self):
        """Print welcome message."""
        console.print("\n[bold cyan]🤖 Paddi Security AI Assistant[/bold cyan]")
        console.print("=" * 60)
        console.print("\n[green]Hello! I'm Paddi, your AI security advisor.[/green]")
        console.print("\nI can help you with:")

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Feature", style="cyan")
        table.add_row("🔍 Security audits", "Find vulnerabilities in your infrastructure")
        table.add_row("💡 Risk analysis", "Understand security risks and their impact")
        table.add_row("🔧 Fix suggestions", "Get actionable remediation steps")
        table.add_row("📊 Reports", "Generate comprehensive security reports")
        table.add_row("💻 Code analysis", "Analyze code for security issues")

        console.print(table)
        console.print("\n[dim]Type 'exit' to quit[/dim]\n")

    def _print_goodbye(self):
        """Print goodbye message."""
        console.print("\n[bold cyan]👋 Thank you for using Paddi![/bold cyan]")
        console.print("[green]Stay secure! 🔒[/green]\n")

    def _process_user_input(self, user_input: str):
        """Process user input and show response."""
        # Show thinking indicator
        with console.status("[bold green]Thinking...[/bold green]", spinner="dots"):
            response = self.coordinator.process_complex_request(user_input)

        # Display response
        console.print("\n[bold green]Paddi:[/bold green]")

        # Format and display the response
        if response.get("success"):
            self._display_response(response)
        else:
            console.print("[red]I encountered an error while processing your request.[/red]")

        # Update context
        self._update_context(response)

    def _display_response(self, response: Dict[str, Any]):
        """Display formatted response."""
        # Main message
        message = response.get("message", "")
        console.print(Markdown(message))

        # Show execution plan if interesting
        plan = response.get("plan_executed", [])
        if len(plan) > 1:
            console.print("\n[dim]Actions taken:[/dim]")
            for action in plan:
                console.print(f"  [dim]✓[/dim] {action.replace('_', ' ').title()}")

        # Show key results
        results = response.get("results", {})
        self._display_key_results(results)

    def _display_key_results(self, results: Dict[str, Any]):
        """Display key results in a formatted way."""
        # Check for vulnerabilities
        for key, result in results.items():
            if isinstance(result, dict) and result.get("status") == "completed":
                if "vulnerabilities" in result:
                    self._display_vulnerabilities(result["vulnerabilities"])
                elif "findings" in result and key != "collect_cloud_config":
                    self._display_findings(result["findings"])
                elif "recommendations" in result:
                    self._display_recommendations(result["recommendations"])

    def _display_vulnerabilities(self, vulnerabilities: List[Dict[str, Any]]):
        """Display vulnerabilities in a table."""
        if not vulnerabilities:
            return

        console.print("\n[bold yellow]⚠️  Vulnerabilities Found:[/bold yellow]")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("File", style="cyan")
        table.add_column("Line", justify="right")
        table.add_column("Type", style="yellow")
        table.add_column("Severity", style="red")

        for vuln in vulnerabilities[:5]:  # Show top 5
            table.add_row(
                vuln.get("file", "N/A"),
                str(vuln.get("line", "N/A")),
                vuln.get("type", "N/A"),
                vuln.get("severity", "N/A"),
            )

        console.print(table)

        if len(vulnerabilities) > 5:
            console.print(f"[dim]... and {len(vulnerabilities) - 5} more[/dim]")

    def _display_findings(self, findings: List[Dict[str, Any]]):
        """Display security findings."""
        if not findings:
            return

        console.print("\n[bold red]🚨 Security Findings:[/bold red]")

        for i, finding in enumerate(findings[:3], 1):
            severity = finding.get("severity", "UNKNOWN")
            color = {
                "CRITICAL": "red",
                "HIGH": "red",
                "MEDIUM": "yellow",
                "LOW": "blue",
            }.get(severity, "white")

            console.print(
                f"\n{i}. [{color}]{severity}[/{color}] - {finding.get('description', 'N/A')}"
            )
            if "recommendation" in finding:
                console.print(f"   [dim]→ {finding['recommendation']}[/dim]")

    def _display_recommendations(self, recommendations: List[Dict[str, Any]]):
        """Display recommendations."""
        if not recommendations:
            return

        console.print("\n[bold green]✅ Recommendations:[/bold green]")

        for i, rec in enumerate(recommendations[:3], 1):
            priority = rec.get("priority", "N/A")
            color = {
                "HIGH": "red",
                "MEDIUM": "yellow",
                "LOW": "green",
            }.get(priority, "white")

            console.print(f"\n{i}. [{color}]{priority} Priority[/{color}]")
            console.print(f"   {rec.get('action', 'N/A')}")
            console.print(f"   [dim]Impact: {rec.get('impact', 'N/A')}[/dim]")
            console.print(f"   [dim]Effort: {rec.get('effort', 'N/A')}[/dim]")

    def _update_context(self, response: Dict[str, Any]):
        """Update conversation context."""
        # Extract important information
        results = response.get("results", {})

        # Update findings
        for key, result in results.items():
            if isinstance(result, dict):
                if "findings" in result:
                    self.context["findings"].extend(result["findings"])
                if "recommendations" in result:
                    self.context["recommendations"] = result["recommendations"]

        # Add to history
        self.conversation_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "response": response,
            }
        )


class SecurityChatbot:
    """Advanced chatbot with memory and learning capabilities."""

    def __init__(self):
        """Initialize chatbot."""
        self.memory = {
            "short_term": [],  # Recent conversation
            "long_term": {},  # Learned patterns
            "context": {},  # Current context
        }
        self.learning_enabled = True

    def chat(self, message: str) -> str:
        """Process chat message with context awareness."""
        # Add to short-term memory
        self.memory["short_term"].append(
            {
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Analyze context
        context = self._analyze_context(message)

        # Generate contextual response
        response = self._generate_contextual_response(message, context)

        # Learn from interaction
        if self.learning_enabled:
            self._learn_from_interaction(message, response, context)

        # Add to memory
        self.memory["short_term"].append(
            {
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Maintain memory size
        if len(self.memory["short_term"]) > 20:
            self.memory["short_term"] = self.memory["short_term"][-20:]

        return response

    def _analyze_context(self, message: str) -> Dict[str, Any]:
        """Analyze message context."""
        context = {
            "intent": None,
            "entities": {},
            "sentiment": "neutral",
            "urgency": "normal",
        }

        # Check urgency
        urgent_words = ["urgent", "asap", "immediately", "critical", "emergency"]
        if any(word in message.lower() for word in urgent_words):
            context["urgency"] = "high"

        # Check for follow-up
        if self.memory["short_term"]:
            last_exchange = self.memory["short_term"][-2:]
            if len(last_exchange) == 2:
                # This is a follow-up conversation
                context["is_followup"] = True
                context["previous_topic"] = last_exchange[0].get("topic")

        return context

    def _generate_contextual_response(self, message: str, context: Dict[str, Any]) -> str:
        """Generate response based on context."""
        # High urgency response
        if context.get("urgency") == "high":
            return self._handle_urgent_request(message)

        # Follow-up response
        if context.get("is_followup"):
            return self._handle_followup(message, context)

        # New conversation
        return self._handle_new_request(message)

    def _handle_urgent_request(self, message: str) -> str:
        """Handle urgent security requests."""
        return (
            "🚨 I understand this is urgent. Let me help you immediately.\n\n"
            "I'm analyzing your infrastructure for critical vulnerabilities...\n"
            "This will take just a moment."
        )

    def _handle_followup(self, message: str, context: Dict[str, Any]) -> str:
        """Handle follow-up questions."""
        return (
            "Based on our previous discussion, I can provide more details.\n"
            "Let me elaborate on that point..."
        )

    def _handle_new_request(self, message: str) -> str:
        """Handle new requests."""
        return "I'll help you with that. Let me analyze your request..."

    def _learn_from_interaction(self, message: str, response: str, context: Dict[str, Any]):
        """Learn from user interactions."""
        # Simple pattern learning
        pattern_key = context.get("intent", "unknown")
        if pattern_key not in self.memory["long_term"]:
            self.memory["long_term"][pattern_key] = []

        self.memory["long_term"][pattern_key].append(
            {
                "input": message,
                "context": context,
                "response_quality": None,  # Could be rated by user
                "timestamp": datetime.now().isoformat(),
            }
        )


def main():
    """Main entry point for conversational interface."""
    import sys

    if "--web" in sys.argv:
        # Launch Streamlit interface
        interface = ConversationalInterface()
        interface.start_web_interface()
    else:
        # Launch CLI interface
        interface = ConversationalInterface()
        interface.start_cli_interface()


if __name__ == "__main__":
    import fire

    fire.Fire(main)
