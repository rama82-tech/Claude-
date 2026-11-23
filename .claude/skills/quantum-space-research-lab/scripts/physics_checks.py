"""Reusable physics / QA assertions for quantum and space simulations.

Import from tests:
    import sys; sys.path.insert(0, "<skill>/scripts")
    from physics_checks import *
or copy the functions you need into tests/physics_checks.py.

Every function raises AssertionError with a readable message on failure.
"""
from __future__ import annotations

import numpy as np

__all__ = [
    "assert_normalized",
    "assert_probabilities",
    "assert_unitary",
    "assert_valid_density_matrix",
    "assert_conserved",
    "assert_monotonic",
    "assert_no_fabricated_fallback",
    "specific_orbital_energy",
    "specific_angular_momentum",
]


def assert_normalized(psi, atol: float = 1e-10) -> None:
    """State vector has unit L2 norm."""
    psi = np.asarray(psi, dtype=complex).ravel()
    n = np.linalg.norm(psi)
    assert abs(n - 1.0) <= atol, f"state norm = {n!r}, expected 1 (atol={atol})"


def assert_probabilities(p, atol: float = 1e-10) -> None:
    """Probabilities are real, non-negative and sum to 1."""
    p = np.asarray(p)
    assert np.all(np.abs(np.imag(p)) <= atol), "probabilities have imaginary parts"
    p = np.real(p)
    assert np.all(p >= -atol), f"negative probability: min={p.min()!r}"
    s = p.sum()
    assert abs(s - 1.0) <= atol, f"probabilities sum to {s!r}, expected 1 (atol={atol})"


def assert_unitary(U, atol: float = 1e-10) -> None:
    """U^dagger U = I."""
    U = np.asarray(U, dtype=complex)
    assert U.ndim == 2 and U.shape[0] == U.shape[1], f"not square: {U.shape}"
    err = np.max(np.abs(U.conj().T @ U - np.eye(U.shape[0])))
    assert err <= atol, f"not unitary: max|U†U - I| = {err!r}"


def assert_valid_density_matrix(rho, atol: float = 1e-10) -> None:
    """Hermitian, trace 1, positive semidefinite."""
    rho = np.asarray(rho, dtype=complex)
    herm = np.max(np.abs(rho - rho.conj().T))
    assert herm <= atol, f"not Hermitian: max|rho - rho†| = {herm!r}"
    tr = np.trace(rho).real
    assert abs(tr - 1.0) <= atol, f"trace = {tr!r}, expected 1"
    eig = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
    assert eig.min() >= -atol, f"not PSD: min eigenvalue = {eig.min()!r}"


def assert_conserved(series, rtol: float = 1e-6, name: str = "quantity") -> None:
    """Max relative drift of a scalar or vector time series from its initial value <= rtol."""
    s = np.asarray(series, dtype=float)
    s0 = s[0]
    scale = np.linalg.norm(s0) if s.ndim > 1 else abs(s0)
    assert scale > 0, f"{name}: initial value is zero; use an absolute check instead"
    drift = np.max(np.linalg.norm(s - s0, axis=-1) if s.ndim > 1 else np.abs(s - s0)) / scale
    assert drift <= rtol, f"{name} not conserved: relative drift {drift:.3e} > {rtol:.1e}"


def assert_monotonic(series, decreasing: bool = True, atol: float = 0.0, name: str = "quantity") -> None:
    """For dissipative systems (e.g. drag): quantity never increases (or decreases)."""
    d = np.diff(np.asarray(series, dtype=float))
    if decreasing:
        assert np.all(d <= atol), f"{name} increased by up to {d.max():.3e}"
    else:
        assert np.all(d >= -atol), f"{name} decreased by up to {(-d).max():.3e}"


def assert_no_fabricated_fallback(data, min_rows: int = 1, max_constant_fraction: float = 0.95) -> None:
    """Heuristic guard that loaded 'real' data isn't empty, all-NaN, or a constant placeholder.

    Works on pandas DataFrames/Series or array-likes. This is a safety net,
    not proof of provenance — also review the loader code for silent fallbacks.
    """
    arr = np.asarray(getattr(data, "values", data), dtype=float)
    assert arr.size >= min_rows, f"loaded data has {arr.size} values (< {min_rows})"
    finite = arr[np.isfinite(arr)]
    assert finite.size > 0, "loaded data is entirely NaN/inf"
    _, counts = np.unique(finite, return_counts=True)
    frac = counts.max() / finite.size
    assert frac <= max_constant_fraction, (
        f"{frac:.0%} of values are identical — looks like placeholder/fill data"
    )


def specific_orbital_energy(r, v, mu: float) -> np.ndarray:
    """epsilon = v^2/2 - mu/|r|  (SI: r in m, v in m/s, mu in m^3/s^2). r, v shape (N, 3)."""
    r = np.atleast_2d(r)
    v = np.atleast_2d(v)
    return 0.5 * np.sum(v * v, axis=1) - mu / np.linalg.norm(r, axis=1)


def specific_angular_momentum(r, v) -> np.ndarray:
    """h = r x v, shape (N, 3)."""
    return np.cross(np.atleast_2d(r), np.atleast_2d(v))


if __name__ == "__main__":  # quick self-test
    bell = np.array([1, 0, 0, 1]) / np.sqrt(2)
    assert_normalized(bell)
    assert_probabilities(np.abs(bell) ** 2)
    assert_valid_density_matrix(np.outer(bell, bell.conj()))
    H = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
    assert_unitary(H)
    assert_conserved([1.0, 1.0 + 1e-9, 1.0 - 1e-9])
    assert_monotonic([3, 2, 2, 1])
    try:
        assert_no_fabricated_fallback(np.full(100, -999.0))
        raise SystemExit("fallback guard failed to fire")
    except AssertionError:
        pass
    print("physics_checks self-test OK")
