"""Transition primitives for the video-transition-curve exercise.

All progress values are normalized to the closed interval ``[0, 1]``.
Frames are two-dimensional lists of floats in row-major order:
``frame[y][x]``, with ``h`` rows and ``w`` columns.  Masks use the same
shape, where ``0.0`` means "show A" and ``1.0`` means "show B".

Every function below is a stub that raises ``NotImplementedError`` until it
is implemented according to its docstring.  The test suite compares numbers
with an absolute tolerance of ``1e-6`` (``1e-9`` for the exact endpoint
checks).
"""

import math

TOLERANCE = 1e-6

EASINGS = ("linear", "in", "out", "inout", "back")
DIRECTIONS = ("left", "right", "top", "bottom")
KINDS = (
    "dissolve",
    "wipe_left",
    "wipe_right",
    "wipe_top",
    "wipe_bottom",
    "slide_left",
    "slide_right",
    "slide_top",
    "slide_bottom",
)


class TransitionError(ValueError):
    """Raised when transition parameters are invalid."""


def _clamp01(t):
    """Clamp ``t`` to the closed interval ``[0.0, 1.0]``."""
    return min(1.0, max(0.0, float(t)))


def _frame_shape(frame, label):
    """Return ``(h, w)`` of a rectangular non-empty frame, or raise."""
    if not frame:
        raise TransitionError("frame %s is empty" % label)
    w = len(frame[0])
    if w == 0:
        raise TransitionError("frame %s has zero-width rows" % label)
    for row in frame:
        if len(row) != w:
            raise TransitionError("frame %s is not rectangular" % label)
    return len(frame), w


def ease(name, t):
    """Ease normalized progress ``t`` with the curve called ``name``.

    ``t`` is clamped to ``[0.0, 1.0]`` before evaluation.  Curves:

    * ``"linear"``: ``t``
    * ``"in"``: ``t ** 2``
    * ``"out"``: ``1 - (1 - t) ** 2``
    * ``"inout"``: ``2 * t ** 2`` for ``t < 0.5``, else
      ``1 - 2 * (1 - t) ** 2``
    * ``"back"``: ease-out-back with ``c1 = 0.544`` and ``c3 = c1 + 1``:
      ``1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2``

    Every curve returns ``0.0`` when ``t == 0.0`` and ``1.0`` when
    ``t == 1.0`` (``back`` may overshoot ``1.0`` by at most 1% in between).
    An unknown name raises :class:`TransitionError`.
    """
    t = _clamp01(t)
    if name == "linear":
        return t
    if name == "in":
        return t ** 2
    if name == "out":
        return 1.0 - (1.0 - t) ** 2
    if name == "inout":
        if t < 0.5:
            return 2.0 * t ** 2
        return 1.0 - 2.0 * (1.0 - t) ** 2
    if name == "back":
        c1 = 0.544
        c3 = c1 + 1.0
        return 1.0 + c3 * (t - 1.0) ** 3 + c1 * (t - 1.0) ** 2
    raise TransitionError("unknown easing: %r" % (name,))


def dissolve(a, b, t):
    """Blend scalar ``a`` (frame A) into ``b`` (frame B) at progress ``t``.

    ``t`` is clamped to ``[0.0, 1.0]`` so the result never leaves the
    ``a..b`` range.  Returns ``(1 - t) * a + t * b``: ``t == 0`` returns
    ``a`` exactly and ``t == 1`` returns ``b`` exactly.
    """
    t = _clamp01(t)
    if t == 0.0:
        return float(a)
    if t == 1.0:
        return float(b)
    return (1.0 - t) * a + t * b


