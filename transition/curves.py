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
    raise NotImplementedError


def dissolve(a, b, t):
    """Blend scalar ``a`` (frame A) into ``b`` (frame B) at progress ``t``.

    ``t`` is clamped to ``[0.0, 1.0]`` so the result never leaves the
    ``a..b`` range.  Returns ``(1 - t) * a + t * b``: ``t == 0`` returns
    ``a`` exactly and ``t == 1`` returns ``b`` exactly.
    """
    raise NotImplementedError


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
    raise NotImplementedError


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
    raise NotImplementedError


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
    raise NotImplementedError


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
    raise NotImplementedError


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
    raise NotImplementedError


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
    raise NotImplementedError
