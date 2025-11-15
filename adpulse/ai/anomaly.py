"""
Lightweight anomaly detection utilities.
"""
from __future__ import annotations

import statistics
from typing import Iterable, List, Sequence


def detect_metric_spike(data: Sequence[float], threshold_std: float = 2.0) -> List[int]:
    if len(data) < 2:
        return []
    mean = statistics.fmean(data)
    std = statistics.pstdev(data)
    if std == 0:
        return []
    return [idx for idx, value in enumerate(data) if value > mean + threshold_std * std]


def detect_metric_drop(data: Sequence[float], threshold_std: float = 2.0) -> List[int]:
    if len(data) < 2:
        return []
    mean = statistics.fmean(data)
    std = statistics.pstdev(data)
    if std == 0:
        return []
    return [idx for idx, value in enumerate(data) if value < mean - threshold_std * std]


def find_recent_anomalies(
    dates: Sequence[str],
    values: Sequence[float],
    threshold_std: float = 2.0,
) -> List[dict]:
    anomalies: List[dict] = []
    spikes = detect_metric_spike(values, threshold_std=threshold_std)
    drops = detect_metric_drop(values, threshold_std=threshold_std)

    for idx in spikes:
        anomalies.append(
            {
                "date": dates[idx],
                "value": values[idx],
                "type": "spike",
            }
        )

    for idx in drops:
        anomalies.append(
            {
                "date": dates[idx],
                "value": values[idx],
                "type": "drop",
            }
        )
    # Deduplicate by date/type
    seen = set()
    deduped: List[dict] = []
    for anomaly in anomalies:
        key = (anomaly["date"], anomaly["type"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(anomaly)
    return deduped
