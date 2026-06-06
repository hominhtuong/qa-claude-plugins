#!/usr/bin/env python3
"""Unit tests for the Lark auth/read helpers — stdlib `unittest`, no network.

Run from anywhere:
    python3 plugins/qa/scripts/tests/test_lark.py
    (or)  cd plugins/qa/scripts && python3 -m unittest tests.test_lark -v

Covers the regressions the 6-barrier fix targets: env inline-comment parsing,
placeholder-credential detection, read-scope classification, and error → action mapping.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Make the scripts dir importable regardless of the cwd the tests run from.
SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import _env  # noqa: E402
from _env import (is_ssl_cert_error, parse_env_line, strip_inline_comment)  # noqa: E402


class TestEnvParser(unittest.TestCase):
    def test_inline_comment_stripped_with_space(self):
        self.assertEqual(
            parse_env_line("LARK_DOMAIN=https://open.larksuite.com    # Feishu (China)"),
            ("LARK_DOMAIN", "https://open.larksuite.com"))

    def test_inline_comment_stripped_with_tab(self):
        self.assertEqual(parse_env_line("K=value\t# tail"), ("K", "value"))

    def test_hash_inside_value_kept(self):
        # No whitespace before '#' → it's part of the value (secret/password), not a comment.
        self.assertEqual(parse_env_line("PASS=ab#cd"), ("PASS", "ab#cd"))

    def test_leading_hash_value_kept(self):
        # A value that *starts* with '#' (e.g. a colour) is a literal, not a comment.
        self.assertEqual(parse_env_line("COLOR=#FF0000"), ("COLOR", "#FF0000"))

    def test_url_fragment_kept(self):
        self.assertEqual(parse_env_line("U=https://x.com/p#frag"),
                         ("U", "https://x.com/p#frag"))

    def test_hash_inside_quotes_kept(self):
        self.assertEqual(strip_inline_comment('"a # b"  # tail'), '"a # b"')
        self.assertEqual(parse_env_line('K="a # b"  # tail'), ("K", "a # b"))

    def test_whole_line_comment_and_blank(self):
        self.assertIsNone(parse_env_line("# just a comment"))
        self.assertIsNone(parse_env_line("   "))
        self.assertIsNone(parse_env_line("no_equals_here"))

    def test_quotes_and_spacing(self):
        self.assertEqual(parse_env_line("  KEY = 'val'  "), ("KEY", "val"))
        self.assertEqual(parse_env_line('KEY="val"'), ("KEY", "val"))

    def test_load_env_acceptance(self):
        # Acceptance #1: a real .plugin.env line with an inline comment yields the clean URL.
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ".plugin.env"
            p.write_text("LARK_DOMAIN=https://open.larksuite.com   # x\nPASS=ab#cd\n",
                         encoding="utf-8")
            old = os.environ.get("QA_ENV_FILE")
            for k in ("LARK_DOMAIN", "PASS"):
                os.environ.pop(k, None)
            os.environ["QA_ENV_FILE"] = str(p)
            try:
                parsed = _env.load_env()
                self.assertEqual(parsed["LARK_DOMAIN"], "https://open.larksuite.com")
                self.assertEqual(parsed["PASS"], "ab#cd")
                from _env import env_str
                self.assertEqual(env_str("LARK_DOMAIN"), "https://open.larksuite.com")
            finally:
                if old is None:
                    os.environ.pop("QA_ENV_FILE", None)
                else:
                    os.environ["QA_ENV_FILE"] = old


class TestPlaceholderDetection(unittest.TestCase):
    def setUp(self):
        import lark_auth
        self.f = lark_auth.creds_are_placeholder

    def test_default_template_values_are_placeholder(self):
        self.assertTrue(self.f("cli_xxxxxxxxxxxxxxxx", "your_app_secret"))

    def test_empty_is_placeholder(self):
        self.assertTrue(self.f("", ""))
        self.assertTrue(self.f("cli_real", ""))

    def test_secret_placeholder_words(self):
        self.assertTrue(self.f("cli_realLookingId", "your_app_secret"))
        self.assertTrue(self.f("cli_realLookingId", "changeme"))

    def test_real_credentials_pass(self):
        self.assertFalse(self.f("cli_a1b2c3d4e5f6g7", "Zx9kQ2mWpL7nVt3sErA8bC"))

    def test_real_id_with_x_chars_but_not_all_x(self):
        # an id that merely contains x's (not the all-x placeholder) is real
        self.assertFalse(self.f("cli_9axb8cxd7e", "Zx9kQ2mWpL7nVt3sErA8bC"))


class TestReadScopeClassification(unittest.TestCase):
    def setUp(self):
        import lark_auth
        self.c = lark_auth._classify_read_scope
        self.GRANTED = lark_auth.GRANTED
        self.DENIED = lark_auth.DENIED
        self.UNKNOWN = lark_auth.UNKNOWN

    def test_success_is_granted(self):
        self.assertEqual(self.c(200, {"code": 0, "data": {}}), self.GRANTED)

    def test_scope_required_is_denied(self):
        jb = {"code": 99991672,
              "msg": "Access denied. One of the following scopes is required: "
                     "[wiki:wiki, wiki:wiki:readonly, wiki:node:read]"}
        self.assertEqual(self.c(403, jb), self.DENIED)

    def test_not_found_is_granted_scope_works(self):
        # node-not-exist while the scope IS held must NOT be reported as denied
        self.assertEqual(self.c(200, {"code": 131005, "msg": "node not exist"}), self.GRANTED)

    def test_bad_param_is_granted(self):
        self.assertEqual(self.c(200, {"code": 1770002, "msg": "invalid document id"}),
                         self.GRANTED)

    def test_network_error_is_unknown(self):
        self.assertEqual(self.c(0, {"_error": "timed out"}), self.UNKNOWN)


class TestErrorDiagnosis(unittest.TestCase):
    def setUp(self):
        import lark_auth
        self.d = lark_auth.diagnose_error

    def test_ssl(self):
        code, action = self.d("SSLCertVerificationError: CERTIFICATE_VERIFY_FAILED "
                              "self-signed certificate in certificate chain")
        self.assertEqual(code, "SSL_CERT")
        self.assertIn("SSL_CERT_FILE", action)

    def test_redirect_20029(self):
        code, _ = self.d("Invalid redirect URL. Error code: 20029")
        self.assertEqual(code, "REDIRECT_MISMATCH")

    def test_invalid_param_10003(self):
        code, _ = self.d("invalid param (code=10003)")
        self.assertEqual(code, "INVALID_PARAM")

    def test_scope_denied(self):
        code, _ = self.d("Access denied. One of the following scopes is required: [wiki:wiki]")
        self.assertEqual(code, "SCOPE_DENIED")

    def test_doc_denied(self):
        code, _ = self.d("permission denied for this document")
        self.assertIn(code, ("DOC_DENIED", "SCOPE_DENIED"))

    def test_unknown(self):
        code, _ = self.d("some totally unrelated network blip")
        self.assertEqual(code, "UNKNOWN")


class TestSslDetector(unittest.TestCase):
    def test_positive(self):
        self.assertTrue(is_ssl_cert_error("CERTIFICATE_VERIFY_FAILED"))
        self.assertTrue(is_ssl_cert_error("self-signed certificate in certificate chain"))
        self.assertTrue(is_ssl_cert_error("unable to get local issuer certificate"))

    def test_negative(self):
        self.assertFalse(is_ssl_cert_error("connection reset"))
        self.assertFalse(is_ssl_cert_error(""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
