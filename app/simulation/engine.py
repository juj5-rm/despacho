from __future__ import annotations

from typing import Iterable

from app.models.process import Process
from app.models.results import GanttSegment, SimulationResult


class SimulationEngine:
    @staticmethod
    def total_time(schedule: Iterable[GanttSegment]) -> int:
        segments = list(schedule)
        if not segments:
            return 0
        return max(segment.end for segment in segments)

    @staticmethod
    def calculate_metrics(processes: list[Process], schedule: list[GanttSegment]) -> dict[str, dict[str, float]]:
        first_start: dict[str, int] = {}
        last_end: dict[str, int] = {}
        execution_time: dict[str, int] = {process.process_id: 0 for process in processes}

        for segment in schedule:
            if segment.process_id is None:
                continue
            if segment.process_id not in first_start:
                first_start[segment.process_id] = segment.start
            last_end[segment.process_id] = segment.end
            execution_time[segment.process_id] += segment.duration

        metrics: dict[str, dict[str, float]] = {}
        for process in processes:
            completion_time = last_end.get(process.process_id, process.arrival_time)
            ts = completion_time - process.arrival_time
            total_execution = execution_time.get(process.process_id, 0)
            te = max(0, ts - total_execution)
            response = (first_start.get(process.process_id, process.arrival_time) - process.arrival_time)
            metrics[process.process_id] = {
                "completion_time": float(completion_time),
                "turnaround_time": float(ts),
                "waiting_time": float(te),
                "response_time": float(response),
                "ts": float(ts),
                "te": float(te),
                "execution_time": float(total_execution),
            }

        return metrics

    @staticmethod
    def compute_context_switches(schedule: list[GanttSegment]) -> int:
        switches = 0
        previous_process: str | None = None
        for segment in schedule:
            current = segment.process_id
            if current is not None and current != previous_process and previous_process is not None:
                switches += 1
            previous_process = current
        return switches

    @staticmethod
    def build_result(algorithm_name: str, processes: list[Process], schedule: list[GanttSegment]) -> SimulationResult:
        metrics = SimulationEngine.calculate_metrics(processes, schedule)
        total_runtime = SimulationEngine.total_time(schedule)
        average_turnaround = sum(values["turnaround_time"] for values in metrics.values()) / len(metrics) if metrics else 0.0
        average_waiting = sum(values["waiting_time"] for values in metrics.values()) / len(metrics) if metrics else 0.0
        average_response = sum(values["response_time"] for values in metrics.values()) / len(metrics) if metrics else 0.0
        average_ts = sum(values["ts"] for values in metrics.values()) / len(metrics) if metrics else 0.0
        average_te = sum(values["te"] for values in metrics.values()) / len(metrics) if metrics else 0.0
        cpu_time = sum(process.burst_time for process in processes)
        cpu_utilization = (cpu_time / total_runtime * 100) if total_runtime > 0 else 0.0

        return SimulationResult(
            algorithm_name=algorithm_name,
            processes=processes,
            schedule=schedule,
            total_time=total_runtime,
            process_metrics=metrics,
            average_turnaround=average_turnaround,
            average_waiting=average_waiting,
            average_response=average_response,
            average_ts=average_ts,
            average_te=average_te,
            cpu_utilization=cpu_utilization,
            context_switches=SimulationEngine.compute_context_switches(schedule),
        )
