from __future__ import annotations

from app.models.results import SimulationResult


class ReportGenerator:
    @staticmethod
    def generate_comparison(results: list[SimulationResult]) -> str:
        if not results:
            return "No hay resultados para comparar."

        lines = ["## COMPARACIÓN", "Algoritmo | Promedio TS | Promedio TE", "-" * 48]
        for result in results:
            lines.append(f"{result.algorithm_name} | {result.average_ts:.2f} | {result.average_te:.2f}")

        best_ts = min(results, key=lambda result: result.average_ts)
        best_te = min(results, key=lambda result: result.average_te)
        lines.extend([
            "",
            f"Menor promedio de TS: {best_ts.algorithm_name}",
            f"Menor promedio de TE: {best_te.algorithm_name}",
            "",
            "No se declara un 'mejor' algoritmo en sentido absoluto; los resultados dependen de la métrica evaluada.",
        ])
        return "\n".join(lines)

    @staticmethod
    def generate_report(results: list[SimulationResult]) -> str:
        if not results:
            return "INFORME DE SIMULACIÓN\n\nNo se ejecutaron algoritmos."

        lines = [
            "INFORME DE SIMULACIÓN",
            "====================",
            f"Algoritmos ejecutados: {len(results)}",
            "",
        ]

        for result in results:
            lines.extend([
                f"## {result.algorithm_name}",
                "Proceso | Llegada | Ejecución | Finalización | TS | TE",
                "-" * 72,
            ])
            for process in result.processes:
                metrics = result.process_metrics.get(process.process_id, {})
                completion_time = int(metrics.get("completion_time", process.arrival_time))
                ts = int(metrics.get("ts", completion_time - process.arrival_time))
                te = int(metrics.get("te", max(0, ts - process.burst_time)))
                lines.append(
                    f"{process.process_id} | {process.arrival_time} | {process.burst_time} | {completion_time} | {ts} | {te}"
                )
            lines.extend([
                f"Promedio TS: {result.average_ts:.2f}",
                f"Promedio TE: {result.average_te:.2f}",
                "",
            ])

        lines.append(ReportGenerator.generate_comparison(results))
        return "\n".join(lines)