def wipe_mask(w, h, t, direction):
    """Build a sharp wipe mask of ``h`` rows by ``w`` columns.

    ``direction`` names the side the transition starts from:

    * ``"left"``: columns ``x < t * w`` are ``1.0``, the rest are ``0.0``
    * ``"right"``: columns ``x >= w - t * w`` are ``1.0``
    * ``"top"``: rows ``y < t * h`` are ``1.0``
    * ``"bottom"``: rows ``y >= h - t * h`` are ``1.0``

    The boundary is sharp: every value is exactly ``0.0`` or ``1.0``.
    ``t`` is clamped to ``[0.0, 1.0]``.  A non-positive ``w`` or ``h``, or
    an unknown direction, raises :class:`TransitionError` so that ``w == 0``
    can never divide by zero.
    """
    if w <= 0 or h <= 0:
        raise TransitionError("invalid frame size: w=%r h=%r" % (w, h))
    if direction not in DIRECTIONS:
        raise TransitionError("unknown direction: %r" % (direction,))
    t = _clamp01(t)
    mask = []
    for y in range(h):
        row = []
        for x in range(w):
            if direction == "left":
                on = x < t * w
            elif direction == "right":
                on = x >= w - t * w
            elif direction == "top":
                on = y < t * h
            else:  # "bottom"
                on = y >= h - t * h
            row.append(1.0 if on else 0.0)
        mask.append(row)
    return mask


def soft_wipe(mask, feather):
    """Feather a sharp wipe mask produced by :func:`wipe_mask`.

    ``mask`` is a rectangular 2D list of ``0.0`` / ``1.0`` values and
    ``feather`` is the ramp width in whole pixels.  The ramp straddles the
    original boundary and keeps exactly ``feather`` pixels partially
    visible; going from the ``0.0`` side to the ``1.0`` side its values are
    ``0.5 / feather, 1.5 / feather, ..., (feather - 0.5) / feather``.
    With ``feather == 0`` the mask is copied unchanged and stays binary.
    A negative ``feather`` raises :class:`TransitionError`.
    """
    if feather < 0:
        raise TransitionError("negative feather: %r" % (feather,))
    soft = [list(row) for row in mask]
    if feather == 0 or not soft:
        return soft
    h = len(soft)
    w = len(soft[0])
    for y in range(h):
        for x in range(w):
            value = mask[y][x]
            # Distance (in whole pixels) to the nearest pixel of the
            # opposite value, measured along the row and the column.
            best = None
            for xx in range(w):
                if mask[y][xx] != value:
                    d = abs(xx - x)
                    if best is None or d < best:
                        best = d
            for yy in range(h):
                if mask[yy][x] != value:
                    d = abs(yy - y)
                    if best is None or d < best:
                        best = d
            if best is None:
                continue
            ramp = (best - 0.5) / feather
            if value == 1.0:
                new = 0.5 + ramp
            else:
                new = 0.5 - ramp
            soft[y][x] = min(1.0, max(0.0, new))
    return soft


def slide_offset(t, distance, direction):
    """Return the ``(dx, dy)`` offset of the incoming frame at progress ``t``.

    The offset is measured from the frame's final position in screen
    coordinates (x grows to the right, y grows downwards), so ``t == 1``
    always returns ``(0.0, 0.0)``.  ``direction`` is the side the frame
    enters from:

    * ``"left"``: ``(-distance * (1 - t), 0)``
    * ``"right"``: ``(distance * (1 - t), 0)``
    * ``"top"``: ``(0, -distance * (1 - t))``
    * ``"bottom"``: ``(0, distance * (1 - t))``

    ``t`` is clamped to ``[0.0, 1.0]``; an unknown direction raises
    :class:`TransitionError`.
    """
    if direction not in DIRECTIONS:
        raise TransitionError("unknown direction: %r" % (direction,))
    t = _clamp01(t)
    d = float(distance) * (1.0 - t)
    if direction == "left":
        return (-d, 0.0)
    if direction == "right":
        return (d, 0.0)
    if direction == "top":
        return (0.0, -d)
    return (0.0, d)


