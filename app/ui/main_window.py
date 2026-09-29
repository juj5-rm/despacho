from __future__ import annotations

from typing import Optional

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
    QSpinBox,
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
        self.figure = Figure(figsize=(9, 3))
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)
        self.render(result)

    def render(self, result: SimulationResult) -> None:
        self.figure.clear()
        axes = self.figure.add_subplot(111)
        y_positions: dict[str, int] = {}
        unique_processes = []
        for segment in result.schedule:
            process_id = segment.process_id
            if process_id is not None and process_id not in y_positions:
                y_positions[process_id] = len(unique_processes)
                unique_processes.append(process_id)

        if not unique_processes:
            axes.set_title(result.algorithm_name)
            axes.text(0.5, 0.5, "Sin ejecución", ha="center", va="center")
            axes.set_xticks([])
            axes.set_yticks([])
            self.canvas.draw()
            return

        axis_labels = []
        for process_id in unique_processes:
            axis_labels.append(process_id)

        for index, segment in enumerate(result.schedule):
            if segment.process_id is None:
                axes.barh(0, segment.duration, left=segment.start, height=0.6, color="lightgray", edgecolor="black")
                continue
            y = y_positions[segment.process_id]
            color = ["#4C78A8", "#F58518", "#54A24B", "#E45756", "#B279A2", "#FF9DA6", "#72B7B2", "#BAB0AC"][index % 8]
            axes.barh(y, segment.duration, left=segment.start, height=0.6, color=color, edgecolor="black")

        axes.set_yticks(range(len(unique_processes)))
        axes.set_yticklabels(unique_processes)
        axes.set_xlabel("Tiempo")
        axes.set_title(result.algorithm_name)
        axes.set_xlim(0, max(1, result.total_time))
        self.canvas.draw()


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
        self.algorithm_checks["FCFS"].setChecked(True)
        self.algorithm_checks["SJF"].setChecked(True)
        self.algorithm_checks["Priority"].setChecked(True)
        self.algorithm_checks["Round Robin"].setChecked(True)
        self.quantum_input = QSpinBox()
        self.quantum_input.setMinimum(1)
        self.quantum_input.setMaximum(1000)
        self.quantum_input.setValue(2)
        self.process_table = ProcessTableWidget()
        self.results_table = QTableWidget()
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.gantt_container = QWidget()
        self.gantt_layout = QVBoxLayout(self.gantt_container)
        self.tabs = QTabWidget()

        self._build_ui()
        self._load_processes()

    def _default_processes(self) -> list[Process]:
        return [Process("P1", 0, 5), Process("P2", 1, 3)]

    def _build_ui(self) -> None:
        central = QWidget()
        root_layout = QVBoxLayout(central)

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
        root_layout.addLayout(controls_layout)

        quantum_form = QFormLayout()
        quantum_form.addRow("Quantum", self.quantum_input)
        root_layout.addLayout(quantum_form)

        algorithm_layout = QHBoxLayout()
        for checkbox in self.algorithm_checks.values():
            algorithm_layout.addWidget(checkbox)
        root_layout.addLayout(algorithm_layout)

        select_all_button = QPushButton("Seleccionar todos")
        select_all_button.clicked.connect(self._select_all_algorithms)
        root_layout.addWidget(select_all_button)

        root_layout.addWidget(self.process_table)

        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels(["Proceso", "AT", "BT", "Prioridad", "CT", "TAT", "WT", "RT"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.tabs.addTab(self.results_table, "Resultados")
        self.tabs.addTab(self.results_text, "Informe")
        self.tabs.addTab(self.gantt_container, "Gantt")

        root_layout.addWidget(self.tabs)
        self.setCentralWidget(central)

    def _load_processes(self) -> None:
        self.process_table.set_processes(self.processes)

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
        self._load_processes()

    def _select_all_algorithms(self) -> None:
        for checkbox in self.algorithm_checks.values():
            checkbox.setChecked(True)

    def _execute(self) -> None:
        try:
            self.processes = self.process_table.get_processes()
            selected_algorithms = [name for name, checkbox in self.algorithm_checks.items() if checkbox.isChecked()]
            quantum = self.quantum_input.value()
            results = SimulationService.run(self.processes, selected_algorithms, quantum)
            self._render_results(results)
        except ValueError as exc:
            QMessageBox.warning(self, "Validación", str(exc))

    def _render_results(self, results: list[SimulationResult]) -> None:
        self.results_text.clear()
        self.results_text.setPlainText(ReportGenerator.generate_report(results))

        self.gantt_layout.takeAt(0)
        while self.gantt_layout.count():
            child = self.gantt_layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()

        for result in results:
            widget = GanttWidget(result)
            self.gantt_layout.addWidget(widget)

        if not results:
            self.results_table.setRowCount(0)
            return

        self.results_table.setRowCount(0)
        for result in results:
            rows = []
            for process_id, metrics in result.process_metrics.items():
                process = next((p for p in self.processes if p.process_id == process_id), None)
                rows.append({
                    "process": process_id,
                    "arrival": process.arrival_time if process else 0,
                    "burst": process.burst_time if process else 0,
                    "priority": process.priority if process else "",
                    "ct": metrics["completion_time"],
                    "tat": metrics["turnaround_time"],
                    "wt": metrics["waiting_time"],
                    "rt": metrics["response_time"],
                })
            for row_data in rows:
                row_index = self.results_table.rowCount()
                self.results_table.insertRow(row_index)
                values = [
                    row_data["process"],
                    str(row_data["arrival"]),
                    str(row_data["burst"]),
                    str(row_data["priority"]),
                    str(int(row_data["ct"])),
                    str(int(row_data["tat"])),
                    str(int(row_data["wt"])),
                    str(int(row_data["rt"])),
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
