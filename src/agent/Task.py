from agent.LLM import runLLM
from agent.Agent import AgentRegistry
from agent.Config import ModelConfig

# __main__
from Agent import Agent

class Task:
    def __init__(self, task: str, agents: list, repeat: bool = False, exitValue: str = None, debug: bool = False):
        self.task = task
        self.agents = agents
        
        if repeat:
            if exitValue != None:
                self.repeat = repeat
                self.exitValue = exitValue
            elif exitValue == None:
                self.repeat = False
                self.exitValue = exitValue
        elif not repeat:
            self.repeat = repeat
            self.exitValue = None

        self.debug = debug
    
    def solve(self):
        response = ""
        if self.repeat:
            attemptSolvePrompt = f"""
                You need to give the right agent for solving the task. If you have found the right on only respond with the name of the agent.
                
                agents: {[agent.name for agent in self.agents]}
                task: {self.task}
                other responses: {response}
                
                Only respond with the name of the right agent you want to select. You chose from agents given to you, you cant make agents up.
            """
            
            if self.debug:
                print(f"[DEBUG] current prompt: {attemptSolvePrompt}")
            
            stdout = runLLM(prompt=attemptSolvePrompt, debug=self.debug)  # select agent
            
            if ModelConfig.getDefaultOpenAI():
                selectedAgent = AgentRegistry.get_agent(stdout.choices[0].message.content.strip())
            elif not ModelConfig.getDefaultOpenAI():
                selectedAgent = AgentRegistry.get_agent(stdout.strip())
            
            response += selectedAgent.run(prompt="hi", debug=self.debug)            
            
            if self.debug:
                print(f"[DEBUG] selectedAgent: {selectedAgent}")
                print(f"[DEBUG] response: {response}")

        elif not self.repeat:
            attemptSolvePrompt = f"""
                You need to give the right agent for solving the task. If you have found the right on only respond with the name of the agent.
                
                agents: {[agent.name for agent in self.agents]}
                task: {self.task}
                other responses: {response}
                
                Only respond with the name of the right agent you want to select. You chose from agents given to you, you cant make agents up.
            """


if __name__== "__main__":
    ModelConfig.setDefaultModel("gpt-4o", True)
    
    solutionAgent = Agent(
        name="solutionAgent",
        instruction="Give a solution",
    )
    
    newTask = Task(task="solve 15+987675=???", agents=[solutionAgent], repeat=True, exitValue="solution reached", debug=True)

    newTask.solve()
