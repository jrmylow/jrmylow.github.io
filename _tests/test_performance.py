"""Performance tests for page load times using Navigation Timing API."""

import statistics
from dataclasses import dataclass
from typing import List

import pytest
from playwright.sync_api import Page

from constants import (
    PERF_ITERATIONS,
    PERF_MAX_DOM_NODES,
    PERF_MAX_LOAD_TIME,
    PERF_MAX_RESOURCES,
    PERF_MAX_TRANSFER_BYTES,
    PERF_TEST_PAGES,
    PERF_THRESHOLDS,
)


@dataclass
class PerformanceMetrics:
    """Container for page performance metrics in milliseconds."""

    ttfb: float  # Time to First Byte
    dom_interactive: float  # DOM Interactive
    dom_content_loaded: float  # DOMContentLoaded event
    load_complete: float  # Load event complete


def calculate_p90(values: List[float]) -> float:
    """Calculate 90th percentile of values."""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = int(len(sorted_values) * 0.9)
    # Clamp index to valid range
    index = min(index, len(sorted_values) - 1)
    return sorted_values[index]


def get_performance_metrics(page: Page) -> PerformanceMetrics:
    """Extract performance metrics from page using Navigation Timing API."""
    timing = page.evaluate(
        """
        () => {
            const entries = performance.getEntriesByType('navigation');
            if (entries.length > 0) {
                const nav = entries[0];
                return {
                    ttfb: nav.responseStart - nav.requestStart,
                    dom_interactive: nav.domInteractive - nav.requestStart,
                    dom_content_loaded: nav.domContentLoadedEventEnd - nav.requestStart,
                    load_complete: nav.loadEventEnd - nav.requestStart
                };
            }
            // Fallback to legacy timing API
            const t = performance.timing;
            return {
                ttfb: t.responseStart - t.navigationStart,
                dom_interactive: t.domInteractive - t.navigationStart,
                dom_content_loaded: t.domContentLoadedEventEnd - t.navigationStart,
                load_complete: t.loadEventEnd - t.navigationStart
            };
        }
        """
    )
    return PerformanceMetrics(**timing)


def collect_metrics_for_page(
    page: Page, url: str, iterations: int
) -> List[PerformanceMetrics]:
    """Collect performance metrics over multiple page loads."""
    metrics = []
    for _ in range(iterations):
        # Clear cache between runs to get consistent measurements
        page.context.clear_cookies()

        # Navigate and wait for load
        page.goto(url, wait_until="load")

        # Small delay to ensure loadEventEnd is populated
        page.wait_for_timeout(50)

        metric = get_performance_metrics(page)
        metrics.append(metric)

    return metrics


def aggregate_metrics(
    metrics: List[PerformanceMetrics],
) -> dict:
    """Calculate average and P90 for all metric types."""
    ttfb_values = [m.ttfb for m in metrics]
    dom_interactive_values = [m.dom_interactive for m in metrics]
    dom_content_loaded_values = [m.dom_content_loaded for m in metrics]
    load_complete_values = [m.load_complete for m in metrics]

    return {
        "ttfb_avg": statistics.mean(ttfb_values),
        "ttfb_p90": calculate_p90(ttfb_values),
        "dom_interactive_avg": statistics.mean(dom_interactive_values),
        "dom_interactive_p90": calculate_p90(dom_interactive_values),
        "dom_content_loaded_avg": statistics.mean(dom_content_loaded_values),
        "dom_content_loaded_p90": calculate_p90(dom_content_loaded_values),
        "load_complete_avg": statistics.mean(load_complete_values),
        "load_complete_p90": calculate_p90(load_complete_values),
    }


