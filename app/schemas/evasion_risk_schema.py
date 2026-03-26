from pydantic import BaseModel


class CourseEvasionRiskResponse(BaseModel):
    id_curso: int
    nome_curso: str
    id_unidade: int
    total_alunos: int
    risco_medio: float
    risco_percentual: float
    proporcao_alto_risco: float
    proporcao_alto_risco_percentual: float
    limiar_alto_risco: float


class UnidadeEvasionRiskResponse(BaseModel):
    id_unidade: int
    nome_unidade: str
    total_alunos: int
    risco_medio: float
    risco_percentual: float
    proporcao_alto_risco: float
    proporcao_alto_risco_percentual: float
    limiar_alto_risco: float