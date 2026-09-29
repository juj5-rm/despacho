# Simulador de planificación de procesos

Aplicación de escritorio para simular y comparar algoritmos de planificación de procesos en un entorno académico de Sistemas Operativos.

## Requisitos

- Python 3.11+
- PySide6
- matplotlib
- pytest

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecución

```bash
python main.py
```

Para ejecutar en cabeza sin ventana visible (por ejemplo, entornos headless):

```bash
QT_QPA_PLATFORM=offscreen python main.py
```

## Arquitectura

```text
app/
├── algorithms/
│   ├── fcfs.py
│   ├── sjf.py
│   ├── priority.py
│   ├── round_robin.py
│   ├── srtf.py
│   ├── priority_preemptive.py
│   └── base.py
├── models/
│   ├── process.py
│   ├── results.py
│   └── __init__.py
├── simulation/
│   └── engine.py
├── services/
│   ├── validation.py
│   ├── simulation_service.py
│   └── __init__.py
├── reports/
│   ├── generator.py
│   └── __init__.py
├── ui/
│   ├── main_window.py
│   └── __init__.py
├── __init__.py
└──
```

La lógica de algoritmo se separa de la interfaz gráfica. La GUI solo dispara servicios de validación y simulación, y luego presenta resultados.

## Algoritmos disponibles

- FCFS / FIFO
- SJF (no preventivo)
- Priority (no preventivo)
- Round Robin (preventivo)
- SRTF
- Priority Preemptive

## Convención de prioridad

Se utiliza la convenion:

- 1 = mayor prioridad
- valores más altos tienen menor prioridad

Esto se aplica de forma consistente en toda la aplicación.

## Quantum

El quantum es un entero positivo usado solo por Round Robin. Si RR está activo, el quantum debe ser válido. Si no se usa RR, no es obligatorio.

## Métricas

Se utilizan las definiciones académicas estándar:

- AT = Arrival Time / Tiempo de llegada
- BT = Burst Time / Ráfaga
- CT = Completion Time / Tiempo de finalización
- TAT = CT - AT
- WT = TAT - BT
- RT = First Start Time - AT

Se calculan además:

- promedio de TAT
- promedio de WT
- promedio de RT
- utilización de CPU
- tiempo total de ejecución
- cambios de contexto

## Flujo de uso

1. La app inicia con dos procesos.
2. El usuario puede editar, agregar, eliminar o limpiar procesos.
3. Se configura el quantum cuando se usa Round Robin.
4. Se seleccionan uno o varios algoritmos.
5. Se ejecuta la simulación.
6. Se muestran resultados, Gantt, comparación e informe textual.

## Pruebas

```bash
pytest
```

## Archivos importantes

- `main.py`: punto de entrada de la aplicación.
- `app/services/simulation_service.py`: servicio que dispara algoritmos y validaciones.
- `app/simulation/engine.py`: motor común para cálculo de métricas y distribución de resultados.
- `tests/test_scheduler.py`: pruebas del núcleo de simulación.
