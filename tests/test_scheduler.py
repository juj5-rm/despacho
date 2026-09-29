import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QSizePolicy

from app.models.process import Process
from app.services.validation import (
    get_algorithm_availability,
    validate_algorithm_inputs,
    validate_processes,
    validate_quantum,
    validate_priority_usage,
)
from app.simulation.engine import SimulationEngine
from app.algorithms.fcfs import FCFSAlgorithm
from app.algorithms.sjf import SJFAlgorithm
from app.algorithms.priority import PriorityAlgorithm
from app.algorithms.round_robin import RoundRobinAlgorithm
from app.algorithms.srtf import SRTFAlgorithm
from app.algorithms.priority_preemptive import PriorityPreemptiveAlgorithm
from app.ui.main_window import GanttWidget, MainWindow


def test_gantt_selector_renders_single_visible_gantt():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    app.processEvents()
    processes = [
        Process("P1", 0, 5),
        Process("P2", 1, 3),
        Process("P3", 2, 2),
    ]
    results = [
        FCFSAlgorithm().run(processes),
        SJFAlgorithm().run(processes),
    ]

    window._render_results(results)
    window.tabs.setCurrentIndex(2)
    app.processEvents()

    assert window.gantt_selector.isVisible()
    assert window.gantt_selector.count() == 2
    assert window.gantt_scroll.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAsNeeded
    assert window.gantt_scroll.verticalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAsNeeded
    assert window.gantt_layout.count() == 1

    item = window.gantt_layout.itemAt(0)
    assert item is not None
    widget = item.widget()
    assert isinstance(widget, GanttWidget)
    assert widget.canvas.minimumWidth() == 0
    assert widget.sizePolicy().horizontalPolicy() == QSizePolicy.Policy.Expanding


def test_fcfs_order_normal():
    processes = [
        Process("P1", 0, 5),
        Process("P2", 1, 3),
        Process("P3", 2, 8),
        Process("P4", 4, 2),
    ]

    result = FCFSAlgorithm().run(processes)
    assert [seg.process_id for seg in result.schedule] == ["P1", "P2", "P3", "P4"]
    assert result.total_time == 18


def test_sjf_uses_shortest_available_job():
    processes = [
        Process("P1", 0, 5),
        Process("P2", 1, 3),
        Process("P3", 2, 8),
        Process("P4", 4, 2),
    ]

    result = SJFAlgorithm().run(processes)
    assert [seg.process_id for seg in result.schedule] == ["P1", "P4", "P2", "P3"]


def test_priority_orders_by_higher_priority():
    processes = [
        Process("P1", 0, 5, priority=2),
        Process("P2", 1, 3, priority=1),
        Process("P3", 2, 8, priority=3),
    ]

    result = PriorityAlgorithm().run(processes)
    assert [seg.process_id for seg in result.schedule] == ["P1", "P2", "P3"]


def test_round_robin_quantum_two():
    processes = [
        Process("P1", 0, 5),
        Process("P2", 1, 3),
        Process("P3", 2, 8),
        Process("P4", 4, 2),
    ]

    result = RoundRobinAlgorithm(quantum=2).run(processes)
    assert result.total_time == 18
    execution_order = [seg.process_id for seg in result.schedule]
    assert execution_order[:2] == ["P1", "P2"]
    assert execution_order.count("P1") >= 2
    assert execution_order.count("P2") >= 2
    assert execution_order.count("P3") >= 2
    assert execution_order.count("P4") >= 1


def test_metrics_are_coherent():
    processes = [
        Process("P1", 0, 5),
        Process("P2", 1, 3),
        Process("P3", 2, 8),
        Process("P4", 4, 2),
    ]

    result = FCFSAlgorithm().run(processes)
    metrics = SimulationEngine.calculate_metrics(processes, result.schedule)

    assert set(metrics) == {"P1", "P2", "P3", "P4"}
    assert metrics["P1"]["completion_time"] == 5
    assert metrics["P1"]["turnaround_time"] == 5
    assert metrics["P1"]["waiting_time"] == 0
    assert metrics["P1"]["response_time"] == 0


def test_validation_rejects_missing_priority_when_used():
    processes = [
        Process("P1", 0, 5, priority=1),
        Process("P2", 1, 3),
    ]

    try:
        validate_priority_usage(processes)
        assert False, "Expected validation error"
    except ValueError:
        pass


def test_validate_algorithm_inputs_requires_priority_for_priority_preemptive():
    valid_processes = [
        Process("P1", 0, 5, priority=1),
        Process("P2", 1, 3, priority=2),
    ]
    invalid_processes = [
        Process("P1", 0, 5, priority=None),
        Process("P2", 1, 3, priority=2),
    ]

    validate_algorithm_inputs(valid_processes, quantum=None, algorithm_names=["Priority Preemptive"])

    with pytest.raises(ValueError):
        validate_algorithm_inputs(invalid_processes, quantum=None, algorithm_names=["Priority Preemptive"])


