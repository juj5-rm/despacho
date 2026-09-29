from __future__ import annotations

from app.algorithms.base import BaseSchedulingAlgorithm
from app.models.process import Process
from app.models.results import GanttSegment
from app.services.validation import validate_priority_usage, validate_processes


class PriorityPreemptiveAlgorithm(BaseSchedulingAlgorithm):
    name = "Priority Preemptive"

    def run(self, processes: list[Process], quantum: int | None = None) -> object:
        validate_priority_usage(processes)
        arrival_queue = self._sort_by_arrival(processes)
        order_lookup = self._order_lookup(arrival_queue)
        remaining = {process.process_id: process.burst_time for process in arrival_queue}
        ready: list[Process] = []
        schedule: list[GanttSegment] = []
        current_time = 0
        completed: set[str] = set()
        next_index = 0
        current_process: Process | None = None
        running_start = 0

        while len(completed) < len(arrival_queue):
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

            selected = min(
                ready,
                key=lambda process: (
                    process.priority if process.priority is not None else 999999,
                    process.arrival_time,
                    order_lookup.get(process.process_id, 0),
                    process.process_id,
                ),
            )

            if current_process is None or current_process.process_id != selected.process_id:
                if current_process is not None:
                    schedule.append(GanttSegment(current_process.process_id, running_start, current_time))
                current_process = selected
                running_start = current_time

            current_time += 1
            remaining[current_process.process_id] -= 1

            if remaining[current_process.process_id] <= 0:
                schedule.append(GanttSegment(current_process.process_id, running_start, current_time))
                ready.remove(current_process)
                completed.add(current_process.process_id)
                current_process = None

            ready = [process for process in ready if process.process_id not in completed]

        if current_process is not None and current_process.process_id not in completed:
            schedule.append(GanttSegment(current_process.process_id, running_start, current_time))

        return self._build_result(self.name, arrival_queue, schedule)
