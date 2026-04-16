"""
Gravitational Attention — Physics-based replacement for Transformer attention.

Ported and adapted from MASSIVEMAGNETICS/black-hole (gravitational_attention.py)
and integrated into the NexusForge 2.0 framework.

Key concepts
------------
* Tokens are treated as **matter** — each has a *position* (location in
  semantic space-time) and a *mass* (learnable importance weight).
* Attention is modelled as **gravitational force**:

      F(i, j) = G × (M_i × M_j) / (distance(P_i, P_j)² + ε)

* An **event horizon** (ε) prevents division-by-zero singularities.
* **Hawking Radiation** clamps maximum force to prevent "black hole collapse"
  (attention collapse where one token dominates).
* Optional **space-time curvature** warps the distance metric, allowing the
  model to represent non-Euclidean semantic relationships.

This is a pure-NumPy implementation so it runs without PyTorch/TensorFlow.
"""

import math
from dataclasses import dataclass, field
from typing import Optional, List

import numpy as np


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class GravitationalConfig:
    """Hyper-parameters for :class:`GravitationalAttentionLayer`."""

    dim_model: int = 64
    """Model (token embedding) dimensionality."""

    dim_position: int = 16
    """Semantic space-time position dimensionality."""

    num_heads: int = 1
    """Number of parallel gravitational attention heads.

    .. note::
        Multi-head gravitational attention is reserved for a future extension.
        The current implementation is single-head regardless of this value.
        Setting ``num_heads > 1`` has no effect until multi-head support is added.
    """

    gravitational_constant: float = 1.0
    """Initial value of G (Newton's gravitational constant analogue)."""

    event_horizon: float = 1e-6
    """ε added to distance² to prevent singularities."""

    max_force: Optional[float] = None
    """Hawking Radiation cap on maximum force (``None`` = uncapped)."""

    curvature: float = 0.0
    """Space-time curvature (0 = flat Euclidean, > 0 = curved)."""

    learnable_G: bool = True
    """Whether G is a trainable parameter.

    * ``True``  — ``_log_G`` is stored as mutable state; a gradient-based
      training loop can update it via ``layer._log_G += lr * grad``.
    * ``False`` — G is frozen at its initial value; ``layer.G`` always returns
      ``gravitational_constant`` unchanged.
    """


# ---------------------------------------------------------------------------
# Layer
# ---------------------------------------------------------------------------


