"""Tests for verify_load's pure diff logic — no database required."""

from src.ingest.verify_load import diff_counts


def test_clean_when_actual_matches_expected():
    expected = {"a": 10, "b": 20}
    actual = {"a": 10, "b": 20}
    assert diff_counts(expected, actual) == []


def test_reports_row_count_mismatch_with_delta():
    expected = {"a": 10}
    actual = {"a": 7}
    problems = diff_counts(expected, actual)
    assert len(problems) == 1
    line = problems[0]
    assert "a" in line
    assert "expected 10" in line
    assert "got 7" in line
    assert "-3" in line


def test_reports_missing_table():
    expected = {"a": 10, "b": 20}
    actual = {"a": 10}
    problems = diff_counts(expected, actual)
    assert len(problems) == 1
    assert "b" in problems[0]
    assert "MISSING" in problems[0]


def test_reports_unexpected_table():
    expected = {"a": 10}
    actual = {"a": 10, "stowaway": 999}
    problems = diff_counts(expected, actual)
    assert len(problems) == 1
    assert "stowaway" in problems[0]
    assert "UNEXPECTED" in problems[0]


def test_reports_multiple_problems_in_one_run():
    expected = {"a": 10, "b": 20, "c": 30}
    actual = {"a": 11, "c": 30, "d": 5}
    problems = diff_counts(expected, actual)
    assert len(problems) == 3
