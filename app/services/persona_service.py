from __future__ import annotations

import os
import json
import re
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from threading import Lock, Thread

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

CACHE_TTL = timedelta(hours=1)

_personas_cache = {
    "expires": datetime.min,
    "data": None,
    "refreshing": False,
    "last_error": None,
}

_cache_lock = Lock()

DEFAULT_SENSITIVE_FEATURES = {"RACA_COR", "MES_NASCIMENTO", "ANO_NASCIMENTO"}

# --- Funções antigas mantidas para compatibilidade (não usadas mais no caminho quente) ---
# fetch_high_risk_ids, population_stats, dominant_signal_groups e aggregate_signals faziam,
# juntas, "2 + personas_n" round-trips ao banco (uma query por persona dentro do loop de
# build_persona_inputs). fetch_high_risk_and_population() e build_persona_inputs() abaixo
# substituem essa cadeia inteira por 2 queries no total, usando window functions pra fazer
# o agrupamento e o ranking de sinais dentro do próprio Postgres.

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


def aggregate_signals(db: Session, aluno_ids: List[int], sensitive: Optional[set[str]] = None) -> List[Dict[str, Any]]:
    """
    Ranking geral de sinais (não agrupado por persona) usado no 'top_risk_drivers' da
    resposta de /students/personas/high-risk. É 1 query única sobre todo o conjunto de
    alunos de alto risco -- nunca foi parte do N+1 (esse era o loop por grupo em
    build_persona_inputs), então continua igual à versão original.
    """
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
# --- fim das funções antigas ---


def fetch_high_risk_and_population(
    db: Session,
    threshold: float,
    top_n: int,
) -> Tuple[List[int], Dict[str, Any]]:
    """
    Substitui fetch_high_risk_ids() + population_stats() (2 round-trips) por 1 único
    round-trip: COUNT(*)/COUNT(*) FILTER pra estatística populacional e um array_agg
    dos top N ids, tudo na mesma query.
    """
    row = db.execute(
        text("""
            SELECT
              COUNT(*) AS total_scored,
              COUNT(*) FILTER (WHERE classificacao >= :thr) AS high_risk_count,
              (
                SELECT COALESCE(array_agg(id_aluno_graduacao), '{}')
                FROM (
                    SELECT id_aluno_graduacao
                    FROM output_modelo
                    WHERE classificacao >= :thr
                    ORDER BY classificacao DESC
                    LIMIT :n
                ) top
              ) AS high_risk_ids
            FROM output_modelo
        """),
        {"thr": threshold, "n": top_n},
    ).mappings().first()

    pop = {
        "total_scored": int(row["total_scored"]) if row else 0,
        "high_risk_count": int(row["high_risk_count"]) if row and row["high_risk_count"] is not None else 0,
        "high_risk_threshold": threshold,
    }
    high_risk_ids = [int(x) for x in (row["high_risk_ids"] or [])] if row else []
    return high_risk_ids, pop


