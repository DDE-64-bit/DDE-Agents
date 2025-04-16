import subprocess
import os
import base64
from agent.CleanOutput import cleanOutput

from agent.Config import ModelConfig

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

def _checkOutputGuardrails(agent: 'Agent', response: str, debug: bool = False):
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
            
            stdout = agent.runOpenAI(checkOutputGuardrailsPrompt, debug)
            
            if stdout.choices[0].message.content == "ok":
                if debug:
                    print("[DEBUG] No guardrails triggered")
                return response
            elif stdout.choices[0].message.content == "triggered":
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
    def __init__(self, name: str, instruction: str, model: str = None, tools: list = None, handoffs: list = None, outputs: list = None, inputGuardrails: str = None, outputGuardrails: str = None, openAI: bool = False, images: list = None, selectiveToolUse: bool=True):
        self.name = name
        self.instruction = instruction
        
        
        if model == None:
            if ModelConfig.getDefaultOpenAI() == True: # niet voor deze agent wel algemeen
                self.model = ModelConfig.getDefaultModel()
                self.openAI = ModelConfig.getDefaultOpenAI()
            else: # voor geen van beide 
                self.model = "llama3.1"
                self.openAI = False
        else:
            self.model = model
            self.openAI = openAI

        self.selectiveToolUse = selectiveToolUse
        self.tools = tools if tools is not None else []
        self.handoffs = handoffs if handoffs is not None else []
        self.outputs = outputs if outputs is not None else []
        self.inputGuardrails = inputGuardrails
        self.outputGuardrails = outputGuardrails
        self.images = images if images is not None else []

        AgentRegistry.register(self)



    def runTools(self, prompt: str, debug: bool = False):
        response = ""

        for tool in self.tools[:]:
            if callable(tool):  
                if debug:
                    print(f"[DEBUG] {tool.__name__} is een functie (def).")

                try:
                    if hasattr(tool, '__wrapped__'):
                        toolResult = tool(prompt=prompt)
                        if debug:
                            print(f"[DEBUG] toolresult: {toolResult}")
                    else:
                        toolResult = tool()
                        if debug:
                            print(f"[DEBUG] toolresult: {toolResult}")

                    response += f" response tool: {tool.__name__}: {toolResult} \n"

                    if debug:
                        print(f"[DEBUG] Response {tool.__name__}: {toolResult}")

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
                        print(f"[DEBUG] Response {tool.name}: {toolResult}")
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
                print(f"[DEBUG] response tool: {response}")

        return response

    
    
    
    def runOpenAI(self, prompt: str, debug: bool = False):
        from openai import OpenAI
        client = OpenAI()
        
        if debug:
            print(f"[DEBUG] Current prompt: {prompt}")
        
        
        if self.images != []:
            content = [{"type": "text", "text": prompt}]
            
            for imagePath in self.images:
                if not os.path.exists(imagePath):
                    if debug:
                        print(f"[DEBUG] Niet gevonden: {imagePath}")
                    continue
                
                with open(imagePath, "rb") as f:
                    base64Image = base64.b64encode(f.read()).decode("utf-8")
                    content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64Image}"
                        }
                    })
                    
            stdout = client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": content
                }],
                max_tokens=4000
            )
        elif self.images == []:
            stdout = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ]
            )
        else:
            if debug:
                print(f"[DEBUG] Error in runOpenAI, self.images is not an allowed value: {self.images}")
            
            return "If this happens you better open a github issue."
        
        if debug:
            print(f"[DEBUG] completion: {stdout}")
        
        return stdout
    
    
    
    def runLocalModel(self, prompt: str, debug: bool = False) -> str:
        if self.images:
            for imagePath in self.images:
                if not os.path.exists(imagePath):
                    if debug:
                        print(f"[DEBUG] Niet gevonden: {imagePath}")
                    continue

                cmd = ["ollama", "run", self.model]
                if debug:
                    print(f"[DEBUG] Running: {' '.join(cmd)} with image: {imagePath}")
                    print(f"[DEBUG] Prompt: {prompt}")

                # Encode the image to base64
                with open(imagePath, "rb") as image_file:
                    base64Image = base64.b64encode(image_file.read()).decode("utf-8")

                image_instruction = f"""
                <image>\ndata:image/jpeg;base64,{base64Image}\n</image>
                {prompt}
                """

                process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                stdout, stderr = process.communicate(input=image_instruction)

                if debug:
                    print(f"[DEBUG] Stdout: {stdout}")
                    print(f"[DEBUG] stderr: {stderr}")

                return stdout if stdout else stderr

        else:
            cmd = ["ollama", "run", self.model]
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate(input=prompt)

            if debug:
                print(f"[DEBUG] Stdout: {stdout}")
                print(f"[DEBUG] stderr: {stderr}")

            return stdout if stdout else stderr



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
                    
                    stdout = self.runOpenAI(checkInputGuardrailsPrompt, debug)

                    if stdout.choices[0].message.content == "ok":
                        if debug:
                            print("[DEBUG] No guardrails triggered")
                    elif stdout.choices[0].message.content == "triggered":
                        if debug:
                            print(f"[DEBUG] Guardrails is triggered with '{prompt}'")
                        return f"Guardrails triggered with '{prompt}'"
                    else:
                        if debug:
                            print(f"[DEBUG] Guardrails couldn't be checked with the prompt: '{prompt}'")
                        return f"Guardrails couldn't be checked with the prompt: '{prompt}'"
            
            
            
            # Run Tools
            if self.tools != []:
                response = self.runTools(prompt, debug)


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
                
                if self.openAI:
                    stdout = self.runOpenAI(promptWithHandoffs, debug)
                    selectedAgentName = stdout.choices[0].message.content
                elif not self.openAI:
                    stdout = self.runLocalModel(promptWithHandoffs, debug)

                    selectedAgentName = stdout.strip()
                
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
            
            stdout = self.runOpenAI(normalPrompt, debug)

            response += f"response of {self.name}: {stdout.choices[0].message.content}"
            if disableGuardrails == True:
                return response
            elif disableGuardrails == False:
                return _checkOutputGuardrails(self, stdout.choices[0].message.content, debug)
            
            
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
                    
                    stdout = self.runLocalModel(checkInputGuardrailsPrompt, debug)
                        
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
                response = self.runTools(prompt, debug)
                        
            
            
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
                
                stdout = self.runLocalModel(promptWithHandoffs, debug)

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
            
            stdout = self.runLocalModel(normalPrompt, debug)

            response += f"response of {self.name}: {stdout}"
            if disableGuardrails == True:
                return response
            elif disableGuardrails == False:
                return _checkOutputGuardrails(self, stdout, debug)




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
                - Only Respond with valid json. Don't add anything else so no: '```json'
                
            Follow these instructions precisely."
        """
        
        
        if self.openAI:
            stdout = self.runOpenAI(promptCreateAgent, debug)
        else:
            stdout = self.runLocalModel(prompt, debug)
        
        if debug:
            print(f"\n[DEBUG] Raw stdout before cleanOutput:\n{stdout}\n")


        if self.openAI:
            data = cleanOutput(stdout.choices[0].message.content, self.openAI, debug=debug)
        elif not self.openAI:
            data = cleanOutput(stdout, self.openAI, debug=debug)
        
        if debug:
            print(f"[DEBUG] Raw stdout: {stdout}")
            print(f"[DEBUG] Parsed data: {data}")
        
        if "agents" not in data:
            if debug:
                print("[ERROR] JSON is missing 'agents' key.")
            return None

        agentObjects = []
        for agentInfo in data["agents"]:
            agent = Agent(
                name=agentInfo["name"],
                instruction=agentInfo["instruction"],
                model=self.model,
                openAI=self.openAI,
            )
            agentObjects.append(agent)

        if debug:
            for agent in agentObjects:
                print(f"[DEBUG] New agent created: {agent.name}")

        if debug:
            print(f"[DEBUG] agentObjects: {agentObjects}")
        return agentObjects
