class ModelConfig:
    _model = "llama3.1"
    _openai = False

    @classmethod
    def setDefaultModel(cls, model: str, openAI: bool):
        cls._model = model
        cls._openai = openAI

    @classmethod
    def getDefaultModel(cls):
        return cls._model

    @classmethod
    def getDefaultOpenAI(cls):
        return cls._openai
