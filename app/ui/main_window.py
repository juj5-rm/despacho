from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from matplotlib.figure import Figure

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
except ImportError:  # pragma: no cover
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from app.models.process import Process
from app.models.results import GanttSegment, SimulationResult
from app.reports.generator import ReportGenerator
from app.services.simulation_service import SimulationService


class ProcessTableWidget(QTableWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(["ID", "Llegada", "Ráfaga", "Prioridad"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setAlternatingRowColors(True)

    def set_processes(self, processes: list[Process]) -> None:
        self.setRowCount(len(processes))
        for row, process in enumerate(processes):
            self.setItem(row, 0, QTableWidgetItem(process.process_id))
            self.setItem(row, 1, QTableWidgetItem(str(process.arrival_time)))
            self.setItem(row, 2, QTableWidgetItem(str(process.burst_time)))
            priority_text = "" if process.priority is None else str(process.priority)
            self.setItem(row, 3, QTableWidgetItem(priority_text))

    def get_processes(self) -> list[Process]:
        processes: list[Process] = []
        for row in range(self.rowCount()):
            pid_item = self.item(row, 0)
            arrival_item = self.item(row, 1)
            burst_item = self.item(row, 2)
            priority_item = self.item(row, 3)

            if pid_item is None or arrival_item is None or burst_item is None:
                continue

            process_id = pid_item.text().strip()
            arrival = arrival_item.text().strip()
            burst = burst_item.text().strip()
            priority = priority_item.text().strip() if priority_item is not None else ""

            if not process_id:
                raise ValueError("Cada proceso debe tener un ID válido.")

            try:
                arrival_value = int(arrival)
                burst_value = int(burst)
            except ValueError as exc:
                raise ValueError(f"Los tiempos de llegada y ráfaga deben ser enteros válidos para {process_id}.") from exc

            priority_value: Optional[int] = None
            if priority:
                try:
                    priority_value = int(priority)
                except ValueError as exc:
                    raise ValueError(f"La prioridad de {process_id} debe ser un entero válido.") from exc

            processes.append(Process(process_id, arrival_value, burst_value, priority_value, order=len(processes)))
        return processes


class GanttWidget(QWidget):
    def __init__(self, result: SimulationResult) -> None:
        super().__init__()
        self.result = result
        self.figure = Figure(figsize=(max(8, result.total_time * 1.2 + 2), 2.5 + max(2, len(result.processes)) * 0.8))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumWidth(max(720, int(self.figure.get_figwidth() * 100)))
        self.canvas.setMinimumHeight(max(220, int(self.figure.get_figheight() * 110)))
        self.setMinimumHeight(max(260, int(self.figure.get_figheight() * 120)))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self.canvas)
        self.render(result)

    def render(self, result: SimulationResult) -> None:
        self.figure.clear()
        axes = self.figure.add_subplot(111)
        unique_processes = [process.process_id for process in result.processes]
        y_positions = {process_id: index for index, process_id in enumerate(unique_processes)}

        if not unique_processes:
            axes.set_title(result.algorithm_name)
            axes.text(0.5, 0.5, "Sin ejecución", ha="center", va="center")
            axes.set_xticks([])
            axes.set_yticks([])
            self.canvas.draw()
            return

        axes.set_xlim(0, max(1, result.total_time))
        axes.set_ylim(-0.5, len(unique_processes) - 0.5)
        axes.set_yticks(range(len(unique_processes)))
        axes.set_yticklabels(unique_processes)
        axes.set_xlabel("Tiempo")
        axes.set_title(result.algorithm_name)

        color_cycle = ["#4C78A8", "#F58518", "#54A24B", "#E45756", "#B279A2", "#FF9DA6", "#72B7B2", "#BAB0AC"]
        for process in result.processes:
            process_id = process.process_id
            y = y_positions[process_id]
            execution_segments = [segment for segment in result.schedule if segment.process_id == process_id]
            if not execution_segments:
                continue

            start_time = process.arrival_time
            end_time = max(segment.end for segment in execution_segments)
            axes.add_patch(self._outer_border(start_time, end_time, y))

            waiting_ranges: list[tuple[int, int]] = []
            current_time = start_time
            for segment in sorted(execution_segments, key=lambda item: item.start):
                if segment.start > current_time:
                    waiting_ranges.append((current_time, segment.start))
                current_time = max(current_time, segment.end)
            if end_time > current_time:
                waiting_ranges.append((current_time, end_time))

            for wait_start, wait_end in waiting_ranges:
                width = max(0, wait_end - wait_start)
                if width > 0:
                    axes.barh(y, width, left=wait_start, height=0.35, color="none", edgecolor="black", linewidth=1.5, hatch="//")

            for segment in execution_segments:
                axes.barh(y, segment.duration, left=segment.start, height=0.6, color=color_cycle[y % len(color_cycle)], edgecolor="black", linewidth=1.1)

        axes.grid(axis="x", linestyle="--", alpha=0.25)
        self.canvas.draw()

    @staticmethod
    def _outer_border(start: int, end: int, row: int):
        from matplotlib.patches import Rectangle

        return Rectangle(
            (start, row - 0.55),
            max(0, end - start),
            1.1,
            fill=False,
            edgecolor="black",
            linewidth=2.5,
            linestyle="-",
        )


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Simulador de Planificación de Procesos")
        self.resize(1200, 800)
        self.processes = self._default_processes()
        self.algorithm_checks = {
            "FCFS": QCheckBox("FCFS"),
            "SJF": QCheckBox("SJF"),
            "Priority": QCheckBox("Priority"),
            "Round Robin": QCheckBox("Round Robin"),
            "SRTF": QCheckBox("SRTF"),
            "Priority Preemptive": QCheckBox("Priority Preemptive"),
        }
        self.quantum_input = QSpinBox()
        self.quantum_input.setRange(0, 1000)
        self.quantum_input.setValue(0)
        self.process_table = ProcessTableWidget()
        self.results_table = QTableWidget()
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.gantt_container = QWidget()
        self.gantt_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.gantt_layout = QVBoxLayout(self.gantt_container)
        self.gantt_layout.setContentsMargins(4, 4, 4, 4)
        self.gantt_layout.setSpacing(8)
        self.gantt_scroll = QScrollArea()
        self.gantt_scroll.setWidgetResizable(True)
        self.gantt_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.gantt_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.gantt_scroll.setWidget(self.gantt_container)
        self.gantt_container.setMinimumHeight(350)
        self.tabs = QTabWidget()

        self._build_ui()
        self._load_processes()
        self.process_table.itemChanged.connect(self._refresh_algorithm_availability)
        self.quantum_input.valueChanged.connect(self._refresh_algorithm_availability)
        self.algorithm_checks["FCFS"].setChecked(True)
        self.algorithm_checks["SJF"].setChecked(True)
        self._refresh_algorithm_availability()

    def _default_processes(self) -> list[Process]:
        return [Process("P1", 0, 5), Process("P2", 1, 3)]

    def _build_ui(self) -> None:
        central = QWidget()
        root_layout = QVBoxLayout(central)

        input_panel = QWidget()
        input_layout = QVBoxLayout(input_panel)

        controls_layout = QHBoxLayout()
        add_button = QPushButton("Agregar proceso")
        add_many_button = QPushButton("Agregar varios")
        remove_button = QPushButton("Eliminar proceso")
        clear_button = QPushButton("Limpiar")
        execute_button = QPushButton("Ejecutar")

        add_button.clicked.connect(self._add_process)
        add_many_button.clicked.connect(self._add_multiple_processes)
        remove_button.clicked.connect(self._remove_selected_process)
        clear_button.clicked.connect(self._clear_processes)
        execute_button.clicked.connect(self._execute)

        controls_layout.addWidget(add_button)
        controls_layout.addWidget(add_many_button)
        controls_layout.addWidget(remove_button)
        controls_layout.addWidget(clear_button)
        controls_layout.addWidget(execute_button)
        input_layout.addLayout(controls_layout)

        quantum_form = QFormLayout()
        quantum_form.addRow("Quantum", self.quantum_input)
        input_layout.addLayout(quantum_form)

        algorithm_layout = QHBoxLayout()
        for checkbox in self.algorithm_checks.values():
            algorithm_layout.addWidget(checkbox)
        input_layout.addLayout(algorithm_layout)

        select_all_button = QPushButton("Seleccionar todos")
        select_all_button.clicked.connect(self._select_all_algorithms)
        input_layout.addWidget(select_all_button)

        input_layout.addWidget(self.process_table)

        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels(["Algoritmo", "Proceso", "Llegada", "Ejecución", "Finalización", "TS", "TE"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.tabs.addTab(self.results_table, "Resultados")
        self.tabs.addTab(self.results_text, "Informe")
        self.tabs.addTab(self.gantt_scroll, "Gantt")

        split = QSplitter()
        split.addWidget(input_panel)
        split.addWidget(self.tabs)
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 2)
        root_layout.addWidget(split)
        self.setCentralWidget(central)

    def _load_processes(self) -> None:
        self.process_table.set_processes(self.processes)
        self._refresh_algorithm_availability()

    def _add_process(self) -> None:
        next_id = self._next_process_id()
        self.processes.append(Process(next_id, 0, 1))
        self._load_processes()

    def _next_process_id(self) -> str:
        existing = {process.process_id for process in self.processes}
        index = 1
        while True:
            candidate = f"P{index}"
            if candidate not in existing:
                return candidate
            index += 1

    def _add_multiple_processes(self) -> None:
        count, ok = QInputDialog.getInt(self, "Agregar varios procesos", "Cantidad:", 1, 1, 1000, 1)
        if not ok:
            return
        for _ in range(count):
            self.processes.append(Process(self._next_process_id(), 0, 1))
        self._load_processes()

    def _remove_selected_process(self) -> None:
        selected_rows = sorted({index.row() for index in self.process_table.selectedIndexes()})
        if not selected_rows:
            QMessageBox.warning(self, "Sin selección", "Seleccione un proceso para eliminar.")
            return
        for row in reversed(selected_rows):
            self.processes.pop(row)
        self._load_processes()

    def _clear_processes(self) -> None:
        self.processes = []
        self.quantum_input.setValue(0)
        self._clear_results()
        self._load_processes()
        self._refresh_algorithm_availability()

    def _clear_results(self) -> None:
        self.results_text.clear()
        self.results_table.setRowCount(0)
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels(["Algoritmo", "Proceso", "Llegada", "Ejecución", "Finalización", "TS", "TE"])
        while self.gantt_layout.count():
            child = self.gantt_layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()

    def _select_all_algorithms(self) -> None:
        for name, checkbox in self.algorithm_checks.items():
            if checkbox.isEnabled():
                checkbox.setChecked(True)

    def _refresh_algorithm_availability(self) -> None:
        from app.services.validation import get_algorithm_availability

        try:
            current_processes = self.process_table.get_processes()
        except ValueError:
            current_processes = []

        availability = get_algorithm_availability(current_processes, self.quantum_input.value())
        if not current_processes:
            for checkbox in self.algorithm_checks.values():
                checkbox.setEnabled(False)
                checkbox.setChecked(False)
                checkbox.setToolTip("No hay procesos para ejecutar.")
            return

        messages = {
            "Priority": "Priority no disponible: todos los procesos deben tener una prioridad definida.",
            "Priority Preemptive": "Priority no disponible: todos los procesos deben tener una prioridad definida.",
            "Round Robin": "Round Robin no disponible: el quantum debe ser mayor que 0.",
        }
        for name, checkbox in self.algorithm_checks.items():
            available = availability.get(name, False)
            checkbox.setEnabled(available)
            checkbox.setToolTip(messages.get(name, "") if not available else "")
            if not available:
                checkbox.setChecked(False)

    def _execute(self) -> None:
        try:
            self.processes = self.process_table.get_processes()
            selected_algorithms = [name for name, checkbox in self.algorithm_checks.items() if checkbox.isChecked()]
            if not selected_algorithms:
                QMessageBox.warning(self, "Validación", "Debe seleccionar al menos un algoritmo disponible.")
                return
            quantum = self.quantum_input.value()
            results = SimulationService.run(self.processes, selected_algorithms, quantum)
            self._render_results(results)
        except ValueError as exc:
            QMessageBox.warning(self, "Validación", str(exc))

    def _render_results(self, results: list[SimulationResult]) -> None:
        self.results_text.clear()
        self.results_text.setPlainText(ReportGenerator.generate_report(results))

        while self.gantt_layout.count():
            child = self.gantt_layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()

        for result in results:
            widget = GanttWidget(result)
            widget.setMinimumHeight(max(260, len(result.processes) * 70 + 80))
            widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.gantt_layout.addWidget(widget)

        self.gantt_container.adjustSize()
        self.gantt_scroll.updateGeometry()
        self.results_table.setRowCount(0)
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels(["Algoritmo", "Proceso", "Llegada", "Ejecución", "Finalización", "TS", "TE"])

        for result in results:
            for process in result.processes:
                metrics = result.process_metrics.get(process.process_id, {})
                completion_time = int(metrics.get("completion_time", process.arrival_time))
                ts = int(metrics.get("ts", completion_time - process.arrival_time))
                te = int(metrics.get("te", max(0, ts - process.burst_time)))
                row_index = self.results_table.rowCount()
                self.results_table.insertRow(row_index)
                values = [
                    result.algorithm_name,
                    process.process_id,
                    str(process.arrival_time),
                    str(process.burst_time),
                    str(completion_time),
                    str(ts),
                    str(te),
                ]
                for column_index, value in enumerate(values):
                    self.results_table.setItem(row_index, column_index, QTableWidgetItem(value))

        self.tabs.setTabText(0, "Resultados")
        self.tabs.setTabText(1, "Informe")
        self.tabs.setTabText(2, "Gantt")


def main() -> None:
    import sys

    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
