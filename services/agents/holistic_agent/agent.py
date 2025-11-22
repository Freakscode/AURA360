"""Entry point for the holistic agent when loaded by Google ADK."""

from . import holistic_coordinator

# ADK expects a variable named `root_agent` exposed at the module level.
root_agent = holistic_coordinator
