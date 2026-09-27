"""Read-only smoke check of a running Compose stack. No extra dependencies."""
import json
import time
import urllib.request


def get(url):
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.load(response)


def check():
    targets = get("http://localhost:9090/api/v1/targets")["data"]["activeTargets"]
    assert {t["labels"]["job"] for t in targets} == {"prometheus", "mock_exporter"}
    assert all(t["health"] == "up" for t in targets), targets
    base = "http://localhost:3000"
    assert get(base + "/api/health")["database"] == "ok"
    dashboard = get(base + "/api/dashboards/uid/mock-exp")
    assert dashboard["meta"]["provisioned"]
    assert not dashboard["meta"]["canEdit"], "Anonymous user can edit dashboards"
    queries = []
    for panel in dashboard["dashboard"]["panels"]:
        queries.append({
            "refId": str(panel["id"]), "datasource": panel["datasource"],
            "expr": panel["targets"][0]["expr"], "instant": True,
            "range": False, "intervalMs": 5000, "maxDataPoints": 100,
        })
    now = int(time.time() * 1000)
    request = urllib.request.Request(
        base + "/api/ds/query",
        data=json.dumps({"from": str(now - 60000), "to": str(now), "queries": queries}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        results = json.load(response)["results"]
    for query in queries:
        result = results[query["refId"]]
        assert not result.get("error"), result
        assert result.get("frames"), result
        assert all(frame["data"]["values"][-1] for frame in result["frames"]), result


if __name__ == "__main__":
    deadline = time.monotonic() + 90
    while True:
        try:
            check()
            break
        except (AssertionError, KeyError, OSError) as error:
            if time.monotonic() >= deadline:
                raise SystemExit(f"Smoke check failed: {error}") from error
            time.sleep(3)
    print("PASS: targets UP, dashboard provisioned and read-only, all panel queries return data")
