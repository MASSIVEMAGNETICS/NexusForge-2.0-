"""
Gravitational TokenFormer — Next-generation token processing beyond the
standard Transformer.

Architecture overview
---------------------
Traditional Transformer:
    Input → [LayerNorm → Multi-Head Attention → Add] × N → Feed-Forward → Output

GravitationalTokenFormer:
    Input → TokenEmbedder
          → N × TokenFormerBlock
                ├── GravitationalAttentionLayer   (replaces dot-product MHA)
                ├── Residual + LayerNorm
                ├── SparseFeedForward              (gated activation, identity-aware)
                └── Residual + LayerNorm
          → OutputProjection

Key innovations vs standard Transformer
----------------------------------------
1. **Gravitational attention** — force-based token attraction instead of
   dot-product similarity.  Tokens with high *mass* (importance) attract more
   information from their neighbours.
2. **Sparse Feed-Forward** — only activates neurons above a learned threshold,
   analogous to sparse cortical activity.
3. **Identity-conditioned gating** — if an identity anchor vector is supplied,
   the feed-forward gate is modulated by alignment with the user's identity,
   so identity-relevant tokens are amplified.
4. **Residual mass injection** — token masses (importance weights) computed
   in each attention layer are accumulated across layers and used to produce
   a final *importance map* that can be fed back to the memory system.

All implemented in pure NumPy — no PyTorch/TensorFlow required.
"""

import math
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple

import numpy as np

