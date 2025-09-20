from enum import StrEnum


class ResponseEnum(StrEnum):
    MathAgent = "MathAgent"
    KnowledgeAgent = "KnowledgeAgent"
    UnsupportedLanguage = "UnsupportedLanguage"
    Error = "Error"
