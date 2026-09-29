from __future__ import annotations

from app.algorithms.base import BaseSchedulingAlgorithm
from app.models.process import Process
from app.models.results import GanttSegment
from app.services.validation import validate_processes


class SJFAlgorithm(BaseSchedulingAlgorithm):
    name = "SJF"

    def run(self, processes: list[Process], quantum: int | None = None) -> object:
        validate_processes(processes)
        arrival_queue = self._sort_by_arrival(processes)
        order_lookup = self._order_lookup(arrival_queue)
        waiting: list[Process] = []
        schedule: list[GanttSegment] = []
        current_time = 0
        next_index = 0

        while next_index < len(arrival_queue) or waiting:
            while next_index < len(arrival_queue) and arrival_queue[next_index].arrival_time <= current_time:
                waiting.append(arrival_queue[next_index])
                next_index += 1

            if not waiting:
                if next_index < len(arrival_queue):
                    next_arrival = arrival_queue[next_index].arrival_time
                    if current_time < next_arrival:
                        schedule.append(GanttSegment(None, current_time, next_arrival))
                        current_time = next_arrival
                    continue
                break

            selected = min(
                waiting,
                key=lambda process: (process.burst_time, process.arrival_time, order_lookup.get(process.process_id, 0), process.process_id),
            )
            waiting.remove(selected)

            start = current_time
            end = current_time + selected.burst_time
            schedule.append(GanttSegment(selected.process_id, start, end))
            current_time = end

        return self._build_result(self.name, arrival_queue, schedule)
