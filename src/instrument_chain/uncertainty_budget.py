"""uncertainty-budget-v1 — GUM LPU and JCGM 101 Monte Carlo as a declared record.

Traceability is a declared string. Default is none_claimed.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence

SCHEMA = "uncertainty-budget-v1"


class Dist(str, Enum):
    NORMAL = "normal"
    RECTANGULAR = "rectangular"
    TRIANGULAR = "triangular"
    U_SHAPED = "u_shaped"


_DIVISOR: dict[Dist, float] = {
    Dist.RECTANGULAR: math.sqrt(3.0),
    Dist.TRIANGULAR: math.sqrt(6.0),
    Dist.U_SHAPED: math.sqrt(2.0),
}

_T_TABLE: dict[float, dict[int, float]] = {
    0.95: {
        1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
        8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160,
        14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093,
        20: 2.086, 21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060,
        26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045, 30: 2.042, 40: 2.021,
        50: 2.009, 60: 2.000, 100: 1.984,
    },
    0.99: {
        1: 63.657, 2: 9.925, 3: 5.841, 4: 4.604, 5: 4.032, 6: 3.707, 7: 3.499,
        8: 3.355, 9: 3.250, 10: 3.169, 12: 3.055, 15: 2.947, 20: 2.845,
        25: 2.787, 30: 2.750, 40: 2.704, 50: 2.678, 60: 2.660, 100: 2.626,
    },
}
_T_INF: dict[float, float] = {0.95: 1.960, 0.99: 2.576}


def coverage_factor(dof: float, p: float = 0.95) -> float:
    if p not in _T_TABLE:
        raise ValueError(f"no t-table for p={p}; declared levels are {sorted(_T_TABLE)}")
    if dof <= 0:
        raise ValueError("effective degrees of freedom must be positive")
    table = _T_TABLE[p]
    t_inf = _T_INF[p]
    keys = sorted(table)
    if math.isinf(dof) or dof > keys[-1]:
        if math.isinf(dof):
            return t_inf
        lo = keys[-1]
        w = (1.0 / dof) / (1.0 / lo)
        return t_inf + w * (table[lo] - t_inf)
    if dof <= keys[0]:
        return table[keys[0]]
    hi = min(k for k in keys if k >= dof)
    if hi == dof:
        return table[int(dof)] if int(dof) in table else table[hi]
    lo = max(k for k in keys if k < dof)
    w = (1.0 / dof - 1.0 / hi) / (1.0 / lo - 1.0 / hi)
    return table[hi] + w * (table[lo] - table[hi])


@dataclass(frozen=True)
class TypeA:
    source: str
    s: float
    n: int
    statistic: str
    c: float = 1.0
    unit: str = ""

    def __post_init__(self) -> None:
        if self.n < 2:
            raise ValueError(f"{self.source}: Type A needs n >= 2, got {self.n}")
        if self.s < 0:
            raise ValueError(f"{self.source}: standard deviation must be non-negative")
        if self.statistic not in ("mean", "single"):
            raise ValueError(
                f"{self.source}: statistic must be declared as 'mean' or 'single'"
            )

    @property
    def u(self) -> float:
        return self.s / math.sqrt(self.n) if self.statistic == "mean" else self.s

    @property
    def dof(self) -> float:
        return float(self.n - 1)

    @property
    def contribution(self) -> float:
        return abs(self.c) * self.u

    def to_dict(self) -> dict:
        return {
            "type": "A",
            "source": self.source,
            "s": self.s,
            "n": self.n,
            "statistic": self.statistic,
            "c": self.c,
            "unit": self.unit,
            "u": self.u,
            "dof": self.dof,
        }


@dataclass(frozen=True)
class TypeB:
    source: str
    dist: Dist
    half_width: float | None = None
    std: float | None = None
    k: float = 1.0
    dof: float = math.inf
    c: float = 1.0
    unit: str = ""

    def __post_init__(self) -> None:
        d = Dist(self.dist)
        if d is Dist.NORMAL:
            if self.std is None:
                raise ValueError(f"{self.source}: normal component needs std")
            if self.k <= 0:
                raise ValueError(f"{self.source}: divisor k must be positive")
        else:
            if self.half_width is None:
                raise ValueError(f"{self.source}: {d.value} component needs half_width")
            if self.half_width < 0:
                raise ValueError(f"{self.source}: half_width must be non-negative")

    @property
    def u(self) -> float:
        d = Dist(self.dist)
        if d is Dist.NORMAL:
            return float(self.std) / self.k
        return float(self.half_width) / _DIVISOR[d]

    @property
    def contribution(self) -> float:
        return abs(self.c) * self.u

    def to_dict(self) -> dict:
        return {
            "type": "B",
            "source": self.source,
            "dist": Dist(self.dist).value,
            "half_width": self.half_width,
            "std": self.std,
            "k": self.k,
            "dof": None if math.isinf(self.dof) else self.dof,
            "c": self.c,
            "unit": self.unit,
            "u": self.u,
        }


Component = TypeA | TypeB


@dataclass
class Budget:
    measurand: str
    components: list[Component] = field(default_factory=list)
    correlations: dict[tuple[str, str], float] = field(default_factory=dict)
    traceability: str = "none_claimed"
    unit: str = ""

    def __post_init__(self) -> None:
        names = [c.source for c in self.components]
        dupes = {n for n in names if names.count(n) > 1}
        if dupes:
            raise ValueError(f"duplicate component sources: {sorted(dupes)}")
        for a, b in self.correlations:
            if a not in names or b not in names:
                raise ValueError(f"correlation names ({a}, {b}) for unknown components")

    def _r(self, a: str, b: str) -> float:
        if a == b:
            return 1.0
        return self.correlations.get((a, b), self.correlations.get((b, a), 0.0))

    @property
    def uncorrelated(self) -> bool:
        return not any(v != 0.0 for v in self.correlations.values())

    def u_c(self) -> float:
        if not self.components:
            raise ValueError("empty budget: nothing declared, so nothing is reported")
        var = 0.0
        for i in self.components:
            for j in self.components:
                var += (i.c * i.u) * (j.c * j.u) * self._r(i.source, j.source)
        return math.sqrt(max(var, 0.0))

    def dof_eff(self) -> float:
        if not self.uncorrelated:
            raise ValueError(
                "Welch-Satterthwaite is declared only for uncorrelated components; "
                "this budget declares correlations"
            )
        uc = self.u_c()
        if uc == 0.0:
            return math.inf
        denom = 0.0
        for comp in self.components:
            nu = comp.dof
            if math.isinf(nu):
                continue
            denom += (comp.c * comp.u) ** 4 / nu
        return math.inf if denom == 0.0 else uc**4 / denom

    def k(self, p: float = 0.95) -> float:
        return coverage_factor(self.dof_eff(), p)

    def U(self, p: float = 0.95) -> float:
        return self.k(p) * self.u_c()

    def contributions(self) -> list[dict]:
        uc2 = self.u_c() ** 2
        rows = []
        for comp in self.components:
            ci = comp.c * comp.u
            rows.append(
                {
                    "source": comp.source,
                    "u_i": comp.u,
                    "c_i": comp.c,
                    "c_i_u_i": ci,
                    "variance_share": (ci**2 / uc2) if uc2 > 0 else 0.0,
                }
            )
        rows.sort(key=lambda r: abs(r["c_i_u_i"]), reverse=True)
        return rows

    def monte_carlo(self, n_draws: int = 200_000, seed: int = 0, p: float = 0.95) -> dict:
        import numpy as np

        rng = np.random.default_rng(seed)
        if not self.uncorrelated:
            raise ValueError("Monte Carlo path is declared for uncorrelated components only")
        y = np.zeros(n_draws)
        for comp in self.components:
            if isinstance(comp, TypeA):
                x = comp.u * rng.standard_t(comp.dof, n_draws)
            else:
                d = Dist(comp.dist)
                if d is Dist.NORMAL:
                    x = rng.normal(0.0, comp.u, n_draws)
                elif d is Dist.RECTANGULAR:
                    a = float(comp.half_width)
                    x = rng.uniform(-a, a, n_draws)
                elif d is Dist.TRIANGULAR:
                    a = float(comp.half_width)
                    x = rng.triangular(-a, 0.0, a, n_draws)
                else:
                    a = float(comp.half_width)
                    x = a * np.cos(rng.uniform(0.0, 2.0 * math.pi, n_draws))
            y += comp.c * x
        ys = np.sort(y)
        m = int(round(p * n_draws))
        widths = ys[m:] - ys[: n_draws - m]
        lo = int(np.argmin(widths))
        return {
            "n_draws": n_draws,
            "seed": seed,
            "p": p,
            "u_c": float(np.std(y, ddof=1)),
            "interval_low": float(ys[lo]),
            "interval_high": float(ys[lo + m]),
        }

    def to_record(self, p: float = 0.95) -> dict:
        nu = self.dof_eff() if self.uncorrelated else None
        return {
            "schema": SCHEMA,
            "measurand": self.measurand,
            "unit": self.unit,
            "components": [c.to_dict() for c in self.components],
            "correlations": [
                {"a": a, "b": b, "r": r} for (a, b), r in self.correlations.items()
            ],
            "combination": "gum_lpu" if self.uncorrelated else "gum_lpu_correlated",
            "u_c": self.u_c(),
            "dof_eff": None if (nu is None or math.isinf(nu)) else nu,
            "p": p,
            "k": self.k(p) if self.uncorrelated else None,
            "U": self.U(p) if self.uncorrelated else None,
            "contributions": self.contributions(),
            "traceability": self.traceability,
        }

    def to_json(self, p: float = 0.95, **kw) -> str:
        return json.dumps(self.to_record(p), **kw)


def from_record(rec: dict) -> Budget:
    if rec.get("schema") != SCHEMA:
        raise ValueError(f"expected schema {SCHEMA}, got {rec.get('schema')!r}")
    comps: list[Component] = []
    for c in rec["components"]:
        if c["type"] == "A":
            comps.append(
                TypeA(
                    source=c["source"],
                    s=c["s"],
                    n=c["n"],
                    statistic=c["statistic"],
                    c=c["c"],
                    unit=c.get("unit", ""),
                )
            )
        else:
            comps.append(
                TypeB(
                    source=c["source"],
                    dist=Dist(c["dist"]),
                    half_width=c.get("half_width"),
                    std=c.get("std"),
                    k=c.get("k", 1.0),
                    dof=math.inf if c.get("dof") is None else float(c["dof"]),
                    c=c["c"],
                    unit=c.get("unit", ""),
                )
            )
    corr = {(d["a"], d["b"]): d["r"] for d in rec.get("correlations", [])}
    return Budget(
        measurand=rec["measurand"],
        components=comps,
        correlations=corr,
        traceability=rec.get("traceability", "none_claimed"),
        unit=rec.get("unit", ""),
    )