class GravitationalAttentionLayer:
    """
    Gravitational Attention Layer.

    Drop-in replacement for the standard Transformer attention block.
    Instead of Query–Key–Value dot-product similarity it computes
    gravitational forces between token *positions* weighted by token *masses*.

    The forward pass:
    1. Project input ``X`` → semantic positions ``P`` and masses ``M``.
    2. Project input ``X`` → values ``V`` (information payload).
    3. Compute force matrix ``F(i, j) = G × M_i × M_j / (dist(P_i,P_j)² + ε)``.
    4. Apply softmax over forces to produce attention weights.
    5. Aggregate: ``output = softmax(F) @ V``.
    6. Final output projection.

    Args:
        config: :class:`GravitationalConfig` hyper-parameters.
        seed: Optional random seed for reproducible weight initialisation.

    Example::

        cfg = GravitationalConfig(dim_model=32, dim_position=8)
        layer = GravitationalAttentionLayer(cfg)
        X = np.random.randn(1, 10, 32)   # batch=1, seq_len=10, d_model=32
        output = layer.forward(X)         # shape: (1, 10, 32)
    """

    def __init__(self, config: GravitationalConfig, seed: Optional[int] = None):
        self.config = config
        rng = np.random.default_rng(seed)

        d = config.dim_model
        dp = config.dim_position

        # Projection matrices (Xavier initialisation)
        self.W_position = self._xavier(d, dp, rng)   # d_model → d_position
        self.W_mass = self._xavier(d, 1, rng)         # d_model → mass scalar
        self.W_value = self._xavier(d, d, rng)        # d_model → d_model
        self.W_output = self._xavier(d, d, rng)       # d_model → d_model

        # Gravitational constant — stored in log-space when learnable so that
        # any gradient step keeps G positive.  When not learnable, _fixed_G
        # holds the frozen initial value.
        self._log_G = math.log(max(config.gravitational_constant, 1e-8))
        self._fixed_G: float = config.gravitational_constant

        # Metric tensor for curved space-time
        if config.curvature > 0:
            self._metric = self._build_metric(dp, config.curvature)
        else:
            self._metric = np.eye(dp)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    @property
    def G(self) -> float:
        """Current gravitational constant (always positive).

        Returns the fixed initial value when ``config.learnable_G`` is
        ``False``; otherwise returns ``exp(_log_G)`` which a training loop
        can update by adjusting ``_log_G``.
        """
        if not self.config.learnable_G:
            return self._fixed_G
        return math.exp(self._log_G)

    def forward(
        self,
        X: np.ndarray,
        mask: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Gravitational attention forward pass.

        Args:
            X: Token embeddings, shape ``(batch, seq_len, dim_model)``.
            mask: Optional boolean mask ``(batch, seq_len, seq_len)``.
                  ``True`` positions are *masked out* (set to -∞ before softmax).

        Returns:
            Output tensor, same shape as ``X``.
        """
        # 1. Positions and masses
        positions = X @ self.W_position           # (B, L, dp)
        raw_mass = X @ self.W_mass                 # (B, L, 1)
        # Numerically-stable softplus: log(1 + exp(x)) = log1p(exp(-|x|)) + max(x, 0)
        # avoids overflow for large positive raw_mass values.
        masses = (
            np.log1p(np.exp(-np.abs(raw_mass))) + np.maximum(raw_mass, 0) + 0.01
        )

        # 2. Values
        values = X @ self.W_value                  # (B, L, d)

        # 3. Gravitational force matrix
        force = self._compute_forces(positions, masses)  # (B, L, L)

        # 4. Optional mask
        if mask is not None:
            force = np.where(mask, -1e9, force)

        # 5. Softmax over forces → attention weights
        attn = self._softmax(force)                # (B, L, L)

        # 6. Weighted aggregation
        out = attn @ values                        # (B, L, d)

        # 7. Output projection
        out = out @ self.W_output                  # (B, L, d)
        return out

    # ------------------------------------------------------------------
    # Force computation
    # ------------------------------------------------------------------

    def _compute_forces(
        self, positions: np.ndarray, masses: np.ndarray
    ) -> np.ndarray:
        """
        Compute pairwise gravitational forces.

        ``F(i, j) = G × M_i × M_j / (dist²(P_i, P_j) + ε)``

        Args:
            positions: ``(B, L, dp)``
            masses: ``(B, L, 1)``

        Returns:
            Force matrix ``(B, L, L)``
        """
        # Pairwise distance² using the (possibly curved) metric
        # positions_i: (B, L, 1, dp), positions_j: (B, 1, L, dp)
        pi = positions[:, :, np.newaxis, :]
        pj = positions[:, np.newaxis, :, :]
        diff = pi - pj                            # (B, L, L, dp)

        if self.config.curvature > 0:
            # Curved: d² = diff @ metric @ diff.T  (per pair)
            temp = diff @ self._metric             # (B, L, L, dp)
            dist2 = np.sum(temp * diff, axis=-1)   # (B, L, L)
        else:
            dist2 = np.sum(diff ** 2, axis=-1)     # (B, L, L)

        dist2 = dist2 + self.config.event_horizon

        # Mass products
        mi = masses[:, :, np.newaxis, :]           # (B, L, 1, 1)
        mj = masses[:, np.newaxis, :, :]           # (B, 1, L, 1)
        mass_prod = (mi * mj).squeeze(-1)          # (B, L, L)

        force = self.G * mass_prod / dist2

        # Hawking Radiation cap
        if self.config.max_force is not None:
            force = np.minimum(force, self.config.max_force)

        return force

    # ------------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _xavier(fan_in: int, fan_out: int, rng: np.random.Generator) -> np.ndarray:
        limit = math.sqrt(6.0 / (fan_in + fan_out))
        return rng.uniform(-limit, limit, (fan_in, fan_out))

    @staticmethod
    def _softmax(x: np.ndarray) -> np.ndarray:
        """Numerically stable softmax over the last axis."""
        shifted = x - x.max(axis=-1, keepdims=True)
        exp_x = np.exp(shifted)
        return exp_x / (exp_x.sum(axis=-1, keepdims=True) + 1e-12)

    @staticmethod
    def _build_metric(dp: int, curvature: float) -> np.ndarray:
        """Build a Schwarzschild-inspired curved-space metric tensor."""
        metric = np.eye(dp)
        for i in range(dp):
            for j in range(dp):
                if i != j:
                    metric[i, j] = curvature * math.exp(-abs(i - j) / dp)
        return metric
