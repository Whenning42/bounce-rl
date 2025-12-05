"""
Allowed input mappings for the BounceRL input system.

This module provides utilities for defining which keys are allowed in an
environment using either allow lists or deny lists.
"""

from typing import Union

from bounce_rl.input.keys import (
    Digits,
    FnKeys,
    Letters,
    Modifiers,
    MouseButtons,
    Other,
    Punctuation,
    ScrollButtons,
)

# Type alias for a key value
Key = int

# Type alias for a key class (tuple of keys)
KeyClass = tuple[Key, ...]

# Union type for constructor arguments
KeyOrKeyClass = Union[Key, KeyClass]


# All keys in the system (for deny list conversion)
_ALL_KEYS = (
    Letters
    + Digits
    + Punctuation
    + FnKeys
    + Modifiers
    + Other
    + MouseButtons
    + ScrollButtons
)


class AllowKeys:
    """
    An allow list of keys.

    Can be constructed from a mix of individual keys and key classes.
    The keys() method returns the deduplicated, expanded list of allowed keys.
    """

    def __init__(self, allowed: list[KeyOrKeyClass]):
        """
        Create an allow list from a list of keys and/or key classes.

        Args:
            allowed: List of keys (int) and/or key classes (tuples of keys)
        """
        self._allowed = allowed

    def keys(self) -> list[Key]:
        """
        Returns the expanded list of allowed keys, with duplicates removed.

        Returns:
            Deduplicated list of key values
        """
        expanded = []
        for item in self._allowed:
            if isinstance(item, tuple):
                # It's a key class - expand it
                expanded.extend(item)
            else:
                # It's a single key
                expanded.append(item)

        # Deduplicate while preserving order
        seen = set()
        result = []
        for key in expanded:
            if key not in seen:
                seen.add(key)
                result.append(key)

        return result


class DisallowKeys:
    """
    A deny list of keys.

    Can be constructed from a mix of individual keys and key classes.
    The to_allow_list() method converts this to an allow list containing
    all keys except the denied ones.
    """

    def __init__(self, disallowed: list[KeyOrKeyClass]):
        """
        Create a deny list from a list of keys and/or key classes.

        Args:
            disallowed: List of keys (int) and/or key classes (tuples of keys)
        """
        self._disallowed = disallowed

    def to_allow_list(self) -> AllowKeys:
        """
        Convert this deny list to an allow list.

        Returns all keys in the system except those in the deny list.

        Returns:
            AllowKeys instance containing all non-denied keys
        """
        # First, expand the disallow list
        disallowed_expanded = []
        for item in self._disallowed:
            if isinstance(item, tuple):
                disallowed_expanded.extend(item)
            else:
                disallowed_expanded.append(item)

        # Convert to set for efficient lookup
        disallowed_set = set(disallowed_expanded)

        # Build allowed list from all keys minus disallowed
        allowed = [key for key in _ALL_KEYS if key not in disallowed_set]

        return AllowKeys(allowed)