def test_validation_rejects_invalid_quantum():
    try:
        validate_quantum(0)
        assert False, "Expected validation error"
    except ValueError:
        pass


def test_gantt_segments_are_non_overlapping_and_cover_all_time():
    processes = [
        Process("P1", 0, 3),
        Process("P2", 1, 2),
    ]

    result = FCFSAlgorithm().run(processes)
    assert result.schedule[0].start == 0
    assert result.schedule[-1].end == 5
    for i in range(1, len(result.schedule)):
        assert result.schedule[i - 1].end <= result.schedule[i].start


def test_ts_and_te_are_coherent_for_all_processes():
    processes = [
        Process("P1", 0, 5),
        Process("P2", 1, 3),
    ]

    result = FCFSAlgorithm().run(processes)

    for process in processes:
        metrics = result.process_metrics[process.process_id]
        ts = metrics["completion_time"] - process.arrival_time
        te = ts - process.burst_time
        assert metrics["ts"] == ts
        assert metrics["te"] == te
        assert ts == metrics["te"] + process.burst_time


def test_algorithm_availability_requires_valid_priority_and_quantum_data():
    processes_without_priority = [
        Process("P1", 0, 5),
        Process("P2", 1, 3),
    ]
    incomplete_priority_processes = [
        Process("P1", 0, 5, priority=1),
        Process("P2", 1, 3),
    ]

    availability = get_algorithm_availability(processes_without_priority, quantum=0)
    assert availability["FCFS"] is True
    assert availability["SJF"] is True
    assert availability["Priority"] is False
    assert availability["Round Robin"] is False

    availability = get_algorithm_availability(incomplete_priority_processes, quantum=2)
    assert availability["Priority"] is False
    assert availability["Round Robin"] is True


def test_reference_scenario_has_valid_outputs():
    processes = [
        Process("P1", 0, 5),
        Process("P2", 1, 3),
        Process("P3", 2, 8),
        Process("P4", 4, 2),
    ]

    priorities = {
        "P1": 2,
        "P2": 1,
        "P3": 4,
        "P4": 3,
    }

    for p in processes:
        p.priority = priorities[p.process_id]

    fcfs = FCFSAlgorithm().run(processes)
    sjf = SJFAlgorithm().run(processes)
    prio = PriorityAlgorithm().run(processes)
    rr = RoundRobinAlgorithm(quantum=2).run(processes)

    assert fcfs.total_time == 18
    assert sjf.total_time == 18
    assert prio.total_time == 18
    assert rr.total_time == 18
    assert len(fcfs.schedule) > 0
    assert len(sjf.schedule) > 0
    assert len(prio.schedule) > 0
    assert len(rr.schedule) > 0


def test_validate_processes_rejects_duplicate_ids():
    processes = [
        Process("P1", 0, 5),
        Process("P1", 1, 2),
    ]

    try:
        validate_processes(processes)
        assert False, "Expected validation error"
    except ValueError:
        pass


def test_empty_process_list_is_rejected():
    with pytest.raises(ValueError, match="at least one process|Debe existir al menos un proceso"):
        validate_processes([])


def test_process_order_is_not_mutated():
    processes = [
        Process("P1", 0, 5),
        Process("P2", 1, 3),
        Process("P3", 2, 2),
    ]
    original = [process.order for process in processes]

    FCFSAlgorithm().run(processes)

    assert [process.order for process in processes] == original


def test_srtf_reference_schedule_matches_academic_rule():
    processes = [
        Process("P1", 0, 8),
        Process("P2", 2, 3),
    ]

    result = SRTFAlgorithm().run(processes)

    assert [(segment.process_id, segment.start, segment.end) for segment in result.schedule] == [
        ("P1", 0, 2),
        ("P2", 2, 5),
        ("P1", 5, 11),
    ]


def test_priority_preemptive_reference_schedule_matches_academic_rule():
    processes = [
        Process("P1", 0, 10, priority=3),
        Process("P2", 5, 1, priority=1),
    ]

    result = PriorityPreemptiveAlgorithm().run(processes)

    assert [(segment.process_id, segment.start, segment.end) for segment in result.schedule] == [
        ("P1", 0, 5),
        ("P2", 5, 6),
        ("P1", 6, 11),
    ]


def test_round_robin_exact_boundary_rule_for_quantum_two():
    processes = [
        Process("P1", 0, 5),
        Process("P2", 0, 3),
    ]

    result = RoundRobinAlgorithm(quantum=2).run(processes)

    assert [(segment.process_id, segment.start, segment.end) for segment in result.schedule] == [
        ("P1", 0, 2),
        ("P2", 2, 4),
        ("P1", 4, 6),
        ("P2", 6, 7),
        ("P1", 7, 8),
    ]
