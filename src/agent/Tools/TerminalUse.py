import subprocess
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agent.Agent import Agent
from agent.Config import ModelConfig
from agent.CleanOutput import cleanOutput
from agent.LLM import runLLM

ModelConfig.setDefaultModel("llama3.1", False)

debug = True

def _makeSteps(task: str, debug: bool = False):
    prompt = f"""
        You need to break down the given task into steps.
        
        task = {task}
    """
    
    if debug:
        print(f"[DEBUG]: prompt: {prompt}")
    
    steps = runLLM(prompt=prompt, debug=debug)
    
    if debug:
        print(f"[DEBUG]: steps: {steps}")
    
    return steps

def _makeCommands(steps: str, debug: bool = False):
    prompt = f"""
        "You have to make commands for each step only answer in usable json.
        
        Steps to task: {steps}
        
        {{
            "commands": [
                {{
                    "id": "1",
                    "command": "{{enter command here}}"
                }},
                {{
                    "id": "2",
                    "command": "{{enter command here}}"
                }}
            ]
        }}

        Extra instructions:
            - You need to only generate command for the given steps. So don't add unnecessary steps. 
            - Only Respond with valid json. Don't add anything else so no: '''json or ```
            - NEVER use interactive tools like nano/vim/emacs.
            - Use shell commands like `echo` or `printf` to insert text into files.
            
        Follow these instructions precisely."
    """
    
    if debug:
        print(f"[DEBUG]: prompt: {prompt}")
    
    commands = runLLM(prompt=prompt, debug=debug)
    
    if debug:
        if ModelConfig.getDefaultOpenAI():
            #print(f"[DEBUG]: commands['choices'][0]['message']['content']: {commands['choices'][0]['message']['content']}")
            print(f"[DEBUG]: commands: {commands}")
        elif not ModelConfig.getDefaultOpenAI():
            print(f"[DEBUG]: commands: {commands}")
    
    if ModelConfig.getDefaultOpenAI():
        return commands.choices[0].message.content
    return commands

def _runCommands(commands: str, debug: bool = False):
    response = cleanOutput(stdout=commands, openAI=ModelConfig.getDefaultOpenAI(), debug=debug)
    
    if response and "commands" in response:
        for cmd in response["commands"]:
            try:
                if debug:
                    print(f"Running command {cmd['id']}: {cmd['command']}")
                result_cmd = subprocess.run(cmd["command"], shell=True, capture_output=True, text=True)
                if debug:
                    print(f"[OUTPUT]\n{result_cmd.stdout}")
                
                    if result_cmd.stderr:
                        print(f"[ERROR]\n{result_cmd.stderr}")
            except Exception as e:
                print(f"[EXCEPTION] Failed to run command {cmd['id']}: {e}")
    else:
        print("No valid commands found.")
        
def terminalUse(task: str, debug: bool = False):
    steps = _makeSteps(task=task, debug=debug)
    commands = _makeCommands(steps=steps, debug=debug)
    r = _runCommands(commands=commands, debug=debug)
    
    return r

if __name__ == "__main__":
    print(terminalUse(task="make a file called 1 and in it put a funny oneliner. on linux", debug=debug))
