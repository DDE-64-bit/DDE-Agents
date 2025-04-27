# Note: LINUX ONLY

import subprocess
import json
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agent.Agent import Agent
from agent.Config import ModelConfig
from agent.CleanOutput import cleanOutput
from agent.LLM import runLLM
from agent.Tool import dynamicTool

debug = False

@dynamicTool
def createFile(fileName: str, content: str):
    """_summary_

    Args:
        fileName (str): name of the file that has to be created + the file extention sepparated with a "."
        content (str): the start content of the file, if you want to create an empty file give content the value of "None"
    """
    
    if debug:
        print(f"[DEBUG] filename: {fileName}")
        print(f"[DEBUG] content: {content}")
    
    if content.lower() == "none":
        try:
            cmd = ["touch", fileName]
            subprocess.run(cmd, check=True)
        except:
            print(f"[ERROR] \"{fileName}\" couldn't be created")
    else:
        try:
            cmd = ["echo", content, ">", fileName]
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except:
            print(f"[ERROR] \"{fileName}\" couldn't be created with \"{content}\" as content")

if __name__ == "__main__":
    ModelConfig.setDefaultModel("gpt-4o", True)
    debug = True
    
    
    agent = Agent(
        name="agent",
        instruction="",
        tools=[createFile],
    )
    
    # agent.run(prompt="make a file called bella.py and in it put print(\"hi bella!!!\")", debug=True)
    createFile(prompt="make a file called bella.py and in it put print(\"hi bella!!!\")")
