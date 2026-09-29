from .validation import validate_algorithm_inputs, validate_processes, validate_priority_usage, validate_quantum

__all__ = [
    "SimulationService",
    "validate_algorithm_inputs",
    "validate_processes",
    "validate_priority_usage",
    "validate_quantum",
]


def __getattr__(name: str):
    if name == "SimulationService":
        from .simulation_service import SimulationService
        return SimulationService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
