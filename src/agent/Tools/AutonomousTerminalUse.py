import subprocess
import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agent.Agent import Agent
from agent.Config import ModelConfig
from agent.CleanOutput import cleanOutput
from agent.LLM import runLLM
from agent.Tool import dynamicTool

def _getSteps(task: str, debug: bool = False):
    getStepsPrompt = f"""
        You need to give a few bulletpoints back for easy doable steps to accomplish the tasks. 1 step needs to be able to be done by 1 command.
        
        task: {task}
    """
    
    if debug:
        print(f"[DEBUG] getStepsPrompt: {getStepsPrompt}")
    
    steps = runLLM(prompt=getStepsPrompt, debug=debug)
    
    if debug:
        print(f"[DEBUG] autonomous terminal use steps: {steps}")
    
    return steps

def _makeCommand(task: str, steps: str, previousCommand: str, debug: bool = False):
    makeCommandPrompt = f"""
        You need to give a command based on the following information to get to closer to completing the task.
        
        task: {task}
        steps to task: {steps}
        previous command: {previousCommand}
        
        Now only respond with the command. Dont add anything else!! not 'oke ill do that' not ```bash or shell or whatever only the pure command.
    """

    if debug:
        print(f"[DEBUG] makeCommandPrompt: {makeCommandPrompt}")
        
    command = runLLM(prompt=makeCommandPrompt, debug=debug)
    
    if debug:
        print(f"[DEBUG] command: {command}")
    
    return command

def autonomousTerminalUse(task: str, debug: bool = False):
    currentCommand = ""
    commands = ""
    steps = _getSteps(task=task, debug=debug)
    
    while True:
        currentCommand =_makeCommand(task=task, steps=steps, previousCommand=currentCommand, debug=debug)
        
        if ModelConfig.getDefaultOpenAI():
            currentCommand = currentCommand.choices[0].message.content
        
        process = subprocess.Popen(stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate(input=currentCommand)
    
if __name__ == "__main__":
    ModelConfig.setDefaultModel("gpt-4o", True)
    