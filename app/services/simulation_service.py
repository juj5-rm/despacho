from __future__ import annotations

from app.algorithms.fcfs import FCFSAlgorithm
from app.algorithms.priority import PriorityAlgorithm
from app.algorithms.priority_preemptive import PriorityPreemptiveAlgorithm
from app.algorithms.round_robin import RoundRobinAlgorithm
from app.algorithms.sjf import SJFAlgorithm
from app.algorithms.srtf import SRTFAlgorithm
from app.models.process import Process
from app.models.results import SimulationResult
from app.services.validation import validate_algorithm_inputs


class SimulationService:
    _algorithms = {
        "FCFS": FCFSAlgorithm,
        "SJF": SJFAlgorithm,
        "Priority": PriorityAlgorithm,
        "Round Robin": RoundRobinAlgorithm,
        "RR": RoundRobinAlgorithm,
        "SRTF": SRTFAlgorithm,
        "Priority Preemptive": PriorityPreemptiveAlgorithm,
    }

    @classmethod
    def run(cls, processes: list[Process], algorithm_names: list[str], quantum: int | None = None) -> list[SimulationResult]:
        validate_algorithm_inputs(processes, quantum, algorithm_names)
        results: list[SimulationResult] = []
        for algorithm_name in algorithm_names:
            algorithm_cls = cls._algorithms.get(algorithm_name)
            if algorithm_cls is None:
                raise ValueError(f"Unsupported algorithm: {algorithm_name}")
            if algorithm_name in {"Round Robin", "RR"}:
                result = algorithm_cls().run(processes, quantum=quantum)
            elif algorithm_name == "Priority":
                result = algorithm_cls().run(processes)
            elif algorithm_name == "Priority Preemptive":
                result = algorithm_cls().run(processes)
            else:
                result = algorithm_cls().run(processes)
            results.append(result)
        return results
