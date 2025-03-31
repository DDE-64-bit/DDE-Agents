import subprocess
import json

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


def checkOutputGuardrails(agent: 'Agent', response: str, debug: bool = False):
    # OpenAI
    if agent.openAI:
        from openai import OpenAI
        client = OpenAI()

        if agent.outputGuardrails != None:
            checkOutputGuardrailsPrompt = f"""
            You are now an AI safety compliance agent.

                - Your task: Evaluate if the provided output violates the established guardrails.
                - Guardrails: {agent.outputGuardrails}
                - Output: {response}

                Instructions:
                1. If the output violates any of the guardrails, respond strictly with: 'triggered'.
                2. If the output does NOT violate any of the guardrails, respond strictly with: 'ok'.
                3. You are not permitted to generate, interpret, or elaborate on the output in any way other than specified above.

                Adhere to these instructions precisely.
            """
            
            if debug:
                print(f"[DEBUG] Current prompt: {checkOutputGuardrailsPrompt}")
            
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": checkOutputGuardrailsPrompt,
                    }
                ]
            )
            
            if debug:
                print(f"[DEBUG] Completion: {completion}")
            
            if completion.choices[0].message.content == "ok":
                if debug:
                    print("[DEBUG] No guardrails triggered")
                return response
            elif completion.choices[0].message.content == "triggered":
                if debug:
                    print(f"[DEBUG] Guardrails is triggered with {response}")
                return f"Guardrails triggered"
            else:
                if debug:
                    print(f"[DEBUG] Guardrails couldn't be checked with the response: {response}")
                return f"Guardrails couldn't be checked"
        else:
            return response
        
    
    #Local
    elif not agent.openAI:
        if agent.outputGuardrails != None:
            checkOutputGuardrailsPrompt = f"""
                ollama run {agent.model} "You are now an AI safety compliance agent.

                - Your task: Evaluate if the provided output violates the established guardrails.
                - Guardrails: {agent.outputGuardrails}
                - Output: {response}

                Instructions:
                1. If the output violates any of the guardrails, respond strictly with: 'triggered'.
                2. If the output does NOT violate any of the guardrails, respond strictly with: 'ok'.
                3. You are not permitted to generate, interpret, or elaborate on the output in any way other than specified above.

                Adhere to these instructions precisely."
            """
            
            if debug:
                print(f"[DEBUG] Current prompt: {checkOutputGuardrailsPrompt}")
            
            process = subprocess.Popen(checkOutputGuardrailsPrompt, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
            stdout, stderr = process.communicate()
            
            if debug:
                print(f"[DEBUG] Stdout: {stdout}")
                print(f"[DEBUG] stderr: {stderr}")
            
            if stdout.strip() == "ok":
                if debug:
                    print("[DEBUG] No guardrails triggered")
                return response
            elif stdout.strip() == "triggered":
                if debug:
                    print(f"[DEBUG] Guardrails is triggered with {response}")
                return f"Guardrails triggered"
            else:
                if debug:
                    print(f"[DEBUG] Guardrails couldn't be checked with the response: {response}")
                return f"Guardrails couldn't be checked"
        else:
            return response



class Agent:
    def __init__(self, name: str, instruction: str, model: str = "llama3.1", tools: list = None, handoffs: list = None, outputs: list = None, inputGuardrails: str = None, outputGuardrails: str = None, openAI: bool = False):
        self.name = name
        self.instruction = instruction
        self.model = model if model is not None else "llama3.1"
        self.tools = tools if tools is not None else []
        self.handoffs = handoffs if handoffs is not None else []
        self.outputs = outputs if outputs is not None else []
        self.inputGuardrails = inputGuardrails
        self.outputGuardrails = outputGuardrails
        self.openAI = openAI
        
        AgentRegistry.register(self)

    def run(self, prompt: str, debug: bool = False, disableGuardrails: bool = False) -> str:
        if self.openAI:
            if debug:
                print(f"[DEBUG] Using openAI model: {self.model}")

        response = ""

        handoffsList = ", ".join([handoff.name for handoff in self.handoffs])
        if debug:
            print(f"[DEBUG] HandoffsList: {handoffsList}")

#---------------------------------------------------------------------------------------------------

        # OpenAI 
        if self.openAI:
            from openai import OpenAI
            client = OpenAI()
            
            # Guardrails
            if self.inputGuardrails != None:
                if  disableGuardrails == False:
                    checkInputGuardrailsPrompt = f"""
                        You are now an AI safety compliance agent.

                        - Your task: Evaluate if the provided prompt violates the established guardrails.
                        - Guardrails: {self.inputGuardrails}
                        - Input Prompt: {prompt}

                        Instructions:
                        1. If the prompt violates any of the guardrails, respond strictly with: 'triggered'.
                        2. If the prompt does NOT violate any of the guardrails, respond strictly with: 'ok'.
                        3. You are not permitted to generate, interpret, or elaborate on the prompt in any way other than specified above.

                        Adhere to these instructions precisely.
                    """
                    
                    if debug:
                        print(f"[DEBUG] Current prompt: {checkInputGuardrailsPrompt}")
                    
                    completion = client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {
                                "role": "user",
                                "content": checkInputGuardrailsPrompt,
                            }
                        ]
                    )
                    
                    if debug:
                        print(f"[DEBUG] completion: {completion}")

                    if completion.choices[0].message.content == "ok":
                        if debug:
                            print("[DEBUG] No guardrails triggered")
                    elif completion.choices[0].message.content == "triggered":
                        if debug:
                            print(f"[DEBUG] Guardrails is triggered with '{prompt}'")
                        return f"Guardrails triggered with '{prompt}'"
                    else:
                        if debug:
                            print(f"[DEBUG] Guardrails couldn't be checked with the prompt: '{prompt}'")
                        return f"Guardrails couldn't be checked with the prompt: '{prompt}'"
            
            
            
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



            # Run Handoffs
            if self.handoffs != []:
                promptWithHandoffs = f"""
                    You are now an AI agent.

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
                """
                
                if debug:
                    print(f"[DEBUG] Current prompt: {promptWithHandoffs}")
                
                completion = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": promptWithHandoffs,
                        }
                    ]
                )
                
                if debug:
                    print(f"[DEBUG] completion: {completion}")

                selectedAgentName = completion.choices[0].message.content
                
                selectedAgent = AgentRegistry.get_agent(selectedAgentName)
                
                if debug:
                    print(f"[DEBUG] selectedAgent: {selectedAgent}")
                                
                return selectedAgent.run(prompt, debug)              
                        
            


            # Run normal
            normalPrompt = f"""
                You are now an AI agent.

                Agent information:
                    - Agent name: {self.name}
                    - Agent instruction: {self.instruction}
                    - Prompt: {prompt}
                    - Extra info: {response}

                The above list defines you. You can't make any other info up.
                
                Follow these instructions precisely.
            """
            
            if debug:
                print(f"[DEBUG] Current prompt: {normalPrompt}")
            
            completion = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": normalPrompt,
                    }
                ]
            )
            
            if debug:
                print(f"[DEBUG] completion: {completion}")

            response += f"response of {self.name}: {completion.choices[0].message.content}"
            if disableGuardrails == True:
                return response
            elif disableGuardrails == False:
                return checkOutputGuardrails(self, completion.choices[0].message.content, debug)
            
            
