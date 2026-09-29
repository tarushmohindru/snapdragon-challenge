"""Import frozen experiment code without changing its locked files."""
import sys
from pathlib import Path

EXPERIMENT = Path(__file__).resolve().parents[1] / 'experiments/cliptrail'
if str(EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT))

from benchmark_core import static_selection  # noqa: E402
from reference_backend import ClipReference, cosine, sha256  # noqa: E402


def scene_indices(changes, budget=16):
    """The exact benchmark scene selector, with its original tie rules."""
    return static_selection('scene', changes, min(budget, len(changes)))