def apply_transition(a, b, t, kind):
    """Render one transition between frames ``a`` and ``b`` at progress ``t``.

    Both frames are rectangular 2D lists with the same non-empty shape.
    ``kind`` is one of :data:`KINDS`:

    * ``"dissolve"``: per-pixel :func:`dissolve`
    * ``"wipe_<dir>"``: the :func:`wipe_mask` mask selects A or B per pixel
    * ``"slide_<dir>"``: B slides in from ``<dir>`` using
      :func:`slide_offset`, with ``distance`` equal to ``w`` for
      left/right and ``h`` for top/bottom; pixels not covered by B keep A

    The result is a new 2D list with exactly the shape of ``a`` (never
    ``w + 1`` or ``h + 1``).  ``t`` is clamped to ``[0.0, 1.0]`` so output
    values stay within ``[0.0, 1.0]``.  Mismatched or empty shapes, and
    unknown ``kind`` values, raise :class:`TransitionError`.
    """
    ha, wa = _frame_shape(a, "a")
    hb, wb = _frame_shape(b, "b")
    if (ha, wa) != (hb, wb):
        raise TransitionError(
            "frame shapes differ: a is %dx%d, b is %dx%d" % (ha, wa, hb, wb)
        )
    if kind not in KINDS:
        raise TransitionError("unknown transition kind: %r" % (kind,))
    t = _clamp01(t)
    h, w = ha, wa

    if kind == "dissolve":
        return [
            [dissolve(a[y][x], b[y][x], t) for x in range(w)]
            for y in range(h)
        ]

    if kind.startswith("wipe_"):
        direction = kind[len("wipe_"):]
        mask = wipe_mask(w, h, t, direction)
        return [
            [dissolve(a[y][x], b[y][x], mask[y][x]) for x in range(w)]
            for y in range(h)
        ]

    # "slide_<dir>": B slides in, pixels not covered by B keep A.
    direction = kind[len("slide_"):]
    distance = w if direction in ("left", "right") else h
    dx, dy = slide_offset(t, distance, direction)
    result = []
    for y in range(h):
        row = []
        for x in range(w):
            sx = int(round(x - dx))
            sy = int(round(y - dy))
            if 0 <= sx < w and 0 <= sy < h:
                row.append(float(b[sy][sx]))
            else:
                row.append(float(a[y][x]))
        result.append(row)
    return result


def validate(w, h, t, kind):
    """Return a list of human-readable problems with the parameters.

    An empty list means the parameters are valid.  Recognized problems:

    * ``w <= 0`` or ``h <= 0`` (invalid frame size)
    * ``t`` outside ``[0.0, 1.0]``
    * ``kind`` not present in :data:`KINDS`

    The function never raises for these conditions; callers such as
    :func:`transition_batch` decide whether to raise
    :class:`TransitionError`.
    """
    problems = []
    if w <= 0:
        problems.append("invalid frame width: %r" % (w,))
    if h <= 0:
        problems.append("invalid frame height: %r" % (h,))
    if not (0.0 <= t <= 1.0):
        problems.append("t out of range [0.0, 1.0]: %r" % (t,))
    if kind not in KINDS:
        problems.append("unknown transition kind: %r" % (kind,))
    return problems


def transition_batch(pairs, config):
    """Apply a transition to every pair and return the frames in order.

    ``pairs`` is a list of dicts with keys ``"a"`` and ``"b"`` (2D frames of
    equal, non-empty shape) and optional per-pair overrides ``"t"`` and
    ``"kind"``.  ``config`` is a dict whose ``"t"`` (default ``0.5``) and
    ``"kind"`` (default ``"dissolve"``) are used when a pair does not
    override them.

    Returns ``{"count": len(pairs), "frames": [frame, ...]}`` where frame
    ``i`` is the :func:`apply_transition` result for pair ``i``, in input
    order.  Every pair gets fresh state: masks, offsets and result rows are
    never shared between tasks.  If any pair is invalid (bad shape, unknown
    kind, ``t`` outside ``[0.0, 1.0]``, ...) the whole batch raises
    :class:`TransitionError` and no partial result is returned.
    """
    config = config or {}
    default_t = config.get("t", 0.5)
    default_kind = config.get("kind", "dissolve")

    frames = []
    for index, pair in enumerate(pairs):
        a = pair["a"]
        b = pair["b"]
        t = pair.get("t", default_t)
        kind = pair.get("kind", default_kind)

        ha, wa = _frame_shape(a, "a")
        hb, wb = _frame_shape(b, "b")
        problems = []
        if (ha, wa) != (hb, wb):
            problems.append(
                "frame shapes differ: a is %dx%d, b is %dx%d"
                % (ha, wa, hb, wb)
            )
        problems.extend(validate(wa, ha, t, kind))
        if problems:
            raise TransitionError(
                "invalid pair %d: %s" % (index, "; ".join(problems))
            )

        # Fresh mask/offset/result rows are built per call, so no state
        # is ever shared between pairs.
        frames.append(apply_transition(a, b, t, kind))

    return {"count": len(pairs), "frames": frames}
