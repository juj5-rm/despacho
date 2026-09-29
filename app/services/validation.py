from __future__ import annotations

from app.models.process import Process


def validate_processes(processes: list[Process]) -> None:
    if not processes:
        raise ValueError("Debe existir al menos un proceso.")

    seen_ids: set[str] = set()
    for process in processes:
        if process.process_id in seen_ids:
            raise ValueError(f"Duplicate process ID found: {process.process_id}")
        seen_ids.add(process.process_id)
        if process.arrival_time < 0:
            raise ValueError(f"Arrival time for {process.process_id} must be >= 0.")
        if process.burst_time <= 0:
            raise ValueError(f"Burst time for {process.process_id} must be > 0.")


def validate_quantum(quantum: int | None) -> None:
    if quantum is None:
        raise ValueError("A valid quantum is required for Round Robin.")
    if isinstance(quantum, bool) or not isinstance(quantum, int):
        raise ValueError("Quantum must be an integer.")
    if quantum <= 0:
        raise ValueError("Quantum must be a positive integer.")


def validate_priority_usage(processes: list[Process]) -> None:
    priorities = [process.priority for process in processes]
    has_priority = any(priority is not None for priority in priorities)
    if has_priority:
        missing = [process.process_id for process in processes if process.priority is None]
        if missing:
            raise ValueError("Priority-based algorithms require all processes to have a valid priority value.")
        for process in processes:
            if process.priority is None or not isinstance(process.priority, int) or process.priority <= 0:
                raise ValueError(f"Priority for {process.process_id} must be a positive integer.")


def validate_algorithm_inputs(processes: list[Process], quantum: int | None, algorithm_names: list[str]) -> None:
    validate_processes(processes)
    if not algorithm_names:
        raise ValueError("At least one algorithm must be selected.")
    if any(name in {"Round Robin", "RR"} for name in algorithm_names):
        validate_quantum(quantum)
    if any(name in {"Priority", "Priority Preemptive"} for name in algorithm_names):
        validate_priority_usage(processes)
