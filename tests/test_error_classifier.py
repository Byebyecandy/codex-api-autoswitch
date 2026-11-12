import unittest
from error_classifier import ErrorKind, classify_error


class ClassifierTests(unittest.TestCase):
    def test_authentication_and_forbidden_failover(self):
        self.assertTrue(classify_error(401).should_failover)
        result = classify_error(403, "permission denied")
        self.assertEqual(result.kind, ErrorKind.AUTH_ACCOUNT)
        self.assertTrue(result.should_failover)

    def test_explicit_quota_but_not_rate_limit(self):
        self.assertTrue(classify_error(400, '{"code":"insufficient_quota"}').should_failover)
        self.assertFalse(classify_error(429, "too many requests").should_failover)

    def test_network_request_and_server_failures_do_not_switch(self):
        errors = (classify_error(None, exception="DNS failure"), classify_error(None, exception="Connection reset"), classify_error(400), classify_error(404, "model not found"), classify_error(500), classify_error(503))
        self.assertTrue(all(not error.should_failover for error in errors))


if __name__ == "__main__":
    unittest.main()
