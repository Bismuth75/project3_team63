from dataclasses import dataclass, field
import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
G = 9.81
RHO_WATER = 1000.0
J_PER_KWH = 3.6e6
SECONDS_PER_DAY = 86_400
TARGET_OUTPUT_GAL = 100_000 #gal/day

galPerm3 = 264.172

TARGET_OUTPUT_M = 0.0043812636 #m^3/s


# ---------------------------------------------------------------------------
# Unit operations: fermenter, distiller, filter, dehydrator
# (all priced as $ per m^3/s of INLET flow, plus a fixed kWh/day draw)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class UnitOp:
    kind: str                 # "fermenter" | "distiller" | "filter" | "dehydrator"
    tier: str
    efficiency: float         # meaning depends on kind (see tables below)
    cost_per_flow: float      # $ per (m^3/s) of total inlet flow
    energy_kwh_per_day: float

    def capital_cost(self, inlet_flow_m3s: float) -> float:
        return self.cost_per_flow * inlet_flow_m3s

    def power_w(self) -> float:
        """Average electrical power draw in watts."""
        return self.energy_kwh_per_day * J_PER_KWH / SECONDS_PER_DAY

    def energy_j(self, days: float = 1.0) -> float:
        return self.energy_kwh_per_day * J_PER_KWH * days


# (tier, efficiency, $ per m^3/s, kWh/day)
_FERMENTER_TABLE = [   # efficiency = fraction of sugar converted
    ("Scrap",       0.50,   320_000, 46_600),
    ("Average",     0.75,   380_000, 47_200),
    ("Premium",     0.90,   460_000, 47_500),
    ("World-class", 0.95, 1_100_000, 48_000),
]
_DISTILLER_TABLE = [   # efficiency = fraction alcohol of exit stream
    ("Scrap",       0.810,   390_000, 47_004),
    ("Average",     0.900,   460_000, 47_812),
    ("Premium",     0.915,   560_000, 48_200),
    ("World-class", 0.980, 1_370_000, 49_500),
]
_MATERIAL_REMOVAL_TABLE = [  # efficiency = mass fraction of contaminant removed
    ("Scrap",       0.50, 200_000, 48_800),
    ("Average",     0.75, 240_000, 49_536),
    ("Premium",     0.90, 280_000, 50_350),
    ("World-class", 0.98, 480_000, 51_000),
]

FERMENTERS  = [UnitOp("fermenter",  *row) for row in _FERMENTER_TABLE]
DISTILLERS  = [UnitOp("distiller",  *row) for row in _DISTILLER_TABLE]
FILTERS     = [UnitOp("filter",     *row) for row in _MATERIAL_REMOVAL_TABLE]
DEHYDRATORS = [UnitOp("dehydrator", *row) for row in _MATERIAL_REMOVAL_TABLE]


# ---------------------------------------------------------------------------
# Pumps: price depends on (tier, effective performance height rating)
# ---------------------------------------------------------------------------
PUMP_TIERS = ["Cheap", "Value", "Standard", "High-Grade", "Premium"]
PUMP_EFFICIENCY = np.array([0.80, 0.83, 0.86, 0.89, 0.92])
PUMP_RATINGS_M = np.arange(6, 37, 3)          # 6, 9, ..., 36
# rows = height rating, cols = tier; $ per m^3/s
PUMP_COST = np.array([
    [200_000, 240_000, 280_000, 340_000,   415_000],  # 6 m
    [220_000, 260_000, 310_000, 380_000,   456_000],  # 9
    [240_000, 290_000, 340_000, 410_000,   502_000],  # 12
    [260_000, 310_000, 380_000, 460_000,   552_000],  # 15
    [290_000, 350_000, 420_000, 500_000,   607_000],  # 18
    [320_000, 380_000, 460_000, 550_000,   668_000],  # 21
    [350_000, 420_000, 510_000, 610_000,   735_000],  # 24
    [390_000, 460_000, 560_000, 670_000,   808_000],  # 27
    [420_000, 510_000, 610_000, 740_000,   889_000],  # 30
    [470_000, 560_000, 670_000, 810_000,   978_000],  # 33
    [510_000, 620_000, 740_000, 890_000, 1_076_000],  # 36
])


@dataclass(frozen=True)
class Pump:
    tier: str
    efficiency: float
    rating_m: float           # max total vertical lift this pump is rated for
    cost_per_flow: float      # $ per (m^3/s)

    def capital_cost(self, flow_m3s: float) -> float:
        return self.cost_per_flow * flow_m3s

    def power_w(self, flow_m3s: float, total_head_m: float, rho: float = RHO_WATER) -> float:
        """Electrical power: rho*g*Q*H / eta. total_head_m should include lift + losses."""
        return rho * G * flow_m3s * total_head_m / self.efficiency

    def can_lift(self, height_m: float) -> bool:
        return height_m <= self.rating_m


