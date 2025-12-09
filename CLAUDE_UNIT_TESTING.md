# Unit Testing Best Practices for Claude

This document outlines best practices for writing clean, maintainable unit tests in this project.

## Test Framework

Use the `unittest` package for all unit tests. Tests should be runnable with both `pytest` and `unittest`:

```python
import unittest

class TestMyFeature(unittest.TestCase):
    def test_specific_behavior(self):
        # test code here
        pass

if __name__ == "__main__":
    unittest.main()
```

## Test Structure

### Use Descriptive Test Names

Test names should clearly describe what behavior is being tested:

```python
# Good
def test_process_gym_action_relative_move(self):
def test_mask_action_masks_disallowed_keys(self):

# Bad
def test_process_gym_action_generates_mouse_actions(self):  # Too broad
def test_case_1(self):  # Non-descriptive
```

### One Test Per Behavior

Split tests that check multiple behaviors into separate test methods:

```python
# Bad - multiple test cases in one test
def test_process_gym_action_generates_mouse_actions(self):
    # Test case 1: Relative move
    ...
    # Test case 2: Absolute move
    ...
    # Test case 3: Drag
    ...

# Good - one test per behavior
def test_process_gym_action_relative_move(self):
    ...

def test_process_gym_action_absolute_move(self):
    ...

def test_process_gym_action_relative_drag(self):
    ...
```

## Code Organization

### Use Named Constants Instead of Magic Numbers

Always use named constants for indexing or accessing structured data:

```python
# Bad
masked_action[0]
masked_action[1]

# Good
masked_action[KEYS_INDEX]
masked_action[MOUSE_DISCRETE_INDEX]
```

### Create Helper Functions for Common Setup

Extract repeated setup code into helper functions:

```python
def no_op_gym_action():
    """Create a no-op gym action (all keys no-op, no mouse action)."""
    key_actions = np.zeros(len(ACTION_KEYS), dtype=int)
    mouse_discrete = np.array([MOUSE_ABSOLUTE, MOUSE_ACTION_NONE, MOUSE_DRAG_LEFT])
    mouse_position = np.array([0, 0])
    return [key_actions, mouse_discrete, mouse_position]

# Usage in tests
def test_something(self):
    action = no_op_gym_action()
    action[KEYS_INDEX][specific_index] = specific_value
    ...
```

This pattern makes it clear what's different from the baseline in each test.

## Assertions

### Use Dataclass Equality for Concise Comparisons

When comparing dataclass instances, construct expected objects and use direct equality:

```python
# Bad - checking each field individually
self.assertEqual(result[0].action, KeyActionType.KEY_PRESS)
self.assertEqual(result[0].key, KEY_A)
self.assertEqual(result[1].action, KeyActionType.KEY_DOWN)
self.assertEqual(result[1].key, KEY_B)

# Good - using dataclass equality
expected = [
    KeyAction(action=KeyActionType.KEY_PRESS, key=KEY_A),
    KeyAction(action=KeyActionType.KEY_DOWN, key=KEY_B),
]
self.assertEqual(result, expected)
```

### Inline Simple Values Into Assertions

For simple tests, inline expected values directly into assertions:

```python
# Bad - unnecessary variable
expected = [MouseAction(is_relative=True, position=(10, 20), is_drag=False, drag_button=None)]
self.assertEqual(result, expected)

# Good - inlined
self.assertEqual(
    result,
    [MouseAction(is_relative=True, position=(10, 20), is_drag=False, drag_button=None)]
)
```

### Inline Function Calls When Appropriate

For very simple tests, you can inline the function call being tested:

```python
# Before
result = process_gym_action(action, 800, 600)
self.assertEqual(result, expected)

# After (when test is simple enough)
self.assertEqual(
    process_gym_action(action, 800, 600),
    [MouseAction(is_relative=True, position=(10, 20), is_drag=False, drag_button=None)]
)
```

## Comments

### Use Descriptive Comments, Not Generic Labels

When comments are needed, describe what's happening, not the pattern:

```python
# Bad - generic pattern labels
# Setup
action = no_op_gym_action()
action[KEYS_INDEX] = np.ones(len(ACTION_KEYS), dtype=int)

# Act
masked_action = mask_action(action, allowed_list)

# Expect
self.assertEqual(...)

# Good - descriptive comments
# Create action with all keys set to KEY_PRESS
action = no_op_gym_action()
action[KEYS_INDEX] = np.ones(len(ACTION_KEYS), dtype=int)

# Mask action to disallow KEY_A and KEY_B
masked_action = mask_action(action, DisallowKeys([KEY_A, KEY_B]).to_allow_list())

# Disallowed keys should be KEY_NO_OP, others should remain KEY_PRESS
self.assertEqual(...)
```

### Remove Comments When Code Is Self-Explanatory

If the test is simple enough to understand without comments, remove them:

```python
# Before
def test_process_gym_action_relative_move(self):
    """Verify that relative mouse move is correctly converted."""
    # Setup gym action with relative mouse move
    action = no_op_gym_action()
    action[MOUSE_DISCRETE_INDEX] = np.array([MOUSE_RELATIVE, MOUSE_ACTION_MOVE, MOUSE_DRAG_LEFT])
    action[MOUSE_POSITION_INDEX] = np.array([10, 20])

    # Process the action
    result = process_gym_action(action, 800, 600)

    # Should generate expected mouse action
    self.assertEqual(result, expected)

# After
def test_process_gym_action_relative_move(self):
    """Verify that relative mouse move is correctly converted."""
    action = no_op_gym_action()
    action[MOUSE_DISCRETE_INDEX] = np.array([MOUSE_RELATIVE, MOUSE_ACTION_MOVE, MOUSE_DRAG_LEFT])
    action[MOUSE_POSITION_INDEX] = np.array([10, 20])

    self.assertEqual(
        process_gym_action(action, 800, 600),
        [MouseAction(is_relative=True, position=(10, 20), is_drag=False, drag_button=None)]
    )
```

## Example: Well-Structured Test

Here's a complete example following all these principles:

```python
def no_op_gym_action():
    """Create a no-op gym action (all keys no-op, no mouse action)."""
    key_actions = np.zeros(len(ACTION_KEYS), dtype=int)
    mouse_discrete = np.array([MOUSE_ABSOLUTE, MOUSE_ACTION_NONE, MOUSE_DRAG_LEFT])
    mouse_position = np.array([0, 0])
    return [key_actions, mouse_discrete, mouse_position]


class TestProcessGymAction(unittest.TestCase):
    """Tests for process_gym_action function."""

    def test_process_gym_action_relative_move(self):
        """Verify that relative mouse move is correctly converted."""
        action = no_op_gym_action()
        action[MOUSE_DISCRETE_INDEX] = np.array([MOUSE_RELATIVE, MOUSE_ACTION_MOVE, MOUSE_DRAG_LEFT])
        action[MOUSE_POSITION_INDEX] = np.array([10, 20])

        self.assertEqual(
            process_gym_action(action, 800, 600),
            [MouseAction(is_relative=True, position=(10, 20), is_drag=False, drag_button=None)]
        )
```

## Anti-Patterns to Avoid

1. **Don't test struct-only files** - Files that only contain dataclasses or simple type definitions don't need unit tests
2. **Don't use bare assertions** - Always use unittest assertion methods
3. **Don't batch assertions across different behaviors** - One test method per distinct behavior
4. **Don't use magic numbers** - Always use named constants
5. **Don't over-comment** - If the code is clear, comments just add noise
