import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from collections import namedtuple
import pytest

from utils.mapear_frases import mapear_frases

Segment = namedtuple('Segment', ['start', 'end', 'text'])


def test_mapear_frases_returns_expected_ranges():
    segments = [
        Segment(0.0, 10.0, 'Segment one text part one'),
        Segment(10.0, 20.0, 'Segment two text part two'),
        Segment(20.0, 30.0, 'Third segment has more text'),
        Segment(30.0, 40.0, 'Final segment concluding text'),
    ]

    phrases = [
        {'text': 'Segment one text part one Segment two text part two'},
        {'text': 'Third segment has more text Final segment concluding text'},
    ]

    results = mapear_frases(phrases, segments)

    expected = [
        (0.0, 20.0),
        (20.0, 40.0),
    ]

    assert len(results) == len(expected)
    for mapping, (start, end) in zip(results, expected):
        assert mapping['start'] >= start
        assert mapping['end'] <= end
