from __future__ import annotations
import os
import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_SENSITIVE_FEATURES = {
    "RACA_COR",
    "MES_NASCIMENTO",
    "ANO_NASCIMENTO"
}

import re

HUMAN_LABELS = {
    "PERC_REPROVACAO": "percentual de reprovação",
    "QTD_DISCIPLINAS": "quantidade de disciplinas cursadas",
    "AVG_FREQUENCIA": "frequência média (%)",
    "MIN_FREQUENCIA": "frequência mínima (%)",
    "AVG_NOTA": "média de notas (%)",
    "MEDIAN_NOTA": "mediana de notas (%)",
    "IDADE_MATRICULA": "idade na matrícula",
    "COTAS": "cotas",
}

def parse_range(feature_text: str) -> str:
    t = feature_text
    t = re.sub(r"[-+]?\d+(\.\d+)?", "", t)
    t = t.replace("<=", "").replace(">=", "").replace("<", "").replace(">", "")
    t = " ".join(t.split())
    return t.strip()

def driver_phrase(item: dict) -> str:
    desc = (item.get("descricao") or "").strip()
    label = HUMAN_LABELS.get(desc, desc.lower() if desc else "fator")
    raw = item.get("feature") or ""
    qual = parse_range(raw)
    direction = "aumenta o risco" if float(item.get("peso", 0)) > 0 else "reduz o risco"
    if qual:
        return f"{label} ({qual}) — {direction}"
    return f"{label} — {direction}"


def risk_bucket(score: Optional[float]) -> Tuple[str, Optional[bool]]:
    """
    Retorna (risk_level, needs_attention)
    Ajuste thresholds aqui quando você calibrar o modelo.
    """
    if score is None:
        return ("INDEFINIDO", None)
    if score >= 0.70:
        return ("ALTO", True)
    if score >= 0.40:
        return ("MEDIO", True)
    return ("BAIXO", False)


def sanitize_features(
    features: List[Dict[str, Any]],
    sensitive: Optional[set[str]] = None,
) -> List[Dict[str, Any]]:
    sensitive = sensitive or DEFAULT_SENSITIVE_FEATURES
    out: List[Dict[str, Any]] = []
    for f in features:
        desc = (f.get("descricao") or "").strip()
        if desc in sensitive:
            continue
        out.append(
            {
                "feature": f.get("feature"),
                "peso": float(f.get("peso")),
                "descricao": desc,
            }
        )
    return out

def fetch_xai_from_db(db: Session, aluno_id: int, limit: int = 10) -> Dict[str, Any]:
    om = db.execute(
        text(
            """
            SELECT classificacao
            FROM output_modelo
            WHERE id_aluno_graduacao = :aid
            """
        ),
        {"aid": aluno_id},
    ).mappings().first()

    risk_score = float(om["classificacao"]) if om and om["classificacao"] is not None else None
    risk_level, needs_attention = risk_bucket(risk_score)

    feats = db.execute(
        text(
            """
            SELECT feature, peso, descricao
            FROM peso_features
            WHERE id_aluno_graduacao = :aid
            ORDER BY ABS(peso) DESC
            LIMIT :lim
            """
        ),
        {"aid": aluno_id, "lim": limit},
    ).mappings().all()

    feats_list = [dict(r) for r in feats]

    top_negative = sanitize_features([f for f in feats_list if float(f.get("peso", 0)) < 0][:5])
    top_positive = sanitize_features([f for f in feats_list if float(f.get("peso", 0)) > 0][:5])

    drivers = [driver_phrase(f) for f in (top_negative + top_positive)]

    return {
        "aluno_id": aluno_id,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "needs_attention": needs_attention,
        "explanation": {
            "top_negative": top_negative,
            "top_positive": top_positive,
        },
        "drivers": drivers,
    }

def generate_groq_summary(payload: Dict[str, Any]) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None, {"type": "missing_api_key", "message": "GROQ_API_KEY não encontrada no ambiente"}

    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    neg = sanitize_features(payload["explanation"]["top_negative"])
    pos = sanitize_features(payload["explanation"]["top_positive"])

    prompt = f"""
        Escreva um feedback acadêmico em PT-BR em TEXTO PURO (sem markdown, sem listas, sem quebras de linha).
        2 a 3 frases no total.

        Regras:
        - Não invente causas. Não use "alta" ou "baixa" reprovação se isso não estiver explícito nos drivers.
        - Use APENAS os drivers fornecidos para justificar.
        - Se risk_level=BAIXO e needs_attention=false: tom de manutenção (monitorar, manter rotina).
        - Se needs_attention=true: tom de intervenção (ações práticas).
        - Não use quebras de linha. Retorne JSON MINIFICADO em uma única linha.
        - Não use blocos ``` nem markdown.

        Dados:
        risk_level={payload.get("risk_level")}
        needs_attention={payload.get("needs_attention")}
        drivers={payload.get("drivers", [])[:3]}
        """.strip()

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {
        "model": model,
        "temperature": 0.0,
        "top_p": 1,
        "max_completion_tokens": 1200,
        "messages": [
            {"role": "system", "content": "Você escreve análises curtas, claras e responsáveis."},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
    }

    try:
        r = httpx.post(url, json=body, headers=headers, timeout=60.0)
        if r.status_code >= 400:
            return None, {
                "type": "http_error",
                "status_code": r.status_code,
                "response_text": r.text[:4000],
            }

        data = r.json()
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

        if not content:
            return None, {
                "type": "empty_response",
                "message": "Groq retornou resposta vazia",
                "raw": str(data)[:4000],
            }

        return content, None

    except httpx.TimeoutException:
        return None, {"type": "timeout", "message": "Timeout chamando Groq"}
    except Exception as e:
        return None, {"type": "exception", "message": str(e)}

def generate_personas_with_groq(signals: List[Dict[str, Any]], pop: Dict[str, Any], personas_n: int) -> Tuple[Optional[List[Dict[str, Any]]], Optional[Dict[str, Any]]]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None, {"type": "missing_api_key", "message": "GROQ_API_KEY não encontrada"}

    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    top_signals = signals[:12]

    prompt = f"""
Crie {personas_n} personas de estudantes com ALTO risco de evasão com base em sinais agregados (não individuais).
TEXTO PURO: sem markdown, sem listas com hífen, sem bullets, sem títulos com **, sem quebras de linha.
Não invente dados pessoais e não use atributos sensíveis.

Entrada:
- Estatísticas do grupo: {pop}
- Sinais mais associados ao alto risco (descricao, direction, share, avg_abs_peso): {top_signals}

Saída obrigatória: um JSON válido (apenas JSON, sem texto extra) no formato:
{{
  "personas": [
    {{
      "name": "nome curto",
      "summary": "2 frases diretas descrevendo o perfil e por que está em risco (baseado nos sinais)",
      "common_signals": ["até 4 descricoes exatamente como vieram"],
      "suggested_actions": ["até 2 ações, cada uma no máximo 120 caracteres"],
      "confidence_note": "no máximo 120 caracteres"
    }}
  ]
}}
""".strip()