from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Process:
    process_id: str
    arrival_time: int
    burst_time: int
    priority: Optional[int] = None
    order: int = field(default=0, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self.process_id, str) or not self.process_id.strip():
            raise ValueError("Process ID is required.")
        if self.arrival_time < 0:
            raise ValueError(f"Arrival time for {self.process_id} must be >= 0.")
        if self.burst_time <= 0:
            raise ValueError(f"Burst time for {self.process_id} must be > 0.")
        if self.priority is not None and (not isinstance(self.priority, int) or self.priority <= 0):
            raise ValueError(f"Priority for {self.process_id} must be a positive integer when provided.")