PUMPS = [
    Pump(tier, float(PUMP_EFFICIENCY[j]), float(PUMP_RATINGS_M[i]), float(PUMP_COST[i, j]))
    for i in range(len(PUMP_RATINGS_M))
    for j, tier in enumerate(PUMP_TIERS)
]


def pump_for_height(tier: str, height_m: float) -> Pump:
    """Smallest-rated pump of a given tier that covers the required vertical lift."""
    options = [p for p in PUMPS if p.tier == tier and p.can_lift(height_m)]
    if not options:
        raise ValueError(f"No {tier} pump is rated for {height_m} m (max {PUMP_RATINGS_M[-1]} m)")
    return min(options, key=lambda p: p.rating_m)


# ---------------------------------------------------------------------------
# Shared diameters for liquid pipe / bends / valves
# (a segment's pipe, bends and valves must all share one diameter)
# ---------------------------------------------------------------------------
LIQUID_DIAMETERS_M = np.array([0.10, 0.11, 0.12, 0.13, 0.14, 0.15])


def _velocity(flow_m3s: float, diameter_m: float) -> float:
    return flow_m3s / (np.pi * diameter_m**2 / 4)


# ---------------------------------------------------------------------------
# Pipe (liquid): price depends on (tier/friction factor, diameter)
# ---------------------------------------------------------------------------
PIPE_TIERS = ["Salvage", "Questionable", "Better", "Nice", "Outstanding", "Glorious"]
PIPE_FRICTION = np.array([0.05, 0.03, 0.02, 0.01, 0.005, 0.002])  # Darcy f
# rows = diameter, cols = tier; $ per m
PIPE_COST_PER_M = np.array([
    [ 1_000,  1_200,  1_440,  2_160,  2_700,  2_970],  # 0.10 m
    [ 1_200,  1_440,  1_720,  2_580,  3_230,  3_550],  # 0.11
    [ 2_570,  3_080,  3_700,  5_550,  6_940,  7_640],  # 0.12
    [ 6_300,  7_560,  9_070, 14_000, 17_000, 19_000],  # 0.13
    [14_000, 16_000, 20_000, 29_000, 37_000, 40_000],  # 0.14
    [26_000, 31_000, 37_000, 55_000, 69_000, 76_000],  # 0.15
])


@dataclass(frozen=True)
class Pipe:
    tier: str
    friction_factor: float
    diameter_m: float
    cost_per_m: float

    def capital_cost(self, length_m: float) -> float:
        return self.cost_per_m * length_m

    def velocity(self, flow_m3s: float) -> float:
        return _velocity(flow_m3s, self.diameter_m)

    def head_loss(self, flow_m3s: float, length_m: float) -> float:
        """Darcy-Weisbach major loss, in meters of head."""
        v = self.velocity(flow_m3s)
        return self.friction_factor * (length_m / self.diameter_m) * v**2 / (2 * G)


PIPES = [
    Pipe(tier, float(PIPE_FRICTION[j]), float(LIQUID_DIAMETERS_M[i]), float(PIPE_COST_PER_M[i, j]))
    for i in range(len(LIQUID_DIAMETERS_M))
    for j, tier in enumerate(PIPE_TIERS)
]


# ---------------------------------------------------------------------------
# Ductwork (gas removal only; no bends/valves needed)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Duct:
    diameter_m: float
    cost_per_m: float
    friction_factor: float = 0.002

    def capital_cost(self, length_m: float) -> float:
        return self.cost_per_m * length_m


DUCTS = [Duct(1.00, 228), Duct(1.25, 414), Duct(1.50, 700)]


# ---------------------------------------------------------------------------
# Bends: price depends on (angle, diameter)
# ---------------------------------------------------------------------------
BEND_ANGLES_DEG = np.array([20, 30, 45, 60, 75, 90])
BEND_LOSS_COEFF = np.array([0.10, 0.15, 0.20, 0.22, 0.27, 0.30])  # xi
# rows = diameter, cols = angle; $ per bend
BEND_COST = np.array([
    [  100,   105,   110,   116,   122,   128],  # 0.10 m
    [  149,   157,   164,   173,   181,   190],  # 0.11
    [  493,   517,   543,   570,   599,   700],  # 0.12
    [1_400, 1_500, 1_600, 1_600, 1_700, 1_800],  # 0.13
    [3_200, 3_400, 3_600, 3_800, 3_900, 4_100],  # 0.14
    [6_200, 6_500, 6_900, 7_200, 7_600, 8_000],  # 0.15
])


