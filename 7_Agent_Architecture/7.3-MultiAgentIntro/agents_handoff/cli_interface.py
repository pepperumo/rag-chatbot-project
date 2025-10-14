"""
Simple interface to the handoff research agent.

This just exposes the research agent that uses output functions for email handoffs.
"""

from .research_agent import research_agent, ResearchAgentDependencies

# Export the research agent and dependencies directly
# The research agent now handles handoffs via output functions automatically
__all__ = ['research_agent', 'ResearchAgentDependencies']