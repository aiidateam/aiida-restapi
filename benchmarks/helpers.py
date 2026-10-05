"""Shared helpers for REST API benchmarks.

Import from here in benchmark tests::

    from benchmarks.helpers import bench_request, first_node_uuid
"""

from aiida import orm


def bench_request(benchmark, client, method, url, **kwargs):
    """Benchmark a single HTTP request, recording size + status reliably.

    A probe request is issued first to capture the expected status code and
    response size; the timed function asserts the same status on every round
    so silent 4xx/5xx regressions fail loudly instead of benchmarking an
    error page. ``extra_info`` is set *after* ``benchmark()`` runs, since
    pytest-benchmark may reset it around the timed section.
    """
    func = getattr(client, method)
    probe = func(url, **kwargs)
    assert probe.status_code < 500, f'{method.upper()} {url} -> {probe.status_code}: {probe.text[:500]}'
    expected_status = probe.status_code
    size = len(probe.content)

    def run():
        resp = func(url, **kwargs)
        assert resp.status_code == expected_status, (
            f'{method.upper()} {url} status changed during benchmark: {resp.status_code} != {expected_status}'
        )
        return resp

    benchmark(run)
    benchmark.extra_info['response_bytes'] = size
    benchmark.extra_info['status_code'] = expected_status


def first_pk(model) -> int | None:
    """Return the PK of any entity of *model*, or None if the profile is empty."""
    row = orm.QueryBuilder().append(model, project=['pk']).first()
    return row[0] if row else None


def first_uuid(model) -> str | None:
    """Return the UUID of any entity of *model*, or None if the profile is empty."""
    row = orm.QueryBuilder().append(model, project=['uuid']).first()
    return row[0] if row else None


def first_node_uuid() -> str | None:
    """Return the UUID of any node, or None if the profile is empty."""
    return first_uuid(orm.Node)


def first_data_node_uuid() -> str | None:
    """Return the UUID of any Data node, or None if there isn't one."""
    return first_uuid(orm.Data)