#---------------------------------------------------------------------------------------------------
            
        # Local 
        elif not self.openAI:
            # Check input guardrails
            if self.inputGuardrails != None:
                if  disableGuardrails == False:
                    checkInputGuardrailsPrompt = f"""
                        ollama run {self.model} "You are now an AI safety compliance agent.

                        - Your task: Evaluate if the provided prompt violates the established guardrails.
                        - Guardrails: {self.inputGuardrails}
                        - Input Prompt: {prompt}

                        Instructions:
                        1. If the prompt violates any of the guardrails, respond strictly with: 'triggered'.
                        2. If the prompt does NOT violate any of the guardrails, respond strictly with: 'ok'.
                        3. You are not permitted to generate, interpret, or elaborate on the prompt in any way other than specified above.

                        Adhere to these instructions precisely."
                    """
                    
                    if debug:
                        print(f"[DEBUG] Current prompt: {checkInputGuardrailsPrompt}")
                    
                    process = subprocess.Popen(checkInputGuardrailsPrompt, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
                    stdout, stderr = process.communicate()
                    
                    if debug:
                        print(f"[DEBUG] Stdout: {stdout}")
                        print(f"[DEBUG] stderr: {stderr}")
                        
                    if stdout.strip() == "ok":
                        if debug:
                            print("[DEBUG] No guardrails triggered")
                    elif stdout.strip() == "triggered":
                        if debug:
                            print(f"[DEBUG] Guardrails is triggered with '{prompt}'")
                        return f"Guardrails triggered with '{prompt}'"
                    else:
                        if debug:
                            print(f"[DEBUG] Guardrails couldn't be checked with the prompt: '{prompt}'")
                        return f"Guardrails couldn't be checked with the prompt: '{prompt}'"
            
            
            
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
                        
            
            
            # Run Handoffs
            if self.handoffs != []:
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
                        
            
            if debug:
                stdout = ""

            # Run normal
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
            if disableGuardrails == True:
                return response
            elif disableGuardrails == False:
                return checkOutputGuardrails(self, stdout, debug)




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
                        "name": "descriptiveAgentName1",
                        "instruction": "agent1 instruction"
                    }},
                    {{
                        "name": "descriptiveAgentName2",
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
