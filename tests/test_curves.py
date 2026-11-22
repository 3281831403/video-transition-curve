"""Contract tests for ``transition.curves``.

Every test calls one or more of the stubs in ``transition.curves``, so the
suite starts red (exactly ``15 failed``) and turns green once the contracts
in the module docstrings are implemented.  Test inputs are assembled as
dicts and passed to the stubs as keyword arguments.
"""

import pytest

import transition.curves as curves

TOL = 1e-6


def make_frame(h, w, value):
    """Return an ``h`` by ``w`` frame filled with ``value``."""
    return [[float(value)] * w for _ in range(h)]


def flatten(frame):
    """Return the row-major values of a 2D frame as one flat list."""
    return [value for row in frame for value in row]


def test_ease_endpoints_are_exact():
    for name in curves.EASINGS:
        for t in (0.0, 1.0):
            params = {"name": name, "t": t}
            value = curves.ease(**params)
            assert value == pytest.approx(t, abs=TOL), (params, value)


def test_dissolve_endpoints_are_exact():
    params = {"a": 0.2, "b": 0.9, "t": 0.0}
    assert curves.dissolve(**params) == pytest.approx(0.2, abs=TOL)
    params = {"a": 0.2, "b": 0.9, "t": 1.0}
    assert curves.dissolve(**params) == pytest.approx(0.9, abs=1e-9)
    params = {"a": 0.2, "b": 0.9, "t": 0.5}
    assert curves.dissolve(**params) == pytest.approx(0.55, abs=TOL)


def test_wipe_mask_direction():
    params = {"w": 4, "h": 1, "t": 0.5, "direction": "left"}
    assert curves.wipe_mask(**params) == [[1.0, 1.0, 0.0, 0.0]]
    params = {"w": 4, "h": 1, "t": 0.5, "direction": "right"}
    assert curves.wipe_mask(**params) == [[0.0, 0.0, 1.0, 1.0]]
    params = {"w": 1, "h": 4, "t": 0.5, "direction": "top"}
    assert curves.wipe_mask(**params) == [[1.0], [1.0], [0.0], [0.0]]
    params = {"w": 1, "h": 4, "t": 0.5, "direction": "bottom"}
    assert curves.wipe_mask(**params) == [[0.0], [0.0], [1.0], [1.0]]


def test_soft_wipe_feather_width():
    params = {"w": 8, "h": 1, "t": 0.5, "direction": "left"}
    mask = curves.wipe_mask(**params)
    params = {"mask": mask, "feather": 4}
    row = curves.soft_wipe(**params)[0]
    expected = [1.0, 1.0, 0.875, 0.625, 0.375, 0.125, 0.0, 0.0]
    assert row == pytest.approx(expected, abs=TOL)
    assert len([value for value in row if 0.0 < value < 1.0]) == 4


def test_slide_offset_direction_signs():
    cases = [
        ({"t": 0.0, "distance": 100.0, "direction": "left"}, (-100.0, 0.0)),
        ({"t": 0.0, "distance": 100.0, "direction": "right"}, (100.0, 0.0)),
        ({"t": 0.0, "distance": 100.0, "direction": "top"}, (0.0, -100.0)),
        ({"t": 0.0, "distance": 100.0, "direction": "bottom"}, (0.0, 100.0)),
    ]
    for params, expected in cases:
        dx, dy = curves.slide_offset(**params)
        assert dx == pytest.approx(expected[0], abs=TOL), params
        assert dy == pytest.approx(expected[1], abs=TOL), params
    params = {"t": 0.25, "distance": 100.0, "direction": "left"}
    assert curves.slide_offset(**params) == pytest.approx((-75.0, 0.0), abs=TOL)


def test_apply_transition_keeps_size():
    a = make_frame(3, 5, 0.0)
    b = make_frame(3, 5, 1.0)
    for kind in curves.KINDS:
        params = {"a": a, "b": b, "t": 0.5, "kind": kind}
        result = curves.apply_transition(**params)
        assert len(result) == 3, (kind, len(result))
        assert all(len(row) == 5 for row in result), kind
        assert all(0.0 <= value <= 1.0 for row in result for value in row), kind


def test_unknown_kind_is_rejected():
    params = {"w": 4, "h": 4, "t": 0.5, "kind": "spin_around"}
    assert curves.validate(**params), params
    params = {
        "a": make_frame(2, 2, 0.0),
        "b": make_frame(2, 2, 1.0),
        "t": 0.5,
        "kind": "spin_around",
    }
    with pytest.raises(curves.TransitionError):
        curves.apply_transition(**params)


