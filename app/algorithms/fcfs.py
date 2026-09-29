from __future__ import annotations

from app.algorithms.base import BaseSchedulingAlgorithm
from app.models.process import Process
from app.models.results import GanttSegment
from app.services.validation import validate_processes


class FCFSAlgorithm(BaseSchedulingAlgorithm):
    name = "FCFS"

    def run(self, processes: list[Process], quantum: int | None = None) -> object:
        validate_processes(processes)
        ordered = self._sort_by_arrival(processes)
        schedule: list[GanttSegment] = []
        current_time = 0

        for process in ordered:
            if current_time < process.arrival_time:
                schedule.append(GanttSegment(None, current_time, process.arrival_time))
                current_time = process.arrival_time

            start = current_time
            end = current_time + process.burst_time
            schedule.append(GanttSegment(process.process_id, start, end))
            current_time = end

        return self._build_result(self.name, ordered, schedule)
