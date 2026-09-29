from __future__ import annotations

from app.models.results import SimulationResult


class ReportGenerator:
    @staticmethod
    def generate_comparison(results: list[SimulationResult]) -> str:
        if not results:
            return "No hay resultados para comparar."

        lines = ["COMPARACIÓN", "-----------"]
        for result in results:
            lines.append(
                f"{result.algorithm_name}: TAT promedio = {result.average_turnaround:.2f}, "
                f"WT promedio = {result.average_waiting:.2f}, "
                f"RT promedio = {result.average_response:.2f}, "
                f"Utilización CPU = {result.cpu_utilization:.2f}%"
            )

        best_wait = min(results, key=lambda result: result.average_waiting)
        best_response = min(results, key=lambda result: result.average_response)
        lines.extend([
            "",
            f"{best_wait.algorithm_name} presentó el menor tiempo promedio de espera ({best_wait.average_waiting:.2f}).",
            f"{best_response.algorithm_name} presentó el menor tiempo promedio de respuesta ({best_response.average_response:.2f}).",
            "",
            "En este conjunto de procesos, la diferencia entre algoritmos refleja cómo cada estrategia prioriza la llegada, la duración y la respuesta del sistema.",
        ])
        return "\n".join(lines)

    @staticmethod
    def generate_report(results: list[SimulationResult]) -> str:
        if not results:
            return "INFORME DE SIMULACIÓN\n\nNo se ejecutaron algoritmos."

        lines = [
            "INFORME DE SIMULACIÓN",
            "====================",
            f"Número de algoritmos ejecutados: {len(results)}",
            "",
        ]

        for result in results:
            lines.extend([
                result.algorithm_name,
                "-" * len(result.algorithm_name),
                f"Tiempo total de simulación: {result.total_time}",
                f"Promedio TAT: {result.average_turnaround:.2f}",
                f"Promedio WT: {result.average_waiting:.2f}",
                f"Promedio RT: {result.average_response:.2f}",
                f"Utilización CPU: {result.cpu_utilization:.2f}%",
                f"Cambios de contexto: {result.context_switches}",
                "",
            ])

        lines.append(ReportGenerator.generate_comparison(results))
        return "\n".join(lines)