def test_out_of_range_t_is_clamped():
    params = {"a": 0.0, "b": 1.0, "t": 1.5}
    assert curves.dissolve(**params) == pytest.approx(1.0, abs=TOL)
    params = {"a": 0.0, "b": 1.0, "t": -0.5}
    assert curves.dissolve(**params) == pytest.approx(0.0, abs=TOL)
    params = {
        "a": make_frame(2, 2, 0.0),
        "b": make_frame(2, 2, 1.0),
        "t": 1.4,
        "kind": "dissolve",
    }
    result = curves.apply_transition(**params)
    assert all(value == pytest.approx(1.0, abs=TOL) for row in result for value in row)
    params = {"w": 4, "h": 4, "t": 1.4, "kind": "dissolve"}
    assert curves.validate(**params), params


def test_batch_uses_independent_masks():
    pairs = [
        {
            "a": make_frame(2, 2, 0.0),
            "b": make_frame(2, 2, 1.0),
            "t": 0.5,
            "kind": "wipe_left",
        },
        {
            "a": make_frame(3, 4, 0.0),
            "b": make_frame(3, 4, 1.0),
            "t": 0.5,
            "kind": "wipe_top",
        },
    ]
    params = {"pairs": pairs, "config": {}}
    result = curves.transition_batch(**params)
    frames = result["frames"]
    assert result["count"] == 2
    assert flatten(frames[0]) == pytest.approx([1.0, 0.0, 1.0, 0.0], abs=TOL)
    assert flatten(frames[1]) == pytest.approx(
        [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        abs=TOL,
    )
    assert frames[0] is not frames[1]

    bad_pairs = [
        {
            "a": make_frame(2, 2, 0.0),
            "b": make_frame(2, 2, 1.0),
            "t": 0.5,
            "kind": "wipe_left",
        },
        {
            "a": make_frame(2, 2, 0.0),
            "b": make_frame(2, 2, 1.0),
            "t": 1.5,
            "kind": "dissolve",
        },
    ]
    with pytest.raises(curves.TransitionError):
        curves.transition_batch(pairs=bad_pairs, config={})


def test_zero_width_wipe_is_rejected():
    params = {"w": 0, "h": 4, "t": 0.5, "direction": "left"}
    with pytest.raises(curves.TransitionError):
        curves.wipe_mask(**params)
    params = {"w": 0, "h": 4, "t": 0.5, "kind": "wipe_left"}
    assert curves.validate(**params), params


def test_t_zero_returns_a():
    a = [[0.0, 0.25], [0.5, 1.0]]
    b = make_frame(2, 2, 1.0)
    for kind in ("dissolve", "wipe_left", "slide_left"):
        params = {"a": a, "b": b, "t": 0.0, "kind": kind}
        result = curves.apply_transition(**params)
        assert flatten(result) == pytest.approx(flatten(a), abs=1e-9), kind


def test_t_one_returns_b():
    a = make_frame(2, 2, 0.0)
    b = [[1.0, 0.75], [0.5, 0.0]]
    for kind in ("dissolve", "wipe_left", "slide_left"):
        params = {"a": a, "b": b, "t": 1.0, "kind": kind}
        result = curves.apply_transition(**params)
        assert flatten(result) == pytest.approx(flatten(b), abs=1e-9), kind


def test_feather_zero_keeps_mask_binary():
    params = {"w": 6, "h": 2, "t": 0.5, "direction": "left"}
    mask = curves.wipe_mask(**params)
    params = {"mask": mask, "feather": 0}
    soft = curves.soft_wipe(**params)
    for row in soft:
        for value in row:
            assert value in (0.0, 1.0), value


def test_zero_width_apply_is_rejected():
    params = {"a": [[], []], "b": [[], []], "t": 0.5, "kind": "dissolve"}
    with pytest.raises(curves.TransitionError):
        curves.apply_transition(**params)


def test_batch_preserves_order():
    first_a = make_frame(2, 2, 0.0)
    first_b = make_frame(2, 2, 1.0)
    second_a = make_frame(2, 2, 1.0)
    second_b = make_frame(2, 2, 0.0)
    pairs = [
        {"a": first_a, "b": first_b},
        {"a": second_a, "b": second_b},
    ]
    params = {"pairs": pairs, "config": {"t": 1.0, "kind": "dissolve"}}
    result = curves.transition_batch(**params)
    frames = result["frames"]
    assert len(frames) == 2
    assert flatten(frames[0]) == pytest.approx(flatten(first_b), abs=1e-9)
    assert flatten(frames[1]) == pytest.approx(flatten(second_b), abs=1e-9)