def build_persona_inputs(
    db: Session,
    high_risk_ids: List[int],
    pop: Dict[str, Any],
    personas_n: int,
    top_signals_n: int = 10,
    sensitive: Optional[set[str]] = None,
) -> Dict[str, Any]:
    """
    Substitui dominant_signal_groups() + N chamadas de aggregate_signals() (o N+1) por
    uma única query: agrupa os alunos pelo sinal mais forte (ROW_NUMBER por aluno),
    pega os `personas_n` maiores grupos, e já ranqueia os top sinais dentro de cada
    grupo (ROW_NUMBER por grupo) — tudo em uma única viagem ao banco.

    `pop` já deve vir pronto de fetch_high_risk_and_population(), pra não rodar a
    query de estatística populacional de novo aqui.
    """
    sensitive = sensitive or DEFAULT_SENSITIVE_FEATURES

    if not high_risk_ids:
        return {"population": pop, "groups": []}

    rows = db.execute(
        text("""
            WITH ranked_top AS (
                SELECT
                    id_aluno_graduacao,
                    descricao,
                    ROW_NUMBER() OVER (
                        PARTITION BY id_aluno_graduacao
                        ORDER BY ABS(peso) DESC
                    ) AS rn
                FROM peso_features
                WHERE id_aluno_graduacao = ANY(:ids)
                  AND descricao IS NOT NULL
            ),
            student_group AS (
                SELECT id_aluno_graduacao, descricao AS group_label
                FROM ranked_top
                WHERE rn = 1
                  AND NOT (descricao = ANY(:sensitive))
            ),
            group_sizes AS (
                SELECT group_label, COUNT(*) AS group_size
                FROM student_group
                GROUP BY group_label
                ORDER BY group_size DESC
                LIMIT :personas_n
            ),
            group_signals AS (
                SELECT
                    gs.group_label,
                    gs.group_size,
                    pf.descricao,
                    CASE WHEN AVG(pf.peso) > 0 THEN 'aumenta_risco' ELSE 'reduz_risco' END AS direction,
                    COUNT(DISTINCT pf.id_aluno_graduacao)::float / gs.group_size AS share,
                    AVG(ABS(pf.peso)) AS avg_abs_peso,
                    COUNT(*) AS occurrences,
                    ROW_NUMBER() OVER (
                        PARTITION BY gs.group_label
                        ORDER BY AVG(ABS(pf.peso)) DESC,
                                 COUNT(DISTINCT pf.id_aluno_graduacao) DESC
                    ) AS signal_rank
                FROM group_sizes gs
                JOIN student_group sg ON sg.group_label = gs.group_label
                JOIN peso_features pf ON pf.id_aluno_graduacao = sg.id_aluno_graduacao
                WHERE pf.descricao IS NOT NULL
                  AND NOT (pf.descricao = ANY(:sensitive))
                GROUP BY gs.group_label, gs.group_size, pf.descricao
            )
            SELECT group_label, group_size, descricao, direction, share, avg_abs_peso, occurrences
            FROM group_signals
            WHERE signal_rank <= :top_signals_n
            ORDER BY group_size DESC, signal_rank ASC
        """),
        {
            "ids": high_risk_ids,
            "sensitive": list(sensitive),
            "personas_n": personas_n,
            "top_signals_n": top_signals_n,
        },
    ).mappings().all()

    groups_by_label: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []
    for r in rows:
        label = r["group_label"]
        if label not in groups_by_label:
            groups_by_label[label] = {
                "group_label": label,
                "group_size": int(r["group_size"]),
                "top_signals": [],
            }
            order.append(label)
        groups_by_label[label]["top_signals"].append({
            "descricao": r["descricao"],
            "direction": r["direction"],
            "share": float(r["share"]) if r["share"] is not None else 0.0,
            "avg_abs_peso": float(r["avg_abs_peso"]) if r["avg_abs_peso"] is not None else 0.0,
            "occurrences": int(r["occurrences"]),
        })

    persona_inputs = [groups_by_label[label] for label in order]
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
    # 700 tokens fixos estourava com personas_n >= 2: cada persona repete até 4
    # common_signals (as descrições inteiras, às vezes 150+ caracteres cada) + summary +
    # who_to_interview + confidence_note, então o custo cresce com personas_n. Escala
    # linear com uma margem generosa, com teto de 4000 pra não sair do controle.
    max_tokens = min(4000, 350 + 380 * personas_n)
    body = {
        "model": model,
        "temperature": 0.1,
        "top_p": 1,
        "max_completion_tokens": max_tokens,
        "response_format": {"type": "json_object"},
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
        choice = data.get("choices", [{}])[0]
        finish_reason = choice.get("finish_reason")
        content = choice.get("message", {}).get("content", "").strip()

        if not content:
            return None, {"type": "empty_response", "message": "Groq retornou resposta vazia", "raw": str(data)[:2000]}

        json_str = _extract_json_object(content)
        if not json_str:
            return None, {"type": "invalid_json", "message": "Não foi possível extrair JSON", "raw": content[:2000]}

        try:
            obj = json.loads(json_str)
        except Exception as e:
            if finish_reason == "length":
                # A causa mais provável de JSON quebrado com finish_reason=length é o
                # max_completion_tokens estourado no meio da resposta -- deixa isso
                # explícito em vez de aparecer só como "invalid_json" genérico.
                return None, {
                    "type": "truncated_response",
                    "message": f"Resposta da Groq cortada por limite de tokens (max_completion_tokens={max_tokens}): {e}",
                    "raw": content[:2000],
                }
            return None, {"type": "invalid_json", "message": str(e), "raw": content[:2000]}

        personas = obj.get("personas")
        if not isinstance(personas, list):
            return None, {"type": "invalid_format", "message": "JSON não contém lista 'personas'", "raw": json_str[:2000]}

        return personas, None

    except httpx.TimeoutException:
        return None, {"type": "timeout", "message": "Timeout chamando Groq"}
    except Exception as e:
        return None, {"type": "exception", "message": str(e)}


def _build_and_generate_personas(
    db: Session,
    threshold: float,
    top_n: int,
    personas_n: int,
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Monta o payload completo que /students/personas/high-risk devolve: population,
    groups, signals (top_risk_drivers), personas e groq_error.

    3 queries no total (antes eram até 2 + personas_n):
      1. fetch_high_risk_and_population -> ids de alto risco + stats populacionais
      2. build_persona_inputs           -> grupos + top sinais por grupo (window functions)
      3. aggregate_signals              -> ranking geral de sinais (top_risk_drivers)
    """
    high_risk_ids, pop = fetch_high_risk_and_population(db, threshold=threshold, top_n=top_n)

    if not high_risk_ids:
        return {
            "population": pop,
            "signals": {"top_risk_drivers": []},
            "groups": [],
            "personas": [],
            "groq_error": None,
        }, None

    payload = build_persona_inputs(db, high_risk_ids, pop=pop, personas_n=personas_n)
    signals = aggregate_signals(db, aluno_ids=high_risk_ids)
    personas, groq_error = generate_personas_with_groq(payload, personas_n=personas_n)

    return {
        "population": payload["population"],
        "signals": {"top_risk_drivers": signals[:10]},
        "groups": payload["groups"],
        "personas": personas or [],
        "groq_error": groq_error,
    }, None


def _cache_ttl_for(data: Dict[str, Any]) -> timedelta:
    """1h quando a Groq gerou personas normalmente; 5min quando veio com groq_error
    (personas=[]), pra não deixar uma falha transitória (ex: truncamento) travada em
    cache por uma hora inteira -- assim a próxima visita já tenta de novo."""
    if data.get("groq_error"):
        return timedelta(minutes=5)
    return CACHE_TTL


def _refresh_cache_sync(db: Session, threshold: float, top_n: int, personas_n: int) -> None:
    try:
        data, error = _build_and_generate_personas(db, threshold, top_n, personas_n)
    except Exception as e:
        data, error = None, {"type": "exception", "message": str(e)}

    with _cache_lock:
        if data is not None:
            _personas_cache["data"] = data
            _personas_cache["expires"] = datetime.now() + _cache_ttl_for(data)
        # se deu erro e já existe dado antigo em cache, mantemos o antigo (fallback)
        # e só empurramos a expiração um pouco pra não martelar a API a cada request
        elif _personas_cache["data"] is not None:
            _personas_cache["expires"] = datetime.now() + timedelta(minutes=5)
        _personas_cache["refreshing"] = False
        _personas_cache["last_error"] = error


def get_personas_cached(
    db: Session,
    threshold: float,
    top_n: int,
    personas_n: int,
    force_refresh: bool = False,
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], bool]:
    """
    Ponto de entrada único para /students/personas/high-risk.

    Retorna (data, error, stale), onde `data` é o payload completo
    ({"population", "signals", "groups", "personas", "groq_error"}):
    - Se o cache está válido (dentro de CACHE_TTL) -> retorna na hora, sem chamar o banco/Groq.
    - Se o cache está vencido mas existe payload antigo -> retorna o payload antigo imediatamente
      (stale=True) e dispara um refresh em background (não bloqueia a request).
    - Se não existe NENHUM dado ainda (primeira chamada da aplicação) -> bloqueia e calcula
      de forma síncrona, pois não há nada pra servir.
    """
    now = datetime.now()

    with _cache_lock:
        has_data = _personas_cache["data"] is not None
        is_fresh = has_data and now < _personas_cache["expires"] and not force_refresh
        already_refreshing = _personas_cache["refreshing"]

        if is_fresh:
            return _personas_cache["data"], None, False

        if has_data:
            # serve o que tem (stale) e dispara refresh em background, se ainda não tiver um rodando
            if not already_refreshing:
                _personas_cache["refreshing"] = True
                Thread(
                    target=_refresh_cache_sync,
                    args=(db, threshold, top_n, personas_n),
                    daemon=True,
                ).start()
            return _personas_cache["data"], None, True

        # sem dado nenhum ainda: precisa bloquear e calcular na hora
        if already_refreshing:
            # outra thread já está calculando o primeiro valor; evita disparo duplicado
            _personas_cache["refreshing"] = True
        else:
            _personas_cache["refreshing"] = True

    personas, error = _build_and_generate_personas(db, threshold, top_n, personas_n)

    with _cache_lock:
        if personas is not None:
            _personas_cache["data"] = personas
            _personas_cache["expires"] = datetime.now() + _cache_ttl_for(personas)
        _personas_cache["refreshing"] = False
        _personas_cache["last_error"] = error

    return personas, error, False