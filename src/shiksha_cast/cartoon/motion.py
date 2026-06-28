"""Motion library for the cutout cartoon engine: pure functions that turn an action
+ time into joint-angle contributions (degrees) and a vertical bob. Composed by the
builder into a final pose per character per frame.
"""
from __future__ import annotations

import math

WALK_RATE = 7.5  # radians/sec of the walk cycle


def idle(t: float, phase_off: float = 0.0) -> dict:
    s = math.sin(t * 1.4 + phase_off)
    return {
        "angles": {"arm_left": 8 + 2 * s, "arm_right": -8 - 2 * s, "head": 1.5 * s,
                   "leg_left": 0.0, "leg_right": 0.0},
        "bob": 0.0,
    }


def walk(phase: float) -> dict:
    """phase in radians. Legs swing opposite; arms opposite to legs; body bobs."""
    leg, arm = 24.0, 18.0
    return {
        "angles": {
            "leg_left": leg * math.sin(phase + math.pi),
            "leg_right": leg * math.sin(phase),
            "arm_left": arm * math.sin(phase),
            "arm_right": arm * math.sin(phase + math.pi),
            "head": 2.0 * math.sin(phase * 2),
        },
        "bob": abs(math.sin(phase)) * 10.0,
    }


def wave(lt: float) -> dict:
    """Raise the right arm overhead and wiggle it (lt = local time in the action)."""
    return {"arm_right": -128 + 20 * math.sin(lt * 9.0)}


def point(side: str = "right") -> dict:
    return {"arm_right": -52} if side == "right" else {"arm_left": 52}


def jump_bob(prog: float) -> float:
    """prog 0..1 -> upward bob (px) following a parabola."""
    return math.sin(min(1.0, max(0.0, prog)) * math.pi) * 60.0


def blink_state(t: float, period: float = 3.4, dur: float = 0.12) -> str:
    return "closed" if (t % period) < dur else "open"
