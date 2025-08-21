# DDE Agents

## Overview
DDE Agents is a lightweight and flexible software development kit designed to help developers build, and manage AI agents with ease. It provides tools and utilities for creating intelligent, autonomous systems.

## Features
- **Modular Design**: Build AI agents with reusable components.
- **Extensibility**: Easily integrate custom logic and third-party APIs.
- **Scalability**: Designed to handle small to large-scale multi-agent projects.
- **Easy Tool Intergration**: You can easily create (dynamic) functions or agents as tools.

And above all you can use local ollama and openAI models.

If you want to use a hugginface [GGUF model](https://huggingface.co/docs/hub/gguf) you can do so by setting the model to ```hf.co/{author}/{model}```.

## Installation
To install AgentSDK, use the following command:
```bash
pip install dde-agents
```

**Note:** Not all functionalities are woring as expected. 

## Quick Start
Here’s a simple example to create and run an AI agent:

```python
from agent.Agent import Agent
from agent.Config import ModelConfig

ModelConfig.setDefaultModel("gpt-4o", True)

englishAgent = Agent(
    name="englishAgent",
    instructions="You can only answer in english",
    inputGuardrails="The input can only be english",
)

if __name__ == "__main__":
    print(englishAgent.run(prompt=input("prompt: ")))
```

## API key

If you are using an openAI model you should set the api key using environment variables.

``` shell
export OPENAI_API_KEY='super-secret-key'
```

## Requirements

You need to have ollama installed, you can download it [here](https://ollama.com/).
This is important if you want to use local GGUF models.


## Documentation
For detailed documentation on all the functionalities, visit the full [DDE Agents Docs](./documentation/documentation.md).

For other agents made with this SDK please have a look at [this](https://github.com/DDE-64-bit/AI-agents) repository.
