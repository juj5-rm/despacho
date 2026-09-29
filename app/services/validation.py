from __future__ import annotations

from app.models.process import Process


def _priority_status(processes: list[Process]) -> tuple[bool, str]:
    if not processes:
        return False, "Priority no disponible: no hay procesos para evaluar."

    priorities = [process.priority for process in processes]
    if not any(priority is not None for priority in priorities):
        return False, "Priority no disponible: todos los procesos deben tener una prioridad definida."
    if any(priority is None for priority in priorities):
        return False, "Priority no disponible: todos los procesos deben tener una prioridad definida."
    if any(not isinstance(priority, int) or priority <= 0 for priority in priorities):
        return False, "Priority no disponible: todas las prioridades deben ser enteros mayores que 0."
    return True, ""


def get_algorithm_availability(processes: list[Process], quantum: int | None) -> dict[str, bool]:
    priority_available, _ = _priority_status(processes)
    quantum_available = isinstance(quantum, int) and not isinstance(quantum, bool) and quantum > 0

    return {
        "FCFS": bool(processes),
        "SJF": bool(processes),
        "Priority": priority_available,
        "Round Robin": quantum_available,
        "SRTF": bool(processes),
        "Priority Preemptive": priority_available,
    }


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
        raise ValueError("Round Robin no disponible: el quantum debe ser mayor que 0.")
    if isinstance(quantum, bool) or not isinstance(quantum, int):
        raise ValueError("Round Robin no disponible: el quantum debe ser mayor que 0.")
    if quantum <= 0:
        raise ValueError("Round Robin no disponible: el quantum debe ser mayor que 0.")


def validate_priority_usage(processes: list[Process]) -> None:
    priority_available, message = _priority_status(processes)
    if not priority_available:
        raise ValueError(message)


def validate_algorithm_inputs(processes: list[Process], quantum: int | None, algorithm_names: list[str]) -> None:
    validate_processes(processes)
    if not algorithm_names:
        raise ValueError("At least one algorithm must be selected.")
    if any(name in {"Round Robin", "RR"} for name in algorithm_names):
        validate_quantum(quantum)
    if any(name in {"Priority", "Priority Preemptive"} for name in algorithm_names):
        validate_priority_usage(processes)
