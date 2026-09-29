from dataclasses import dataclass, field
from typing import Optional

from app.models.process import Process


@dataclass
class GanttSegment:
    process_id: Optional[str]
    start: int
    end: int

    @property
    def duration(self) -> int:
        return max(0, self.end - self.start)


@dataclass
class SimulationResult:
    algorithm_name: str
    processes: list[Process] = field(default_factory=list)
    schedule: list[GanttSegment] = field(default_factory=list)
    total_time: int = 0
    process_metrics: dict[str, dict[str, float]] = field(default_factory=dict)
    average_turnaround: float = 0.0
    average_waiting: float = 0.0
    average_response: float = 0.0
    average_ts: float = 0.0
    average_te: float = 0.0
    cpu_utilization: float = 0.0
    context_switches: int = 0
