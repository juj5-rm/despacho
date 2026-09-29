from __future__ import annotations

from collections import deque

from app.algorithms.base import BaseSchedulingAlgorithm
from app.models.process import Process
from app.models.results import GanttSegment
from app.services.validation import validate_processes, validate_quantum


class RoundRobinAlgorithm(BaseSchedulingAlgorithm):
    name = "Round Robin"

    def __init__(self, quantum: int | None = None) -> None:
        self.quantum = quantum

    def run(self, processes: list[Process], quantum: int | None = None) -> object:
        quantum_value = quantum if quantum is not None else self.quantum if self.quantum is not None else 1
        validate_quantum(quantum_value)
        validate_processes(processes)

        # RR boundary rule: arrivals that occur exactly at the quantum boundary are queued before
        # the current process is reinserted, so the newly arrived tasks are not starved by the just-finished slice.
        arrival_queue = self._sort_by_arrival(processes)
        ready: deque[Process] = deque()
        remaining = {process.process_id: process.burst_time for process in arrival_queue}
        schedule: list[GanttSegment] = []
        current_time = 0
        next_index = 0
        completed = 0

        while completed < len(arrival_queue):
            while next_index < len(arrival_queue) and arrival_queue[next_index].arrival_time <= current_time:
                ready.append(arrival_queue[next_index])
                next_index += 1

            if not ready:
                if next_index < len(arrival_queue):
                    next_arrival = arrival_queue[next_index].arrival_time
                    if next_arrival > current_time:
                        schedule.append(GanttSegment(None, current_time, next_arrival))
                        current_time = next_arrival
                    continue
                break

            process = ready.popleft()
            slice_length = min(quantum_value, remaining[process.process_id])
            start = current_time
            end = current_time + slice_length
            schedule.append(GanttSegment(process.process_id, start, end))
            current_time = end
            remaining[process.process_id] -= slice_length

            while next_index < len(arrival_queue) and arrival_queue[next_index].arrival_time <= current_time:
                ready.append(arrival_queue[next_index])
                next_index += 1

            if remaining[process.process_id] > 0:
                ready.append(process)
            else:
                completed += 1

        return self._build_result(self.name, arrival_queue, schedule)
