from Config import ModelConfig

import subprocess

def runLLM(prompt: str, debug: bool = False):
    
    if debug:
        print(f"[DEBUG] ModelConig.getDefaultOpenAI: {ModelConfig.getDefaultOpenAI()}")
        print(f"[DEBUG] ModelConig.getDefaultModel: {ModelConfig.getDefaultModel()}")
    
    
    
    
    if ModelConfig.getDefaultOpenAI():
        from openai import OpenAI
        client = OpenAI()
        
        stdout = client.chat.completions.create(
            model=ModelConfig.getDefaultModel(),
            messages=[{
                "role": "user",
                "content": prompt
            }],
            max_tokens=4000
        )
    elif not ModelConfig.getDefaultOpenAI():
        cmd = ["ollama", "run", ModelConfig.getDefaultModel()]
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate(input=prompt)
        
    if debug:
        print(f"[DEBUG] stdout: {stdout}")
    
    return stdout