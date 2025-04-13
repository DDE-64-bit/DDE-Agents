import re
import json

def cleanOutput(stdout: any, openAI: bool, debug: bool = False): 
    try:
        # Als stdout al een dict is, direct teruggeven
        if isinstance(stdout, dict):
            if debug:
                print("[DEBUG] Output is already a dict")
                print(f"[DEBUG] data: {stdout}")
            return stdout

        content = stdout.strip()

        # Strip eventueel markdown zoals ```json\n...\n```
        clean_output = re.sub(r"^```(?:json)?\n|\n```$", "", content)

        data = json.loads(clean_output)

        if debug:
            print(f"[DEBUG] openAI: {openAI}")
            print(f"[DEBUG] data: {data}")

        return data

    except Exception as e:
        if debug:
            print(f"[ERROR] Failed to clean/parse output: {e}")
        return None
