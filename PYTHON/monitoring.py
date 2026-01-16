# monitoring.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List
from collections import defaultdict
import statistics

@dataclass
class APIMetrics:
    """Metriche aggregate per monitoring"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    response_times: List[float] = field(default_factory=list)
    errors: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def avg_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times)
    
    @property
    def p95_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * 0.95)
        return sorted_times[index]

class MetricsCollector:
    """Collettore metriche per dashboard monitoring"""
    
    def __init__(self):
        self.metrics = APIMetrics()
        self._lock = asyncio.Lock()
    
    async def record_request(
        self,
        success: bool,
        tokens_used: int,
        response_time: float,
        error: Optional[str] = None
    ):
        """Registra metriche singola richiesta"""
        async with self._lock:
            self.metrics.total_requests += 1
            
            if success:
                self.metrics.successful_requests += 1
            else:
                self.metrics.failed_requests += 1
                if error:
                    self.metrics.errors[error] += 1
            
            self.metrics.total_tokens += tokens_used
            self.metrics.response_times.append(response_time)
            
            # Calcolo costo (esempio GPT-4)
            cost_per_1k_tokens = 0.03  # input
            self.metrics.total_cost_usd += (tokens_used / 1000) * cost_per_1k_tokens
    
    def get_summary(self) -> Dict:
        """Ottieni sommario metriche per dashboard"""
        return {
            "total_requests": self.metrics.total_requests,
            "success_rate": f"{self.metrics.success_rate:.2%}",
            "avg_response_time_ms": f"{self.metrics.avg_response_time * 1000:.0f}",
            "p95_response_time_ms": f"{self.metrics.p95_response_time * 1000:.0f}",
            "total_tokens": self.metrics.total_tokens,
            "estimated_cost_usd": f"${self.metrics.total_cost_usd:.2f}",
            "errors": dict(self.metrics.errors)
        }
/* Monitoraggio e Telemetria */
