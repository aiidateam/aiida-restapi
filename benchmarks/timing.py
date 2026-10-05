"""Lightweight timing instrumentation for benchmark breakdowns.

Usage::

    from benchmarks.timing import RequestTimer

    timer = RequestTimer()
    with timer.measure('db_query'):
        result = some_db_call()
    with timer.measure('serialization'):
        formatted = serialize(result)
    print(timer.report())

Each ``measure`` block appends one sample. Aggregates (``to_dict`` /
``report``) are normalised per request over ``rounds`` timed requests, so
numbers stay comparable when the round count changes. Labels are kept
separate per wrapped method (e.g. ``db:get_many``) instead of collapsing
everything into a single bucket.
"""

import time
from collections import OrderedDict
from contextlib import contextmanager


class RequestTimer:
    """Collect named timing samples, aggregated per request."""

    def __init__(self):
        self._samples: OrderedDict[str, list[float]] = OrderedDict()

    @contextmanager
    def measure(self, label: str):
        """Context manager that records one elapsed sample under *label*."""
        start = time.perf_counter()
        try:
            yield self
        finally:
            elapsed = time.perf_counter() - start
            self._samples.setdefault(label, []).append(elapsed)

    def _means(self, rounds: int | None = None) -> OrderedDict[str, float]:
        """Mean seconds per request for each label."""
        means: OrderedDict[str, float] = OrderedDict()
        for label, samples in self._samples.items():
            divisor = rounds or len(samples) or 1
            means[label] = sum(samples) / divisor
        return means

    @property
    def total(self) -> float:
        """Mean total seconds per request (sum of per-label means)."""
        return sum(self._means().values())

    @property
    def measurements(self) -> dict[str, float]:
        """Mean seconds per request for each label (backwards-compatible)."""
        return dict(self._means())

    @property
    def sample_counts(self) -> dict[str, int]:
        """Number of recorded samples per label."""
        return {label: len(samples) for label, samples in self._samples.items()}

    def report(self, rounds: int | None = None) -> str:
        """Return a human-readable per-request breakdown string."""
        means = self._means(rounds)
        total = sum(means.values())
        lines = []
        for label, mean in means.items():
            calls = len(self._samples[label])
            pct = (mean / total * 100) if total > 0 else 0
            lines.append(f'  {label:.<30s} {mean * 1000:8.3f} ms/req  ({pct:5.1f}%, {calls} calls)')
        lines.append(f'  {"TOTAL":.<30s} {total * 1000:8.3f} ms/req')
        return '\n'.join(lines)

    def to_dict(self, rounds: int | None = None) -> dict:
        """Return per-request aggregates as a plain dict (serialisable to JSON)."""
        means = self._means(rounds)
        total = sum(means.values())
        return {
            'layers': {
                label: {
                    'mean_ms_per_request': round(mean * 1000, 3),
                    'mean_seconds_per_request': mean,
                    'calls': len(self._samples[label]),
                    'pct': round(mean / total * 100, 1) if total > 0 else 0,
                }
                for label, mean in means.items()
            },
            'total_ms_per_request': round(total * 1000, 3),
            'total_seconds_per_request': total,
        }

    def clear(self):
        self._samples.clear()
