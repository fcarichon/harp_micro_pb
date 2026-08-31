import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from compute_metrics import compute_metrics  # noqa: E402
from run_pilot import aggregate_votes, parse_vote_response  # noqa: E402


class VoteParsingTests(unittest.TestCase):
    def test_valid_vote(self):
        parsed = parse_vote_response(
            '{"selected_projects": ["P2", "P4"], "justification": "test"}',
            ["P2", "P4", "P6"],
        )
        self.assertTrue(parsed["valid"])
        self.assertEqual(parsed["selected_projects"], ["P2", "P4"])

    def test_duplicate_project_is_invalid(self):
        parsed = parse_vote_response(
            '{"selected_projects": ["P2", "P2"], "justification": "test"}',
            ["P2", "P4"],
        )
        self.assertFalse(parsed["valid"])

    def test_out_of_catalog_project_is_invalid(self):
        parsed = parse_vote_response(
            '{"selected_projects": ["P2", "P9"], "justification": "test"}',
            ["P2", "P4"],
        )
        self.assertFalse(parsed["valid"])


class AggregationTests(unittest.TestCase):
    def test_agreement(self):
        result = aggregate_votes([["P2", "P4"], ["P4", "P2"], ["P2", "P4"]])
        self.assertEqual(result["match"], "agreement")
        self.assertEqual(result["final_vote"], ["P2", "P4"])

    def test_partial_agreement(self):
        result = aggregate_votes([["P2", "P4"], ["P4", "P2"], ["P6", "P8"]])
        self.assertEqual(result["match"], "partial_agreement")
        self.assertEqual(result["final_vote"], ["P2", "P4"])

    def test_three_way_tie_uses_alphabetical_tiebreak(self):
        result = aggregate_votes([["P6", "P4"], ["P4", "P8"], ["P6", "P8"]])
        self.assertEqual(result["match"], "non_agreement")
        self.assertEqual(result["final_vote"], ["P4", "P6"])

    def test_insufficient_majority_is_infeasible(self):
        result = aggregate_votes([["P1", "P2"], ["P1", "P3"], ["P4", "P5"]])
        self.assertEqual(result["match"], "non_agreement")
        self.assertEqual(result["final_vote"], "infeasible_vote")


class MetricsTests(unittest.TestCase):
    def test_repeated_profiles_are_not_collapsed(self):
        projects = [
            {"id": "P1", "cost": 50, "utility": {"Eco": 5}},
            {"id": "P2", "cost": 50, "utility": {"Eco": 4}},
        ]
        metrics = compute_metrics(["P1", "P2"], projects, ["Eco", "Eco", "Eco"], 100)
        self.assertEqual(
            metrics["agent_utilities"],
            {"A1:Eco": 9.0, "A2:Eco": 9.0, "A3:Eco": 9.0},
        )
        self.assertEqual(metrics["welfare"], 9.0)


if __name__ == "__main__":
    unittest.main()
