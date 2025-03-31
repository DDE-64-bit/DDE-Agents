from Agent import Agent

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
