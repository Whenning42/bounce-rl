"""Tests for allowed_inputs.py"""

import unittest
from bounce_rl.input.allowed_inputs import AllowKeys, DisallowKeys
from bounce_rl.input.keys import (
    KEY_A, KEY_B, KEY_C, KEY_D, KEY_E, KEY_Z, KEY_0, KEY_1,
    Letters, Digits, FnKeys, KEY_F1, KEY_F12
)


class TestAllowKeys(unittest.TestCase):
    """Tests for AllowKeys class."""

    def test_allow_list_deduplicates_keys(self):
        """Verify AllowList.keys() de-duplicates any duplicate keys."""
        # Create an allow list with duplicates
        allow_list = AllowKeys([KEY_A, KEY_B, KEY_A, KEY_C, KEY_B])
        keys = allow_list.keys()

        # Should have deduplicated keys in order of first appearance
        self.assertEqual(keys, [KEY_A, KEY_B, KEY_C])

    def test_allow_list_expands_key_classes(self):
        """Verify AllowList expands key classes correctly."""
        # Create an allow list with key classes
        allow_list = AllowKeys([Letters, Digits])
        keys = allow_list.keys()

        # Should have all letters and digits
        self.assertEqual(len(keys), 26 + 10)
        self.assertIn(KEY_A, keys)
        for letter in Letters:
            self.assertIn(letter, keys)
        for digit in Digits:
            self.assertIn(digit, keys)

    def test_allow_list_mixed_keys_and_classes(self):
        """Verify AllowList handles mix of individual keys and classes."""
        allow_list = AllowKeys([KEY_A, Digits, KEY_B])
        keys = allow_list.keys()

        # Should have A, B, and all digits
        self.assertIn(KEY_A, keys)
        self.assertIn(KEY_B, keys)
        for digit in Digits:
            self.assertIn(digit, keys)
        self.assertEqual(len(keys), 2 + 10)  # A, B, and 10 digits

    def test_allow_list_deduplicates_across_classes(self):
        """Verify deduplication works even when key appears in multiple classes."""
        # Manually create a scenario with overlap
        allow_list = AllowKeys([KEY_A, Letters])
        keys = allow_list.keys()

        # KEY_A appears twice (once alone, once in Letters), should deduplicate
        self.assertEqual(keys.count(KEY_A), 1)
        self.assertEqual(len(keys), 26)  # Just the 26 letters


class TestDisallowKeys(unittest.TestCase):
    """Tests for DisallowKeys class."""

    def test_deny_list_to_allow_list(self):
        """Verify DenyList.to_allow_list() returns all keys minus denied ones."""
        # Deny just a few keys
        deny_list = DisallowKeys([KEY_A, KEY_B, KEY_C])
        allow_list = deny_list.to_allow_list()
        keys = allow_list.keys()

        # Should not contain denied keys
        self.assertNotIn(KEY_A, keys)
        self.assertNotIn(KEY_B, keys)
        self.assertNotIn(KEY_C, keys)

        # Should contain other keys
        self.assertIn(KEY_D, keys)
        self.assertIn(KEY_E, keys)
        self.assertIn(KEY_0, keys)
        self.assertIn(KEY_1, keys)

    def test_deny_list_with_key_classes(self):
        """Verify DenyList works with key classes."""
        # Deny all function keys
        deny_list = DisallowKeys([FnKeys])
        allow_list = deny_list.to_allow_list()
        keys = allow_list.keys()

        # Should not contain any function keys
        self.assertNotIn(KEY_F1, keys)
        self.assertNotIn(KEY_F12, keys)
        for fkey in FnKeys:
            self.assertNotIn(fkey, keys)

        # Should still contain letters and digits
        self.assertIn(KEY_A, keys)
        self.assertIn(KEY_0, keys)

    def test_deny_list_mixed(self):
        """Verify DenyList works with mix of keys and classes."""
        # Deny specific keys and a class
        deny_list = DisallowKeys([KEY_A, Digits, KEY_B])
        allow_list = deny_list.to_allow_list()
        keys = allow_list.keys()

        # Should not contain A, B, or any digits
        self.assertNotIn(KEY_A, keys)
        self.assertNotIn(KEY_B, keys)
        for digit in Digits:
            self.assertNotIn(digit, keys)

        # Should contain other letters
        self.assertIn(KEY_C, keys)
        self.assertIn(KEY_Z, keys)


if __name__ == "__main__":
    unittest.main()
