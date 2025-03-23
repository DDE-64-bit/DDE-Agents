import subprocess
import json
import select

class AgentRegistry:
    _agents = []

    @classmethod
    def register(cls, agent):
        cls._agents.append(agent)

    @classmethod
    def get_agent(cls, name):
        return next((agent for agent in cls._agents if agent.name == name), None)

    @classmethod
    def list_agents(cls):
        return cls._agents



class Agent:
    def __init__(self, name: str, instruction: str, model: str = "llama3.1", tools: list = None, handoffs: list = None, outputs: list = None):
        self.name = name
        self.instruction = instruction
        self.model = model if model is not None else "llama3.1"
        self.tools = tools if tools is not None else []
        self.handoffs = handoffs if handoffs is not None else []
        self.outputs = outputs if outputs is not None else []
        
        AgentRegistry.register(self)

    
    
    def run(self, prompt: str, debug: bool = False) -> str:
        response = ""
        
        handoffsList = ", ".join([handoff.name for handoff in self.handoffs])
        if debug:
            print(f"[DEBUG] HandoffsList: {handoffsList}")
        
        # Run Tools
        if self.tools != []:
            for tool in self.tools[:]:
                if callable(tool):  
                    if debug:
                        print(f"[DEBUG] {tool.__name__} is een functie (def).")

                    try:
                        toolResult = tool()
                        response += f" response tool: {tool.__name__}: {toolResult} \n"
                        if debug:
                            print(f"[DEBUG] Response {tool}: {toolResult}")
                            print(f"[DEBUG] Total response: {response}")
                    except Exception as e:
                        response += f" response tool: {tool.__name__} failed: {str(e)} \n"
                        if debug:
                            print(f"[ERROR] Error with {tool.__name__}: {str(e)}")

                elif isinstance(tool, Agent):  
                    if debug:
                        print(f"[DEBUG] {tool.name} is an instance of Agent class")
                    try:
                        toolResult = tool.run(prompt + response, debug)
                        response += f" response tool: {tool.name}: {toolResult} \n"
                        if debug:
                            print(f"[DEBUG] Response {tool}: {toolResult}")
                            print(f"[DEBUG] Total response: {response}")
                    except Exception as e:
                        response += f" response tool: {tool.name} failed: {str(e)} \n"
                        if debug:
                            print(f"[ERROR] Error with {tool.name}: {str(e)}")

                else:
                    if debug:
                        print(f"[ERROR] Unknown type: {type(tool)}")
                    response += f" Error: Unknown type: ({type(tool)}).\n"

                if debug:
                    print(f"[DEBUG] running agent {self.name}")
                if debug:
                    print(f"[DEBUG] response tool: {response}")

        else:
            if debug:
                print("[DEBUG] This agent can't use tools.")


        normalPrompt = f"""
        ollama run {self.model} "You are now an AI agent.

        Agent information:
            - Agent name: {self.name}
            - Agent instruction: {self.instruction}
            - Prompt: {prompt}
            - Extra info: {response}

        The above list defines you. You can't make any other info up.
        
        Follow these instructions precisely."
        """
        
        if debug:
            print(f"[DEBUG] Current prompt: {normalPrompt}")
        
        process = subprocess.Popen(normalPrompt, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        stdout, stderr = process.communicate()
        
        if debug:
            print(f"[DEBUG] Stdout: {stdout}")
            print(f"[DEBUG] stderr: {stderr}")

        response += f"response of {self.name}: {stdout}"
        
        
        if self.handoffs == []:
            return stdout if stdout else stderr
        elif self.handoffs != []:
            promptWithHandoffs = f"""
                ollama run {self.model} "You are now an AI agent.

                Agent information:
                - Agent name: {self.name}
                - Agent instruction: {self.instruction}
                - Agent handoffs: {handoffsList}
                - Prompt: {prompt}

                The above list defines you. You can't make any other info up.

                **Formatting Rules:**
                - You have to select a handoff from your list fitting the task and prompt. It can only be from your list, don't make anything up.
                - Only respond with the name of the agent, nothing else.

                Example input:
                    - Agent handoffs: [spanishAgent, englishAgent]

                Example output:
                spanishAgent
                "
            """
            
            if debug:
                print(f"[DEBUG] Current prompt: {promptWithHandoffs}")
            
            process = subprocess.Popen(promptWithHandoffs, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
            stdout, stderr = process.communicate()
            
            if debug:
                print(f"[DEBUG] Stdout: {stdout}")
                print(f"[DEBUG] stderr: {stderr}")

            selectedAgentName = stdout.strip()
            
            selectedAgent = AgentRegistry.get_agent(selectedAgentName)
            
            if debug:
                print(f"[DEBUG] selectedAgent: {selectedAgent}")
                            
            return selectedAgent.run(prompt, debug)            
        
        

    def loop(self, prompt: str, exitCondition: str, debug: bool = False, sleepInterval: float = 1.0):
        response = ""
        lastResponse = ""
        runs = 0

        while True:
            promptForLoop = f"""
                ollama run {self.model} "You are now an AI agent.

                Agent information:
                - Agent name: {self.name}
                - Agent instruction: {self.instruction}
                - Conversation history: {response}
                - New prompt: {prompt}

                Follow these instructions precisely and provide a useful response."
            """
            
            if debug:
                print(f"[DEBUG] Prompt for loop: {promptForLoop}")
            
            process = subprocess.Popen(promptForLoop, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
            stdout, stderr = process.communicate()
            if debug:
                print(f"[DEBUG] Stdout: {stdout}")
                print(f"[DEBUG] stderr: {stderr}")
            
            lastResponse = stdout.strip()
            response += " " + lastResponse  

            if debug:
                print(f"[DEBUG] Agent Response: {lastResponse}")

            promptCheckExitCondition = f"""
                ollama run {self.model} "You are now an AI agent.

                Agent information:
                - Task: Decide if the conversation has met the exit condition.
                - Conversation history: {response}
                - Exit condition: {exitCondition}
                
                If the exit condition is met, respond with exactly: 'exit'. Otherwise, respond with 'continue'."
            """
            
            if debug:
                print(f"[DEBUG] Prompt for exit condition check: {promptCheckExitCondition}")

            process = subprocess.Popen(promptCheckExitCondition, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
            stdout, stderr = process.communicate()
            if debug:
                print(f"[DEBUG] Stdout: {stdout}")
                print(f"[DEBUG] stderr: {stderr}")

            exitCheck = stdout.strip().lower()

            if debug:
                print(f"[DEBUG] Exit Check Result: {exitCheck}")

            if exitCheck == "exit":
                if debug:
                    print(f"[DEBUG] Exit condition met. Last response: {lastResponse}")
                return lastResponse

            runs += 1
        
    
    
    def generateAgent(self, prompt: str, debug: bool = False) -> 'list[Agent]':
        promptCreateAgent = f"""
            ollama run {self.model} "You are now an AI agent.

            Agent information:
                - Agent name: {self.name}
                - Agent instruction: {self.instruction}
                - Prompt: {prompt}

            The above list defines you. You can't make any other info up.
            
            You need to make the agents that are asked in the prompt, make the agents using the json. Order the agents in the order on wich they're needed for the task.

            You need to give an output like this (valid JSON):

            {{
                "agents": [
                    {{
                        "name": "agent1",
                        "instruction": "agent1 instruction"
                    }},
                    {{
                        "name": "agent2",
                        "instruction": "agent2 instruction"
                    }}
                ]
            }}

            Extra instructions:
                - You need to only generate agents asked. So don't add unnecessary agents like tokenizer. 
                - Only Respond with valid json. Don't add anything else
                
            Follow these instructions precisely."
        """
        if debug:
            print(f"[DEBUG] Current prompt: {promptCreateAgent}")

        process = subprocess.Popen(
            ["ollama", "run", self.model],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=promptCreateAgent)

        if debug:
            print(f"[DEBUG] Stdout: {stdout}")
            print(f"[DEBUG] Stderr: {stderr}")

        try:
            data = json.loads(stdout.strip())

            if debug:
                print(f"[DEBUG] Data: {data}")
            
            if "agents" not in data:
                if debug:
                    print("[ERROR] JSON is missing 'agents' key.")
                return None

            agentObjects = []
            for agentInfo in data["agents"]:
                agent = Agent(
                    name=agentInfo["name"],
                    instruction=agentInfo["instruction"]
                )
                agentObjects.append(agent)

            if debug:
                for agent in agentObjects:
                    print(f"[DEBUG] New agent created: {agent.name}")

            if debug:
                print(f"[DEBUG] agentObjects: {agentObjects}")
            return agentObjects
            
        except json.JSONDecodeError as e:
            if debug:
                print(f"[ERROR] Failed to decode JSON: {e}")
            return None

        
        
        