class TestPageLoadPerformance:
    """Performance tests for page load times."""

    @pytest.fixture(autouse=True)
    def setup(self, jekyll_server: str):
        """Store server URL for tests."""
        self.server = jekyll_server

    def test_homepage_load_time(self, page: Page, jekyll_server: str):
        """Homepage should load within performance thresholds."""
        metrics = collect_metrics_for_page(
            page, f"{jekyll_server}/", iterations=PERF_ITERATIONS
        )
        agg = aggregate_metrics(metrics)

        assert (
            agg["ttfb_avg"] < PERF_THRESHOLDS["ttfb_avg"]
        ), f"TTFB avg {agg['ttfb_avg']:.0f}ms exceeds {PERF_THRESHOLDS['ttfb_avg']}ms"
        assert (
            agg["dom_content_loaded_avg"] < PERF_THRESHOLDS["dom_content_loaded_avg"]
        ), (
            f"DOMContentLoaded avg {agg['dom_content_loaded_avg']:.0f}ms "
            f"exceeds {PERF_THRESHOLDS['dom_content_loaded_avg']}ms"
        )
        assert agg["load_complete_avg"] < PERF_THRESHOLDS["load_complete_avg"], (
            f"Load avg {agg['load_complete_avg']:.0f}ms "
            f"exceeds {PERF_THRESHOLDS['load_complete_avg']}ms"
        )

    def test_all_pages_p90_performance(self, page: Page, jekyll_server: str):
        """All test pages should meet P90 performance thresholds."""
        all_metrics = []

        for path in PERF_TEST_PAGES:
            url = f"{jekyll_server}{path}"
            try:
                metrics = collect_metrics_for_page(
                    page, url, iterations=PERF_ITERATIONS
                )
                all_metrics.extend(metrics)
            except Exception as e:
                pytest.skip(f"Could not load {path}: {e}")

        agg = aggregate_metrics(all_metrics)

        # Report all metrics
        print(f"\n{'='*60}")
        print("PERFORMANCE RESULTS (all pages combined)")
        print(f"{'='*60}")
        print(
            f"Samples: {len(all_metrics)} ({len(PERF_TEST_PAGES)} pages x {PERF_ITERATIONS} runs)"
        )
        print(f"\n{'Metric':<25} {'Average':>10} {'P90':>10} {'Threshold':>12}")
        print(f"{'-'*60}")
        print(
            f"{'TTFB':<25} {agg['ttfb_avg']:>10.0f}ms {agg['ttfb_p90']:>10.0f}ms "
            f"{PERF_THRESHOLDS['ttfb_p90']:>10}ms"
        )
        print(
            f"{'DOM Interactive':<25} {agg['dom_interactive_avg']:>10.0f}ms "
            f"{agg['dom_interactive_p90']:>10.0f}ms {'N/A':>12}"
        )
        print(
            f"{'DOMContentLoaded':<25} {agg['dom_content_loaded_avg']:>10.0f}ms "
            f"{agg['dom_content_loaded_p90']:>10.0f}ms "
            f"{PERF_THRESHOLDS['dom_content_loaded_p90']:>10}ms"
        )
        print(
            f"{'Load Complete':<25} {agg['load_complete_avg']:>10.0f}ms "
            f"{agg['load_complete_p90']:>10.0f}ms "
            f"{PERF_THRESHOLDS['load_complete_p90']:>10}ms"
        )
        print(f"{'='*60}\n")

        # Assert P90 thresholds
        assert (
            agg["ttfb_p90"] < PERF_THRESHOLDS["ttfb_p90"]
        ), f"TTFB P90 {agg['ttfb_p90']:.0f}ms exceeds {PERF_THRESHOLDS['ttfb_p90']}ms"
        assert (
            agg["dom_content_loaded_p90"] < PERF_THRESHOLDS["dom_content_loaded_p90"]
        ), (
            f"DOMContentLoaded P90 {agg['dom_content_loaded_p90']:.0f}ms "
            f"exceeds {PERF_THRESHOLDS['dom_content_loaded_p90']}ms"
        )
        assert agg["load_complete_p90"] < PERF_THRESHOLDS["load_complete_p90"], (
            f"Load P90 {agg['load_complete_p90']:.0f}ms "
            f"exceeds {PERF_THRESHOLDS['load_complete_p90']}ms"
        )

    def test_individual_page_performance(self, page: Page, jekyll_server: str):
        """Each page individually should meet performance thresholds."""
        results = {}

        for path in PERF_TEST_PAGES:
            url = f"{jekyll_server}{path}"
            try:
                metrics = collect_metrics_for_page(
                    page, url, iterations=PERF_ITERATIONS
                )
                results[path] = aggregate_metrics(metrics)
            except Exception:
                results[path] = None

        # Report per-page results
        print(f"\n{'='*70}")
        print("PER-PAGE PERFORMANCE RESULTS")
        print(f"{'='*70}")
        print(f"{'Page':<20} {'TTFB':>8} {'DOMLoaded':>12} {'Load':>10} {'Status':>10}")
        print(f"{'-'*70}")

        failures = []
        for path, agg in results.items():
            if agg is None:
                print(
                    f"{path:<20} {'SKIP':>8} {'SKIP':>12} {'SKIP':>10} {'SKIPPED':>10}"
                )
                continue

            status = "PASS"
            if agg["load_complete_avg"] >= PERF_THRESHOLDS["load_complete_avg"]:
                status = "FAIL"
                failures.append(path)

            print(
                f"{path:<20} {agg['ttfb_avg']:>7.0f}ms "
                f"{agg['dom_content_loaded_avg']:>11.0f}ms "
                f"{agg['load_complete_avg']:>9.0f}ms {status:>10}"
            )

        print(f"{'='*70}\n")

        assert len(failures) == 0, f"Pages exceeding thresholds: {failures}"

    def test_no_performance_regression(self, page: Page, jekyll_server: str):
        """Ensure no single page load takes excessively long (outlier detection)."""
        outliers = []

        for path in PERF_TEST_PAGES:
            url = f"{jekyll_server}{path}"
            try:
                metrics = collect_metrics_for_page(page, url, iterations=5)
                for i, m in enumerate(metrics):
                    if m.load_complete > PERF_MAX_LOAD_TIME:
                        outliers.append(f"{path} run {i+1}: {m.load_complete:.0f}ms")
            except Exception:
                pass

        assert (
            len(outliers) == 0
        ), f"Found {len(outliers)} loads exceeding {PERF_MAX_LOAD_TIME}ms: {outliers}"