@dataclass(frozen=True)
class Bend:
    angle_deg: float
    loss_coeff: float
    diameter_m: float
    cost: float

    def head_loss(self, flow_m3s: float) -> float:
        """Minor loss xi * v^2 / 2g, in meters of head."""
        v = _velocity(flow_m3s, self.diameter_m)
        return self.loss_coeff * v**2 / (2 * G)


BENDS = [
    Bend(float(BEND_ANGLES_DEG[j]), float(BEND_LOSS_COEFF[j]),
         float(LIQUID_DIAMETERS_M[i]), float(BEND_COST[i, j]))
    for i in range(len(LIQUID_DIAMETERS_M))
    for j in range(len(BEND_ANGLES_DEG))
]


# ---------------------------------------------------------------------------
# Valves: price depends on (tier/flow coefficient, diameter)
# Only unit-operation inlets/outlets need valves; waste streams do not.
# ---------------------------------------------------------------------------
VALVE_TIERS = ["Salvage", "Questionable", "Outstanding", "Glorious"]
VALVE_FLOW_COEFF = np.array([800, 700, 600, 500])
# rows = diameter, cols = tier; $ per valve
VALVE_COST = np.array([
    [  100,   120,   270,   297],  # 0.10 m
    [  120,   144,   323,   355],  # 0.11
    [  257,   308,   694,   764],  # 0.12
    [  630,   756, 1_700, 1_900],  # 0.13
    [1_400, 1_600, 3_700, 4_000],  # 0.14
    [2_600, 3_100, 6_900, 7_600],  # 0.15
])


@dataclass(frozen=True)
class Valve:
    tier: str
    flow_coeff: float
    diameter_m: float
    cost: float

    def head_loss(self, flow_m3s: float) -> float:
        # TODO: fill in with the valve head-loss formula from the course slides.
        # The catalog only gives a flow coefficient, and the formula that converts
        # it to head loss depends on how your slides define it.
        raise NotImplementedError("Add the valve head-loss formula from the project slides")


VALVES = [
    Valve(tier, float(VALVE_FLOW_COEFF[j]), float(LIQUID_DIAMETERS_M[i]), float(VALVE_COST[i, j]))
    for i in range(len(LIQUID_DIAMETERS_M))
    for j, tier in enumerate(VALVE_TIERS)
]


# ---------------------------------------------------------------------------
# A pipe segment: one pipe + its bends + valves, all at one diameter
# ---------------------------------------------------------------------------
@dataclass
class PipeSegment:
    pipe: Pipe
    length_m: float
    bends: list = field(default_factory=list)
    valves: list = field(default_factory=list)

    def __post_init__(self):
        d = self.pipe.diameter_m
        for part in self.bends + self.valves:
            if not np.isclose(part.diameter_m, d):
                raise ValueError(f"{part} diameter does not match pipe diameter {d} m")

    def capital_cost(self) -> float:
        return (self.pipe.capital_cost(self.length_m)
                + sum(b.cost for b in self.bends)
                + sum(v.cost for v in self.valves))

    def head_loss(self, flow_m3s: float) -> float:
        return (self.pipe.head_loss(flow_m3s, self.length_m)
                + sum(b.head_loss(flow_m3s) for b in self.bends)
                + sum(v.head_loss(flow_m3s) for v in self.valves))


# ---------------------------------------------------------------------------
# Convenience lookups
# ---------------------------------------------------------------------------
def by_tier(parts, tier):
    return [p for p in parts if p.tier == tier]


def by_diameter(parts, diameter_m):
    return [p for p in parts if np.isclose(p.diameter_m, diameter_m)]


def find_bend(angle_deg: float, diameter_m: float) -> Bend:
    return next(b for b in BENDS if b.angle_deg == angle_deg and np.isclose(b.diameter_m, diameter_m))


# Sanity checks so a typo in a table is caught immediately
assert PUMP_COST.shape == (len(PUMP_RATINGS_M), len(PUMP_TIERS))
assert PIPE_COST_PER_M.shape == (len(LIQUID_DIAMETERS_M), len(PIPE_TIERS))
assert BEND_COST.shape == (len(LIQUID_DIAMETERS_M), len(BEND_ANGLES_DEG))
assert VALVE_COST.shape == (len(LIQUID_DIAMETERS_M), len(VALVE_TIERS))


if __name__ == "__main__":
    print(TARGET_OUTPUT_M)
    print(TARGET_OUTPUT_GAL / galPerm3 / SECONDS_PER_DAY)
    print(f"Error = {TARGET_OUTPUT_GAL / galPerm3 / SECONDS_PER_DAY - TARGET_OUTPUT_M}")