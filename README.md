# DDE Agents

## Overview
DDE Agents is a lightweight and flexible software development kit designed to help developers build, and manage AI agents with ease. It provides tools and utilities for creating intelligent, autonomous systems.

## Features
- **Modular Design**: Build AI agents with reusable components.
- **Extensibility**: Easily integrate custom logic and third-party APIs.
- **Scalability**: Designed to handle small to large-scale multi-agent projects.
- **Easy Tool Intergration**: You can easily create (dynamic) functions or agents as tools.

## Installation
To install AgentSDK, use the following command:
```bash
pip install dde-agents
```

**Note:** Not all functionalities are woring as expected. 

## Quick Start
Here’s a simple example to create and run an AI agent:

```python
from agents.Agent import Agent
from agents.Config import ModelConfig

ModelConfig.setDefaultModel("gpt-4o", True)

englishAgent = Agent(
    name="englishAgent",
    instructions="You can only answer in english",
    inputGuardrails="The input can only be english",
)

if __name__ == "__main__":
    print(englishAgent.run(prompt=input("prompt: ")))
```

## Documentation
For detailed documentation on all the functionalities, visit the full [AgentSDK Docs](./documentation/documentation.md).

