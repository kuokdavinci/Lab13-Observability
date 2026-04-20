from __future__ import annotations

import os
import time
from dataclasses import dataclass

from . import metrics
from .mock_llm import FakeLLM
from .mock_rag import retrieve
from .pii import hash_user_id, summarize_text, scrub_text
from .tracing import langfuse_context, observe


@dataclass
class AgentResult:
    answer: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    quality_score: float

# Bước con: Retrieval
@observe(name="retrieval")
def instrumented_retrieve(message: str):
    docs = retrieve(message)
    langfuse_context.update_current_observation(metadata={"doc_count": len(docs)})
    return docs

# Bước con: Generation
@observe(as_type="generation", name="llm_generation")
def instrumented_generate(llm: FakeLLM, prompt: str):
    response = llm.generate(prompt)
    langfuse_context.update_current_observation(
        input=scrub_text(prompt),
        output=scrub_text(response.text),
        usage_details={
            "input": response.usage.input_tokens,
            "output": response.usage.output_tokens
        }
    )
    return response

class LabAgent:
    def __init__(self, model: str = "claude-sonnet-4-5") -> None:
        self.model = model
        self.llm = FakeLLM(model=model)
        self._cache: dict[str, AgentResult] = {}

    @observe(name="chat")
    def run(self, user_id: str, feature: str, session_id: str, message: str) -> AgentResult:
        started = time.perf_counter()
        
        # 1. Cập nhật Trace Metadata NGAY LẬP TỨC (Dù là cache hit hay không)
        langfuse_context.update_current_trace(
            user_id=hash_user_id(user_id),
            session_id=session_id,
            metadata={"feature": feature, "env": os.getenv("APP_ENV", "dev")},
            tags=["lab-13-local"]
        )
        
        # 2. Check Cache (Cost Optimization Bonus)
        cache_key = f"{feature}:{message.strip().lower()}"
        if cache_key in self._cache:
            result = self._cache[cache_key]
            latency_ms = int((time.perf_counter() - started) * 1000)
            
            # Record locally
            metrics.record_cache_hit()
            metrics.record_request(
                latency_ms=latency_ms,
                cost_usd=0.0,
                tokens_in=0,
                tokens_out=0,
                quality_score=result.quality_score,
            )
            
            # Record Score to Langfuse for Cache Hit
            langfuse_context.score_current_trace(
                name="quality-score",
                value=result.quality_score,
                comment="Cache Hit Score"
            )
            
            return AgentResult(
                answer=result.answer + " (Cached)",
                latency_ms=latency_ms,
                tokens_in=0,
                tokens_out=0,
                cost_usd=0.0,
                quality_score=result.quality_score,
            )

        # 3. Bước Retrieval (Tự động tạo Span con)
        docs = instrumented_retrieve(message)
        
        # 4. Bước Generation (Tự động tạo Generation con)
        prompt = f"Feature={feature}\nDocs={docs}\nQuestion={message}"
        response = instrumented_generate(self.llm, prompt)

        # 5. Final Calculation
        quality_score = self._heuristic_quality(message, response.text, docs)
        latency_ms = int((time.perf_counter() - started) * 1000)
        cost_usd = self._estimate_cost(response.usage.input_tokens, response.usage.output_tokens)

        result = AgentResult(
            answer=response.text,
            latency_ms=latency_ms,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            cost_usd=cost_usd,
            quality_score=quality_score,
        )

        # Update Cache
        self._cache[cache_key] = result

        # Record metrics locally
        metrics.record_request(
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            quality_score=quality_score,
        )
        
        # Send Score to Langfuse
        langfuse_context.score_current_trace(
            name="quality-score",
            value=quality_score,
            comment="Heuristic quality check (Lab 13)"
        )

        return result

    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        return (prompt_tokens * 0.00001) + (completion_tokens * 0.00003)

    def _heuristic_quality(self, question: str, answer: str, docs: list[str]) -> float:
        if len(answer) < 20:
            return 0.2
        if any(doc[:20] in answer for doc in docs):
            return 0.9
        return 0.5
