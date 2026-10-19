
import unittest

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


class KnowledgeBrainTests(unittest.TestCase):

    def test_users_api_article_ranks_first(self):
        response = client.get(
            "/search",
            params={
                "q": "How can I manage users with API calls?",
                "limit": 5,
            },
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertGreaterEqual(data["total_matches"], 1)
        self.assertEqual(data["result_count"], 5)
        self.assertEqual(len(data["results"]), 5)

        first_result = data["results"][0]

        self.assertIn("12000103947", first_result["url"])
        self.assertGreater(first_result["score"], 0)

        print("\nPASS: Users API article ranks first.")

    def test_result_limit_is_respected(self):
        response = client.get(
            "/search",
            params={
                "q": "users API",
                "limit": 3,
            },
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertLessEqual(data["result_count"], 3)
        self.assertEqual(
            data["result_count"],
            len(data["results"]),
        )
        self.assertGreaterEqual(
            data["total_matches"],
            data["result_count"],
        )

        print("PASS: Result limit and counts are correct.")

    def test_unmatched_query_returns_no_results(self):
        response = client.get(
            "/search",
            params={
                "q": "qzxvnonexistenttoken987654",
                "limit": 5,
            },
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["total_matches"], 0)
        self.assertEqual(data["result_count"], 0)
        self.assertEqual(data["results"], [])

        print("PASS: Unmatched query returns no results.")


if __name__ == "__main__":
    unittest.main(verbosity=2)

