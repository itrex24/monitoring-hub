"""Local demo exporter: synthetic resource metrics and real process uptime."""

import random
import time

from flask import Flask, Response
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Gauge, generate_latest

app = Flask(__name__)
registry = CollectorRegistry()

cpu = Gauge("mock_cpu_percent", "Synthetic CPU usage percent", registry=registry)
disk = Gauge("mock_disk_used_gb", "Synthetic disk used in GB", registry=registry)
uptime = Gauge("mock_uptime_seconds", "Exporter uptime in seconds", registry=registry)
service_health = Gauge(
    "mock_service_health", "Synthetic service health (1=up, 0=down)",
    ["service"], registry=registry,
)
started_at = time.monotonic()
uptime.set_function(lambda: time.monotonic() - started_at)


@app.get("/metrics")
def metrics():
    """Generate fresh demo samples for each scrape."""
    cpu.set(random.uniform(5, 80))
    disk.set(random.uniform(50, 350))
    for service in ("api", "worker", "scheduler"):
        service_health.labels(service=service).set(random.random() > 0.1)
    return Response(generate_latest(registry), content_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    # This server is for the localhost-only demo, not production deployment.
    app.run(host="0.0.0.0", port=8000)
