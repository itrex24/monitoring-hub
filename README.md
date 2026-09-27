# Monitoring Hub

A local learning stack demonstrating Python → Prometheus → Grafana. CPU, disk,
and service health are synthetic; uptime measures the exporter process.
This is a local demo, not a production monitoring deployment.

## Run

Install Docker Desktop with Linux containers and Docker Compose. Windows
PowerShell and a WSL terminal both work; enable Docker Desktop integration for
Ubuntu if using WSL. Local Python and the old virtual environment are not needed.

From the repository root:

```sh
docker compose up --build -d
docker compose ps
```

- [Grafana dashboard](http://localhost:3000/d/mock-exp/mock-exporter-overview)
- [Prometheus targets](http://localhost:9090/targets)
- [Exporter metrics](http://localhost:8000/metrics)

Ports bind only to localhost. Grafana allows anonymous viewing, not editing.
Dashboard and datasource configuration live in Git. Grafana's initial local admin
login is `admin` / `admin`; change its password when first signing in. Do not expose
this configuration to a shared network without configuring authentication.

```sh
docker compose logs --tail=100
docker compose stop        # Stop containers; retain state
docker compose up -d       # Start again
docker compose down        # Remove containers; retain named data volumes
```

Prometheus history and Grafana state use named Docker volumes. `docker compose
down -v` permanently deletes those volumes; use it only to intentionally reset the
demo. Provisioned dashboards are reloaded from Git on startup.

## Data flow

Prometheus pulls `/metrics` from `mock-exporter:8000` every five seconds and also
scrapes itself. Grafana queries `http://prometheus:9090` and refreshes every five
seconds. Python does not push metrics to either service.

| Metric | Meaning |
| --- | --- |
| `mock_cpu_percent` | Random 5–80 percent per request |
| `mock_disk_used_gb` | Random 50–350 decimal GB per request |
| `mock_service_health{service="api\|worker\|scheduler"}` | Separate series per service, approximately 90% UP |
| `mock_uptime_seconds` | Monotonic elapsed process time; resets on restart |

Service labels are `api`, `worker`, and `scheduler` (the table abbreviates them).
Synthetic service health is unrelated to Prometheus's real `up` scrape status.
Opening `/metrics` manually also generates fresh random samples. The exporter
uses Flask's development server and is intentionally limited to this local demo.

## Validate

With Python 3.12 and the runtime requirements installed:

```sh
python -m unittest discover -s tests -v
python scripts/smoke_test.py
```

The smoke check requires the stack to be running and waits up to 90 seconds for
startup. It verifies targets, anonymous read-only dashboard access, and data from
every panel query through Grafana. It does not test browser rendering.

```sh
docker compose config --quiet
docker compose exec -T prometheus promtool check config /etc/prometheus/prometheus.yml
```

GitHub Actions runs these checks on pushes and pull requests.

## Development

For optional local Python development, create a new environment with
`python -m venv .venv`, activate it using your shell's activation script, and run
`python -m pip install -r python-scripts/requirements.txt`. Windows and Linux
virtual environments are not interchangeable. Environments, bytecode, and local
`.env` files are ignored by Git and excluded from the Docker build.

Edit the exporter, then run `docker compose up --build -d`. Edit dashboard JSON
in `grafana/dashboards`; Grafana periodically reloads it. Restart the relevant
service after changing provisioning or Prometheus configuration.

Runtime images are pinned by digest and Python dependencies by version. Update
these deliberately, rebuild, and run the checks before committing. Text files
use LF line endings via `.gitattributes` and `.editorconfig`.

Removing the formerly tracked `python-scripts/.venv` affects future commits only;
old Git commits still contain it. No history rewrite is required for normal cleanup.

## Scope

There are no real host collectors, alert rules, or external integrations yet.
Add a real collector only after deciding what this project should monitor.

## License

[MIT](LICENSE)
