"""Exporter contract checks using only unittest and runtime dependencies."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python-scripts"))
import mock_metrics as exporter
from prometheus_client.parser import text_string_to_metric_families


class ExporterTests(unittest.TestCase):
    def scrape(self):
        response = exporter.app.test_client().get("/metrics")
        self.assertEqual(response.status_code, 200)
        return {
            (sample.name, tuple(sorted(sample.labels.items()))): sample.value
            for family in text_string_to_metric_families(response.text)
            for sample in family.samples
        }

    def test_metric_contract(self):
        samples = self.scrape()
        self.assertTrue(5 <= samples[("mock_cpu_percent", ())] <= 80)
        self.assertTrue(50 <= samples[("mock_disk_used_gb", ())] <= 350)
        for service in ("api", "worker", "scheduler"):
            self.assertIn(samples[("mock_service_health", (("service", service),))], (0, 1))
        self.assertGreaterEqual(samples[("mock_uptime_seconds", ())], 0)

    def test_uptime_survives_backward_wall_clock(self):
        with patch.object(exporter.time, "time", return_value=-1000):
            for elapsed in (10, 25):
                with patch.object(exporter.time, "monotonic", return_value=exporter.started_at + elapsed):
                    self.assertEqual(self.scrape()[("mock_uptime_seconds", ())], elapsed)


if __name__ == "__main__":
    unittest.main()