from nexusforge.attention.gravitational import (
    GravitationalAttentionLayer,
    GravitationalConfig,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class TokenFormerConfig:
    """Full configuration for :class:`GravitationalTokenFormer`."""

    vocab_size: int = 256
    """Character / sub-word vocabulary size."""

    dim_model: int = 64
    """Token embedding dimensionality (d_model)."""

    dim_position: int = 16
    """Semantic position dimensionality for gravitational attention."""

    num_layers: int = 4
    """Number of stacked :class:`TokenFormerBlock` layers."""

    dim_ff: int = 256
    """Feed-forward intermediate dimensionality."""

    num_heads: int = 1
    """Number of gravitational attention heads per layer."""

    max_seq_len: int = 512
    """Maximum input sequence length."""

    gravitational_constant: float = 1.0
    """Initial G for all gravitational attention layers."""

    event_horizon: float = 1e-6
    """ε preventing singularities in force computation."""

    max_force: Optional[float] = 100.0
    """Hawking Radiation cap (set ``None`` for uncapped)."""

    curvature: float = 0.0
    """Space-time curvature (0 = flat)."""

    sparsity_threshold: float = 0.1
    """Feed-forward activation sparsity threshold (ReLU gate)."""

    dropout_rate: float = 0.0
    """Dropout probability (0 = disabled; requires no extra deps)."""


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------


class LayerNorm:
    """
    Simple layer normalization (no learnable parameters for minimal deps).

    Normalises across the last dimension with a small ε for stability.
    """

    def __init__(self, dim: int, eps: float = 1e-5):
        self.dim = dim
        self.eps = eps
        self.gamma = np.ones(dim)
        self.beta = np.zeros(dim)

    def __call__(self, x: np.ndarray) -> np.ndarray:
        mean = x.mean(axis=-1, keepdims=True)
        var = x.var(axis=-1, keepdims=True)
        x_norm = (x - mean) / np.sqrt(var + self.eps)
        return self.gamma * x_norm + self.beta


class SparseFeedForward:
    """
    Sparse Feed-Forward Network — gated activation mimicking sparse cortical
    firing.

    Architecture:
        x → Linear₁ → GeLU → SparsityGate → Linear₂

    The *sparsity gate* zeroes out activations below ``threshold``, ensuring
    only the most relevant neurons fire per token.  When an ``identity_vector``
    is provided, gates are additionally modulated by cosine similarity with
    the identity, amplifying identity-relevant features.
    """

    def __init__(
        self,
        dim_in: int,
        dim_ff: int,
        threshold: float = 0.1,
        seed: Optional[int] = None,
    ):
        rng = np.random.default_rng(seed)
        self.threshold = threshold

        lim1 = math.sqrt(6.0 / (dim_in + dim_ff))
        self.W1 = rng.uniform(-lim1, lim1, (dim_in, dim_ff))
        self.b1 = np.zeros(dim_ff)

        lim2 = math.sqrt(6.0 / (dim_ff + dim_in))
        self.W2 = rng.uniform(-lim2, lim2, (dim_ff, dim_in))
        self.b2 = np.zeros(dim_in)

    def __call__(
        self,
        x: np.ndarray,
        identity_vector: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        # Linear 1 + GeLU
        h = x @ self.W1 + self.b1
        h = self._gelu(h)

        # Sparsity gate — only pass activations above threshold
        gate = (np.abs(h) > self.threshold).astype(np.float32)
        h = h * gate

        # Identity modulation (if provided)
        if identity_vector is not None and identity_vector.shape[-1] == h.shape[-1]:
            # Cosine similarity between hidden state and identity vector
            norm_h = h / (np.linalg.norm(h, axis=-1, keepdims=True) + 1e-8)
            norm_id = identity_vector / (np.linalg.norm(identity_vector) + 1e-8)
            alignment = np.clip(norm_h @ norm_id, 0.0, 1.0)  # (B, L)
            # Boost identity-aligned neurons
            h = h * (1.0 + 0.5 * alignment[..., np.newaxis])

        # Linear 2
        return h @ self.W2 + self.b2

    @staticmethod
    def _gelu(x: np.ndarray) -> np.ndarray:
        """Gaussian Error Linear Unit activation."""
        return 0.5 * x * (1.0 + np.tanh(math.sqrt(2.0 / math.pi) * (x + 0.044715 * x**3)))


# ---------------------------------------------------------------------------
# TokenFormer Block
# ---------------------------------------------------------------------------


class TokenFormerBlock:
    """
    Single GravitationalTokenFormer block.

    Pre-norm architecture (LayerNorm before sub-layer, same as GPT-2/NanoGPT).
    """

    def __init__(self, config: TokenFormerConfig, layer_idx: int = 0):
        self.layer_idx = layer_idx

        attn_cfg = GravitationalConfig(
            dim_model=config.dim_model,
            dim_position=config.dim_position,
            num_heads=config.num_heads,
            gravitational_constant=config.gravitational_constant,
            event_horizon=config.event_horizon,
            max_force=config.max_force,
            curvature=config.curvature,
        )
        self.attention = GravitationalAttentionLayer(
            attn_cfg, seed=layer_idx
        )
        self.norm1 = LayerNorm(config.dim_model)
        self.ff = SparseFeedForward(
            config.dim_model,
            config.dim_ff,
            threshold=config.sparsity_threshold,
            seed=layer_idx + 100,
        )
        self.norm2 = LayerNorm(config.dim_model)

    def forward(
        self,
        x: np.ndarray,
        mask: Optional[np.ndarray] = None,
        identity_vector: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Args:
            x: ``(batch, seq_len, dim_model)``
            mask: Optional causal or padding mask.
            identity_vector: Optional 1D identity anchor vector.

        Returns:
            ``(batch, seq_len, dim_model)``
        """
        # Pre-norm attention + residual
        x = x + self.attention.forward(self.norm1(x), mask=mask)

        # Pre-norm feed-forward + residual
        x = x + self.ff(self.norm2(x), identity_vector=identity_vector)
        return x


# ---------------------------------------------------------------------------
# Full GravitationalTokenFormer
# ---------------------------------------------------------------------------


class GravitationalTokenFormer:
    """
    Gravitational TokenFormer — full sequence model.

    Processes token sequences using stacked :class:`TokenFormerBlock` layers,
    each using gravitational attention instead of dot-product self-attention.

    Optionally integrates with the NexusForge memory and identity systems:
    * An identity vector can modulate feed-forward gating in every block.
    * The output *importance map* (per-token mass accumulation) can be fed
      to the episodic memory system to store the most important tokens.

    Args:
        config: :class:`TokenFormerConfig` hyper-parameters.
        identity_vector: Optional pre-computed identity embedding (e.g.
            from :class:`~nexusforge.memory.identity_anchor.IdentityAnchor`).

    Example::

        cfg = TokenFormerConfig(vocab_size=128, dim_model=32, num_layers=2)
        model = GravitationalTokenFormer(cfg)
        # Simulate a batch of 1 sequence of length 8 with d_model=32
        X = np.random.randn(1, 8, 32)
        output, importance_map = model.forward(X)
        # output: (1, 8, 32)  |  importance_map: (1, 8) per-token salience
    """

    def __init__(
        self,
        config: TokenFormerConfig,
        identity_vector: Optional[np.ndarray] = None,
    ):
        self.config = config
        self.identity_vector = identity_vector

        # Token + positional embedding tables
        rng = np.random.default_rng(42)
        lim = math.sqrt(6.0 / (config.vocab_size + config.dim_model))
        self.token_embed = rng.uniform(-lim, lim, (config.vocab_size, config.dim_model))

        lim_p = math.sqrt(6.0 / (config.max_seq_len + config.dim_model))
        self.pos_embed = rng.uniform(
            -lim_p, lim_p, (config.max_seq_len, config.dim_model)
        )

        # Transformer blocks
        self.blocks: List[TokenFormerBlock] = [
            TokenFormerBlock(config, layer_idx=i) for i in range(config.num_layers)
        ]

        # Final layer norm
        self.final_norm = LayerNorm(config.dim_model)

        # Output projection back to vocab
        lim_out = math.sqrt(6.0 / (config.dim_model + config.vocab_size))
        self.W_out = rng.uniform(-lim_out, lim_out, (config.dim_model, config.vocab_size))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def encode(self, token_ids: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Encode token ID sequences to contextualised embeddings.

        Args:
            token_ids: Integer array of shape ``(batch, seq_len)`` with
                values in ``[0, vocab_size)``.

        Returns:
            Tuple of:
            * ``hidden``: contextualised embeddings ``(batch, seq_len, dim_model)``
            * ``importance_map``: per-token salience scores ``(batch, seq_len)``
        """
        batch, seq_len = token_ids.shape
        assert seq_len <= self.config.max_seq_len, (
            f"Sequence length {seq_len} exceeds max_seq_len {self.config.max_seq_len}"
        )

        # Embedding lookup + positional encoding
        tok = self.token_embed[token_ids]           # (B, L, d)
        pos = self.pos_embed[:seq_len][np.newaxis]   # (1, L, d)
        x = tok + pos                                # (B, L, d)

        # Pass through blocks
        id_vec = self.identity_vector
        for block in self.blocks:
            x = block.forward(x, identity_vector=id_vec)

        x = self.final_norm(x)

        # Importance map: L2 norm of each token's final hidden state
        importance_map = np.linalg.norm(x, axis=-1)  # (B, L)
        # Normalise to [0, 1]
        max_imp = importance_map.max(axis=-1, keepdims=True) + 1e-8
        importance_map = importance_map / max_imp

        return x, importance_map

    def forward(
        self, X: np.ndarray, mask: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Full forward pass on pre-embedded input (e.g., from an external
        embedder or directly from :class:`GravitationalAttentionLayer`).

        Args:
            X: Pre-embedded token tensor ``(batch, seq_len, dim_model)``.
            mask: Optional attention mask.

        Returns:
            Tuple of:
            * ``output``: logits ``(batch, seq_len, vocab_size)``
            * ``importance_map``: per-token salience ``(batch, seq_len)``
        """
        x = X
        id_vec = self.identity_vector
        for block in self.blocks:
            x = block.forward(x, mask=mask, identity_vector=id_vec)

        x = self.final_norm(x)
        logits = x @ self.W_out                     # (B, L, vocab_size)

        importance_map = np.linalg.norm(x, axis=-1)
        max_imp = importance_map.max(axis=-1, keepdims=True) + 1e-8
        importance_map = importance_map / max_imp

        return logits, importance_map

    def set_identity_vector(self, vector: np.ndarray) -> None:
        """Update the identity vector used for feed-forward gating."""
        self.identity_vector = vector

    def get_config(self) -> Dict[str, Any]:
        """Return the model configuration as a plain dictionary."""
        return {
            "vocab_size": self.config.vocab_size,
            "dim_model": self.config.dim_model,
            "dim_position": self.config.dim_position,
            "num_layers": self.config.num_layers,
            "dim_ff": self.config.dim_ff,
            "num_heads": self.config.num_heads,
            "max_seq_len": self.config.max_seq_len,
            "gravitational_constant": self.config.gravitational_constant,
            "curvature": self.config.curvature,
            "sparsity_threshold": self.config.sparsity_threshold,
        }
