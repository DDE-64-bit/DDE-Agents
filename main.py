from Agent import Agent

tutorAgent = Agent(
    name="tutorAgent",
    instruction="You help with homework tasks.",
    inputGuardrails="The prompt can only be math related.",
    outputGuardrails="The output can not contain a direct answer.",
    model="gpt-3.5-turbo",
    openAI=True,
)

if __name__ == "__main__":
    print(tutorAgent.run(input("prompt: "), debug=True, disableGuardrails=True))
