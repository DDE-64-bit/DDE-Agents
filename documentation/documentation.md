# Documentation


DDE Agents come packed with a wide range of features designed to support dynamic and flexible workflows. 

Below is an overview of all available functionalities:

- [Run agents](#run-agents): Lets you run custom agents. This is the base of the SDK.
- [Model selection](#model-selection): You can choose for each agent the preferd model. You have the option between ollama models and OpenAI models.
- [Guardrails](#guardrails): Choose if you want input, output or both kind of guardrails.
- [Chain](#chain): When multiple agents work after each other on the same problem or task you can use chains.
- [Generate agent](#generate-agent): If you need dynamicly generated agents you can have an agent generate as much as you wish.
- [Tools](#tools): You can have either agents or function be availeble as tools.
- [Handoffs](#handoffs): When an agent finishes his task should he stop completly or do you want him to hand his progress or task over to the next agent?

<!--We're currently working on this. If you see this you're interesed to code, so fork this repo and contribute-->
<!--- [Run until](): If you want to have a chain run unitl an exit condition is met? This is your option.-->

<br>

## Run agents

This is the basis of this SDK. The ability to make and run agents.

``` python
from agent.Agent import Agent

tutorAgent = Agent(
    name="tutorAgent",  # The name of the agent
    instruction="You need to help with homework.",  # A default instruction for the agent
    model="gpt-3.5-turbo",  # Set the model to an openAI model
    openAI=True,  # This value is so the SDK knows that you're using an openAI model
)

if __name__ == "__main__":
    print(tutorAgent.run(input("Homework question: ")))  # Run the agent and print the output
```

<br>

## Model selection

There are 2 ways to select the model for an agent.

The first one is manual selection. For the second option you set the default model for all the agents unless an agent is configured with manual selection. 

### Manual selection

``` python
from agent.Agent import Agent

agent = Agent(
    name="agent",
    instruction="You are an ai agent",
    model="gpt-4o",  # This sets the model for this agent to the openAI model gpt 4o
    openAI=True,  # You need to specify that it is an openAI model here
    # If you were using a ollama model you can either leave the openAI option out or set it to False
)
```

### Default model

``` python
from agent.Agent import Agent
from agent.Config import ModelConfig

ModelConfig.setDefaultModel("gpt-4o", True)  # The first parameter is the model and the second is comparable to the openAI bool from manual selection

agent = Agent(
    name="agent",
    instruction="You are an ai agent",
)
```

### Note

There is something importaint to note and that is that there are a lot of different models for a lot of different purposes. For this SDK we classify tasks for agents in 3 scales. We have normal, strict and special. Here is a short description of all of them.

- Normal: normal tasks are tasks that can be done by (almost) all modern large language models. So if you have agents that do a normal task they can use basically all models.
- Strict: strict tasks are tasks that need a specific output in order to work. E.g. if you want to dynamically generate agents or parameters you need a strict model. With that we mean a model that can follow strict rules. Most of the time that means that a model has more parameters.
- Special: and finally special tasks include processing or generating images or using audio. Those tasks can only be performed by specific models.


Here is you can see what functionality works with which scale.

| Functionality | Scale  |
|:-------------|:--------:|
| Run agent| Normal|
| Tools            | Normal  |
| Chain            | Normal  |
| Guardrails       | Strict  |
| Generate Agent   | Strict  |
| Handoff          | Strict  |
| Run until        | Strict  |
| Images           | Special |
| Audio            | Special |


<br>

## Guardrails

You can use guardrails to keep your agents in line.

Input guardrails are used to validate the (user) input against a given rule or rules.

Output guardrails are checked after the agent has completed its task. Then it will check if the output is 'good' according to the given guardrails.

You can use both input and output guardrails on the same agent.


### Input guardrails

``` python
from agent.Agent import Agent

tutorAgent = Agent(
    name="tutorAgent",
    instruction="You need to help with homework.",
    model="gpt-3.5-turbo",
    openAI=True,
    inputGuardrails="The input can only be homework related.",  
    # This will check if the user input is homework related if so the agent will answer the question
    # if not the agent will return a response sayinh input guardrails triggered.
)

if __name__ == "__main__":
    print(tutorAgent.run(input("Homework question: ")))
```

### Output guardrails

``` python
from agent.Agent import Agent

tutorAgent = Agent(
    name="tutorAgent",
    instruction="You need to help with homework.",
    model="gpt-3.5-turbo",
    openAI=True,
    outputGuardrails="The output can only help guide in the direction of the answer but can't contain the answer",  
    # This will check if the output of the agent is not a direct answer
)

if __name__ == "__main__":
    print(tutorAgent.run(input("Homework question: ")))
```

### Both guardrails

``` python
from agent.Agent import Agent

tutorAgent = Agent(
    name="tutorAgent",
    instruction="You need to help with homework.",
    model="gpt-3.5-turbo",
    openAI=True,
    outputGuardrails="The output can only help guide in the direction of the answer but can't contain the answer",  
    inputGuardrails="The input can only be homework related.",  
    # This will check both in- and output guardrails
)

if __name__ == "__main__":
    print(tutorAgent.run(input("Homework question: ")))
```

<br>

## Chain
With a chain you can link a few agents together that will be run in sequence.

``` python
from agent.Agent import Agent
from agent.Chain import Chain
from agent.Config import ModelConfig

# Set model
ModelConfig.setDefaultModel("gpt-4o", True)

# Make agents
warrenBuffettAgent = Agent(
    name="warrenBuffett",
    instruction="You are Warren Buffett. You analyze a stock like warren buffet. answer in 3 bulletpoints.",
)

stockAnalyzerAgent = Agent(
    name="stockAnalyzer",
    instruction="You analyze stocks based on technical analysis and company fundamentals. In 3 bulletpoints.",
)

portfolioManagerAgent = Agent(
    name="portfolioManager",
    instruction="You need to decide based on the given info if the stock is a buy or sell. Be consise. And you have to chose 1.",
)

if __name__ == "__main__":
    # Make chain
    chain = Chain([warrenBuffettAgent, stockAnalyzerAgent, portfolioManagerAgent])
    
    # Execute the chain
    result = chain.execute("Is NVIDIA a buy or sell?")
    
    # Print the results
    for key, value in result.items():
        print(f"\n=== {key.upper()} ===")
        print(value)
```

<br>

## Generate Agent
Generate agent is a powerful tool to dynamically generate agents fitting the task.

``` python
from agent.Agent import Agent
from agent.Chain import Chain
from agent.Config import ModelConfig

# Set model
ModelConfig.setDefaultModel("gpt-4o", True)

# Make agent
triageAgent = Agent(
    name="triageAgent",
    instruction="You need to generate agents to make a good consise prediction about a stock."
)

if __name__ == "__main__":
    # Generate agents
    agents = triageAgent.generateAgent("Generate 3 consise ai agents that can analyze a given stock.")
    
    # Make and run chain
    chain = Chain(agents)
    result = chain.execute("Is NVIDIA a buy or sell?")
    
    # Print the results
    for key, value in result.items():
        print(f"\n=== {key.upper()} ===")
        print(value)
```

<br>

## Tools
Tools can supercharge your ordinary agents.

There are 3 type of tools:

- **Agent as tool**: You can have an agent as tool for an other agent that way the tool agent will be run and the output will be given to the main agent.
- **Function as tool**: You can create a normal python function and the output will be given to the main agent.
- **Dynamic function as tool**: A dynamic functions can be created with the ```@dynamicTool``` decorator when this happens you can give the function to the main agent and it will run a subagent to generate the right parameters for the function using the default model.

### Agent as tool

``` python
from agent.Agent import Agent
from agent.Config import ModelConfig

ModelConfig.setDefaultModel("gpt-4o", True)

# Create the tool agent
topicAgent = Agent(
    name="topic",
    instruction="You need to give a completly random topic. Answer consise, in as little words as possible."
)

# Create the main agent
jokeAgent = Agent(
    name="joke",
    instruction="You need to generate a joke based on the given topic.",
    tools=[topicAgent],
)

if __name__ == "__main__":
    # Run and print the agent
    print(jokeAgent.run(""))
```

### Function as tool

``` python
from agent.Agent import Agent
from agent.Config import ModelConfig

import random

ModelConfig.setDefaultModel("gpt-4o", True)

# Create the tool function 
# This can be anything, e.g. an api request, fetch json data, analyze screenshot. The sky is the limit!
def getTopic():
    number = random.randint(1, 6)
    if number == 1:
        return "awkward first dates"
    elif number == 2:
        return "weird things pets do"
    elif number == 3:
        return "coffee addiction struggles"
    elif number == 4:
        return "gym fails"
    elif number == 5:
        return "bad cooking disasters"
    elif number == 6:
        return "strange roommate habits"

# Create main agent
jokeAgent = Agent(
    name="joke",
    instruction="You need to generate a joke based on the given topic.",
    tools=[getTopic],
)

if __name__ == "__main__":
    # Run and print the agent
    print(jokeAgent.run(""))
```

### Dynamic function as tool

``` python
from agent.Agent import Agent
from agent.Config import ModelConfig
from agent.Tool import dynamicTool

import random

ModelConfig.setDefaultModel("gpt-4o", True)

# Create dynamic function
@dynamicTool # Be 100% sure you add this
def fetchWeather(city: str):
    city = city.lower().strip()
    
    if city == "london":
        return "A clear day 18 degree C"
    if city == "amsterdam":
        return "Cloudy but warm, 20 degree C"
    if city == "singapore":
        return "Hot and sunny day, 40 degree C"

# Create agent
weatherAgent = Agent(
    name="weather",
    instruction="Use the tool to get the weather for the given city. Don't invent or assume additional data. Just return the tool's result. dont parrot the response but say it like a weatherman.",
    tools=[fetchWeather],
)

if __name__ == "__main__":
    # Run and print the agent
    print(weatherAgent.run("What the weather in the netherlands?"))
```

## Handoffs

Handoffs let you give the task/prompt to the next agent with all the context from example tool you've previous ran with that agent or in its context.

``` python 
from agent.Agent import Agent
from agent.Config import ModelConfig

ModelConfig.setDefaultModel("gpt-4o", True)

englishAgent = Agent(
    name="english",
    instruction="You can only speak english.",
)

dutchAgent = Agent(
    name="dutch",
    instruction="You can only speak dutch",
)

triageAgent = Agent(
    name="triage",
    instruction="You need to handoff to the right agent based on the prompt.",
    handoffs=[englishAgent, dutchAgent],
)

if __name__ == "__main__":
    print(triageAgent.run(input("prompt: "), True))
```

