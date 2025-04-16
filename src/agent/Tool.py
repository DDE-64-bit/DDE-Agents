import inspect
import re
import json
import functools

# from functools import wraps

from agent.Agent import Agent
from agent.Config import ModelConfig

debug = False

def extract_json(raw: str, debug: bool = False) -> dict | None:
    raw = re.sub(r"```(?:json)?", "", raw)
    raw = raw.replace("```", "").strip()

    if debug:
        print(f"[DEBUG] Cleaned raw:\n{raw}")

    match = re.search(r'({\s*"parameters"\s*:\s*{[^{}]*}\s*})', raw, re.DOTALL)
    if not match:
        print("[ERROR] No valid JSON object found in output.")
        if debug:
            print(f"[DEBUG] Raw output was:\n{raw}")
        return None
    

    try:
        json_obj = json.loads(match.group(0))

        params = json_obj.get("parameters", {})
        for key, value in params.items():
            if isinstance(value, str):
                if value.lower() == "true":
                    params[key] = True
                elif value.lower() == "false":
                    params[key] = False
                elif value.isdigit():
                    params[key] = int(value)
        
        return json_obj
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON decode failed: {e}")
        return None




def dynamicTool(function):
    @functools.wraps(function)
    def wrapper(*args, prompt=None, **kwargs):
        sig = inspect.signature(function)

        try:
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            return function(*args, **kwargs)
        
        except TypeError as e:
            if debug:
                print(f"[DEBUG] Argument mismatch, AI gaat invullen: {e}")

        source = inspect.getsource(function)
        param_list = list(sig.parameters.keys())

        dynamicAgent = Agent(
            name="dynamicAgent",
            instruction="",
            model=ModelConfig.getDefaultModel(),
            openAI=ModelConfig.getDefaultOpenAI(),
            outputGuardrails="You need to check if the given parameters will not cause problems, so dont't use spaces in links. Or other erros that can be prevented."
        )
        
        agent  = Agent(
            name="agent",
            instruction="",
            model=ModelConfig.getDefaultModel(),
            openAI=ModelConfig.getDefaultOpenAI(),
        )

        prompt_for_params = f"""
            You are an AI agent.

            Agent details:
            - Name: {dynamicAgent.name}
            - Instruction: {dynamicAgent.instruction}
            - Function parameters: {param_list}
            - Function code: {source}
            - User prompt: {prompt}

            This defines your identity. Do not invent or assume any additional context.

            Your job is to infer the correct function parameter values based solely on the user prompt. 

            Respond with **only valid JSON**, like:

            {{
                "parameters": {{
                    "parameter1": "value1",
                    "parameter2": "value2"
                }}
            }}

            Strict rules:
            - No prose, no explanations, no commentary.
            - No code blocks or markdown formatting (no triple backticks).
            - Output must start with '{{' and end with '}}'.
            - Only include parameters listed in the function signature.
            - The JSON must be parseable with `json.loads()` in Python.
            """



        if agent.openAI:
            stdout = agent.runOpenAI(prompt_for_params, debug=debug)
            rawOutput = stdout.choices[0].message.content.strip()
        elif not agent.openAI:
            stdout = agent.runLocalModel(prompt_for_params, debug=debug)
            rawOutput = stdout.strip()
        

        data = extract_json(rawOutput, debug=debug)
        
        if data is None:
            return None


        #clean_output = json_match.group(1)

        # voor openAI 
        # try:
        #     data = json.loads(data)
        # except json.JSONDecodeError as e:
        #     print(f"[ERROR] Failed to parse JSON: {e}")
        #     return None

        if "parameters" not in data:
            print("[ERROR] JSON is missing 'parameters' key.")
            return None

        if debug:
            print("Running function")
        return function(**data["parameters"])

    wrapper.__dynamic_tool__ = True
    return wrapper



# @dynamicTool
# def _getWeatherData(city: str):
#     if city.lower() == "london":
#         return "London: sun"
#     elif city.lower() == "singapore":
#         return "Singapore: amazing weather"
#     elif city.lower() == "washington dc":
#         return "Washington DC: thunder"
#     else:
#         return f"{city}: no weather data found."

# agent = Agent(
#     name="agent",
#     instruction="You need to run the tools based on the prompt",
#     model="gpt-4o",
#     openAI=True,
#     tools=[_getWeatherData]
# )


# if __name__ == "__main__":
#     r = agent.run(input("prompt: "), debug=debug, disableGuardrails=False)
#     print(r)