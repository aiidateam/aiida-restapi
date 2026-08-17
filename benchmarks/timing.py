"""Lightweight timing instrumentation for benchmark breakdowns.

Usage::

    from benchmarks.timing import RequestTimer

    timer = RequestTimer()
    with timer.measure('db_query'):
        result = some_db_call()
    with timer.measure('serialization'):
        formatted = serialize(result)
    print(timer.report())
"""

import time
from collections import OrderedDict


class RequestTimer:
    """Collect named timing measurements for a single request."""

    def __init__(self):
        self._measurements: OrderedDict[str, float] = OrderedDict()
        self._stack: list[tuple[str, float]] = []

    def measure(self, label: str):
        """Context manager that records elapsed time under *label*."""
        start = time.perf_counter()
        self._stack.append((label, start))
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        label, start = self._stack.pop()
        elapsed = time.perf_counter() - start
        self._measurements[label] = elapsed
        return False

    @property
    def total(self) -> float:
        return sum(self._measurements.values())

    @property
    def measurements(self) -> dict[str, float]:
        return dict(self._measurements)

    def report(self) -> str:
        """Return a human-readable breakdown string."""
        lines = []
        total = self.total
        for label, elapsed in self._measurements.items():
            pct = (elapsed / total * 100) if total > 0 else 0
            lines.append(f'  {label:.<30s} {elapsed * 1000:8.3f} ms  ({pct:5.1f}%)')
        lines.append(f'  {"TOTAL":.<30s} {total * 1000:8.3f} ms')
        return '\n'.join(lines)

    def clear(self):
        self._measurements.clear()
        self._stack.clear()
