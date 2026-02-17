from __future__ import annotations

import os
import json
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

DEFAULT_SENSITIVE_FEATURES = {"RACA_COR", "MES_NASCIMENTO", "ANO_NASCIMENTO"}

def fetch_high_risk_ids(db: Session, threshold: float, top_n: int) -> List[int]:
    rows = db.execute(
        text("""
            SELECT id_aluno_graduacao
            FROM output_modelo
            WHERE classificacao >= :thr
            ORDER BY classificacao DESC
            LIMIT :n
        """),
        {"thr": threshold, "n": top_n},
    ).all()
    return [int(r[0]) for r in rows]


def dominant_signal_groups(
    db: Session,
    aluno_ids: List[int],
    personas_n: int,
    sensitive: Optional[set[str]] = None,
) -> List[Dict[str, Any]]:
    if not aluno_ids:
        return []

    sensitive = sensitive or DEFAULT_SENSITIVE_FEATURES

    rows = db.execute(
        text("""
            SELECT DISTINCT ON (id_aluno_graduacao)
                id_aluno_graduacao,
                descricao,
                peso
            FROM peso_features
            WHERE id_aluno_graduacao = ANY(:ids)
              AND descricao IS NOT NULL
            ORDER BY id_aluno_graduacao, ABS(peso) DESC
        """),
        {"ids": aluno_ids},
    ).mappings().all()

    per_label: Dict[str, List[int]] = {}
    for r in rows:
        desc = (r["descricao"] or "").strip()
        if not desc or desc in sensitive:
            continue
        per_label.setdefault(desc, []).append(int(r["id_aluno_graduacao"]))

    ranked = sorted(per_label.items(), key=lambda kv: len(kv[1]), reverse=True)[:personas_n]
    return [{"label": label, "aluno_ids": ids, "size": len(ids)} for label, ids in ranked]


def aggregate_signals(db: Session, aluno_ids: List[int], sensitive: Optional[set[str]] = None) -> List[Dict[str, Any]]:
    if not aluno_ids:
        return []

    sensitive = sensitive or DEFAULT_SENSITIVE_FEATURES

    rows = db.execute(
        text("""
            SELECT
              descricao,
              CASE WHEN AVG(peso) > 0 THEN 'aumenta_risco' ELSE 'reduz_risco' END AS direction,
              COUNT(DISTINCT id_aluno_graduacao)::float / :den AS share,
              AVG(ABS(peso)) AS avg_abs_peso,
              COUNT(*) AS occurrences
            FROM peso_features
            WHERE id_aluno_graduacao = ANY(:ids)
              AND descricao IS NOT NULL
            GROUP BY descricao
            ORDER BY AVG(ABS(peso)) DESC, share DESC
            LIMIT 30
        """),
        {"ids": aluno_ids, "den": float(len(aluno_ids))},
    ).mappings().all()

    out: List[Dict[str, Any]] = []
    for r in rows:
        desc = (r["descricao"] or "").strip()
        if not desc or desc in sensitive:
            continue
        out.append({
            "descricao": desc,
            "direction": r["direction"],
            "share": float(r["share"]) if r["share"] is not None else 0.0,
            "avg_abs_peso": float(r["avg_abs_peso"]) if r["avg_abs_peso"] is not None else 0.0,
            "occurrences": int(r["occurrences"]),
        })
    return out


def population_stats(db: Session, threshold: float) -> Dict[str, Any]:
    row = db.execute(
        text("""
            SELECT
              COUNT(*) AS total_scored,
              SUM(CASE WHEN classificacao >= :thr THEN 1 ELSE 0 END) AS high_risk_count
            FROM output_modelo
        """),
        {"thr": threshold},
    ).mappings().first()

    return {
        "total_scored": int(row["total_scored"]) if row else 0,
        "high_risk_count": int(row["high_risk_count"]) if row and row["high_risk_count"] is not None else 0,
        "high_risk_threshold": threshold,
    }


def build_persona_inputs(
    db: Session,
    high_risk_ids: List[int],
    threshold: float,
    personas_n: int,
) -> Dict[str, Any]:
    pop = population_stats(db, threshold=threshold)

    groups = dominant_signal_groups(db, high_risk_ids, personas_n=personas_n)

    persona_inputs: List[Dict[str, Any]] = []
    for g in groups:
        sig = aggregate_signals(db, aluno_ids=g["aluno_ids"])
        persona_inputs.append({
            "group_label": g["label"],
            "group_size": g["size"],
            "top_signals": sig[:10],
        })

    return {"population": pop, "groups": persona_inputs}


def _extract_json_object(text_content: str) -> Optional[str]:
    cleaned = re.sub(r"```(?:json)?", "", text_content, flags=re.IGNORECASE).replace("```", "").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return cleaned[start:end+1]


def generate_personas_with_groq(
    payload: Dict[str, Any],
    personas_n: int,
) -> Tuple[Optional[List[Dict[str, Any]]], Optional[Dict[str, Any]]]:

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None, {"type": "missing_api_key", "message": "GROQ_API_KEY não encontrada"}

    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    prompt = f"""
        Crie {personas_n} personas de estudantes com ALTO risco de evasão a partir de GRUPOS diferentes (dados agregados, não individuais).

        Regras obrigatórias:
        - Retorne SOMENTE JSON válido (sem markdown, sem texto fora do JSON).
        - Não use nomes próprios (ex.: João, Maria). Use rótulos de persona (ex.: "Sobrecarga de disciplinas").
        - Cada persona DEVE ser diferente: use sinais distintos; não repetir o mesmo conjunto de common_signals.
        - Use APENAS os sinais do grupo correspondente (group_label/top_signals).
        - Não inventar dados pessoais e não usar atributos sensíveis.
        - Não use quebras de linha. Retorne JSON MINIFICADO em uma única linha.
        - Não use blocos ``` nem markdown.

        Entrada (agregada):
        {payload}

        Saída (JSON):
        {{
        "personas": [
            {{
            "name": "nome curto da persona",
            "summary": "2 frases diretas sobre o padrão de risco baseado nos sinais do grupo",
            "common_signals": ["até 4 descricoes exatamente como em top_signals"],
            "who_to_interview": "precisa ser aluno; no máximo 160 caracteres",
            "confidence_note": "1 frase: baseado em dados agregados"
            }}
        ]
        }}
        """.strip()

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {
        "model": model,
        "temperature": 0.1,
        "top_p": 1,
        "max_completion_tokens": 700,
        "messages": [
            {"role": "system", "content": "Responda somente com um objeto JSON válido. Sem texto extra."},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
    }

    try:
        r = httpx.post(url, json=body, headers=headers, timeout=60.0)
        if r.status_code >= 400:
            return None, {"type": "http_error", "status_code": r.status_code, "response_text": r.text[:4000]}

        data = r.json()
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        if not content:
            return None, {"type": "empty_response", "message": "Groq retornou resposta vazia", "raw": str(data)[:2000]}

        json_str = _extract_json_object(content)
        if not json_str:
            return None, {"type": "invalid_json", "message": "Não foi possível extrair JSON", "raw": content[:2000]}

        try:
            obj = json.loads(json_str)
        except Exception as e:
            return None, {"type": "invalid_json", "message": str(e), "raw": content[:2000]}

        personas = obj.get("personas")
        if not isinstance(personas, list):
            return None, {"type": "invalid_format", "message": "JSON não contém lista 'personas'", "raw": json_str[:2000]}

        return personas, None

    except httpx.TimeoutException:
        return None, {"type": "timeout", "message": "Timeout chamando Groq"}
    except Exception as e:
        return None, {"type": "exception", "message": str(e)}