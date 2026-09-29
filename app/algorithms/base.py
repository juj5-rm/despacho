from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from app.models.process import Process
from app.models.results import GanttSegment, SimulationResult
from app.simulation.engine import SimulationEngine


class BaseSchedulingAlgorithm:
    name = "Base"

    def _order_lookup(self, processes: Iterable[Process]) -> dict[str, int]:
        return {process.process_id: index for index, process in enumerate(processes)}

    def _ensure_order(self, processes: Iterable[Process]) -> list[Process]:
        return list(processes)

    def _sort_by_arrival(self, processes: Iterable[Process]) -> list[Process]:
        ordered = list(processes)
        order_lookup = self._order_lookup(ordered)
        return sorted(ordered, key=lambda process: (process.arrival_time, order_lookup.get(process.process_id, 0), process.process_id))

    def _build_result(self, algorithm_name: str, processes: list[Process], schedule: list[GanttSegment]) -> SimulationResult:
        return SimulationEngine.build_result(algorithm_name, processes, schedule)

    def run(self, processes: list[Process], quantum: int | None = None) -> SimulationResult:
        raise NotImplementedError
