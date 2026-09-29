__all__ = [
    "BaseSchedulingAlgorithm",
    "FCFSAlgorithm",
    "SJFAlgorithm",
    "PriorityAlgorithm",
    "RoundRobinAlgorithm",
    "SRTFAlgorithm",
    "PriorityPreemptiveAlgorithm",
]


def __getattr__(name: str):
    if name == "BaseSchedulingAlgorithm":
        from .base import BaseSchedulingAlgorithm
        return BaseSchedulingAlgorithm
    if name == "FCFSAlgorithm":
        from .fcfs import FCFSAlgorithm
        return FCFSAlgorithm
    if name == "SJFAlgorithm":
        from .sjf import SJFAlgorithm
        return SJFAlgorithm
    if name == "PriorityAlgorithm":
        from .priority import PriorityAlgorithm
        return PriorityAlgorithm
    if name == "RoundRobinAlgorithm":
        from .round_robin import RoundRobinAlgorithm
        return RoundRobinAlgorithm
    if name == "SRTFAlgorithm":
        from .srtf import SRTFAlgorithm
        return SRTFAlgorithm
    if name == "PriorityPreemptiveAlgorithm":
        from .priority_preemptive import PriorityPreemptiveAlgorithm
        return PriorityPreemptiveAlgorithm
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
