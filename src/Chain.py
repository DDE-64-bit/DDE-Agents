import json

from Agent import Agent
from Config import ModelConfig
from CleanOutput import cleanOutput

class Chain:
    def __init__(self, agents: list['Agent']):
        self.agents = agents
    
    def execute(self, prompt: str, disableGuardrails: bool = False, debug: bool = False) -> dict:
        results = {}
        currentPrompt = prompt
        
        if debug:
            print(f"[DEBUG] agents in crew: {self.agents}")

        for agent in self.agents:
            result = agent.run(currentPrompt, debug, disableGuardrails)
            results[agent.name] = result
            
            if debug:
                print(f"[DEBUG] Results {agent.name}: {result}")
                
            currentPrompt += f"\n{agent.name} response: {result}"

        return results




    def runUntil(self, prompt: str, exitValue: str, maxRuns: int = 0, disableGuardrails: bool = False, debug: bool = False) -> str:
        results = {}
        currentPrompt = prompt

        maxRuns = maxRuns * len(self.agents)

        _agent = Agent(
            name="agent",
            instruction="You need to decide if the exit conditions are met.",
            model=ModelConfig.getDefaultModel(),
            openAI=ModelConfig.getDefaultOpenAI(),
        )

        if debug:
            print(f"[DEBUG] _agent.openAI: {_agent.openAI}")
            print(f"[DEBUG] agents in crew: {self.agents}")
            print(f"[DEBUG] exitCondition: {exitValue}")
        
        i = 0

        while i < maxRuns:
            for agent in self.agents:
                result = agent.run(currentPrompt, debug, disableGuardrails)
                results[agent.name] = result

                if debug:
                    print(f"[DEBUG] Results {agent.name}: {result}")

                currentPrompt += f"\n{agent.name} response: {result}"

            promptRunUntilExitValue = f"""
                "You are now an AI agent.

                    Agent information:
                        - Agent instruction: {_agent.instruction}
                        - Prompt: {prompt}
                        - The conversation: {currentPrompt}
                        - The exit condition: {exitValue}

                    The above list defines you. You can't make any other info up.

                    You need to decide if the exit conditions have been met. If so, respond with a JSON like this:

                    {{
                        "exitCondition": "yes", # make it no if it hasn't been met.
                        "goodAnswerToPrompt": "The answer to 4+1=5" # leave empty if exit condition is no
                    }}

                    Extra instructions:
                        - Only respond with valid JSON. Don't add anything else.
                        - Never use codeblocks (```json ... ```)
                "
            """

            if _agent.openAI:
                stdout = _agent.runOpenAI(promptRunUntilExitValue, debug=debug)
            else:
                stdout = _agent.runLocalModel(promptRunUntilExitValue, debug=debug)

            data = cleanOutput(stdout, ModelConfig.getDefaultOpenAI(), debug=debug)

            if debug:
                print(f"[DEBUG] JSON output from decision agent: {data}")

            i += 1
            
            try:
                if data.get("exitCondition") == "yes":
                    return data.get("goodAnswerToPrompt", "")
            except Exception as e:
                if debug:
                    print(f"[DEBUG] Failed to parse JSON output: {e}")
                    print(f"[DEBUG] Raw output: {data}")

        return results