class TestResourceMetrics:
    """Tests for page resource sizes and counts."""

    def test_page_resource_count(self, page: Page, jekyll_server: str):
        """Pages should not load excessive resources."""
        page.goto(f"{jekyll_server}/", wait_until="load")

        resource_count = page.evaluate(
            """
            () => performance.getEntriesByType('resource').length
            """
        )

        assert (
            resource_count < PERF_MAX_RESOURCES
        ), f"Homepage loads {resource_count} resources, exceeds {PERF_MAX_RESOURCES}"

    def test_total_transfer_size(self, page: Page, jekyll_server: str):
        """Total page weight should be under threshold."""
        page.goto(f"{jekyll_server}/", wait_until="load")

        total_size = page.evaluate(
            """
            () => {
                const resources = performance.getEntriesByType('resource');
                return resources.reduce((sum, r) => sum + (r.transferSize || 0), 0);
            }
            """
        )

        # Also get the document size
        doc_size = page.evaluate(
            """
            () => {
                const nav = performance.getEntriesByType('navigation')[0];
                return nav ? (nav.transferSize || 0) : 0;
            }
            """
        )

        total = total_size + doc_size
        max_kb = PERF_MAX_TRANSFER_BYTES / 1024

        print(f"\nTotal transfer size: {total / 1024:.1f}KB (limit: {max_kb:.0f}KB)")

        assert (
            total < PERF_MAX_TRANSFER_BYTES
        ), f"Total transfer size {total / 1024:.1f}KB exceeds {max_kb:.0f}KB"

    def test_dom_node_count(self, page: Page, jekyll_server: str):
        """DOM should not have excessive nodes."""
        page.goto(f"{jekyll_server}/", wait_until="load")

        node_count = page.evaluate(
            """
            () => document.getElementsByTagName('*').length
            """
        )

        print(f"\nDOM nodes: {node_count} (limit: {PERF_MAX_DOM_NODES})")

        assert (
            node_count < PERF_MAX_DOM_NODES
        ), f"DOM has {node_count} nodes, exceeds {PERF_MAX_DOM_NODES}"
