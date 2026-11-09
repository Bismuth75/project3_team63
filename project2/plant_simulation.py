from catalog import DIAMETERS
from catalog import FERMENTERS, FILTERS, DISTILLERS, DEHYDRATORS
from catalog import PIPE_COST_PER_M, PIPE_FRICTION
from catalog import BEND_COST, ANGLE_TO_LOSS
from catalog import VALVE_COST,VALVE_FLOW_COEFF
from catalog import RHO_ETH, RHO_FIBER, RHO_SUGAR, RHO_WATER, GAL_TO_M3, J_PER_GAL_ETH
from catalog import PUMP_COST, PUMP_EFFICIENCY, PUMP_RATINGS
from itertools import product
import numpy as np
import matplotlib.pyplot as plt
import math, ast

G = 9.81
# waste parameters
WASTE_EXIT_HEIGHT = 1.0 #waste pipes flow this height
CO2_DUCT_M = 0.25 #alloted length for CO2 ductwork leaving the side of building
DUCT_COST_PER_M = 228 # 1.0m diameter duct (cheapest bc waste doesn't need factor into energy)
WASTE_DIAMETER = 0.10
WASTE_PIPE_Q = 0 #

def eth_percentage_mass_req(eta_fer, eta_fil, eta_dis, eta_deh, waste_mass = 1):
    sugar0 = 0.2 * waste_mass
    water0 = 0.6 * waste_mass
    fiber0 = 0.2 * waste_mass
    
    rho_sugar = 1599
    rho_water = 997
    rho_fiber = 1311
    rho_eth = 789
    # eth1 = 0.51 * eta_fer * sugar0
    # sugar1 = (1 - eta_fer) *  sugar0
    # water1 = water0
    # fiber1 = fiber0
    # CO2out1 = 0.49 * eta_fer * sugar0
    
    # eth2 = eth1
    # sugar2 = sugar1
    # water2 = water1
    # fiber2 = fiber1 * (1 - eta_fil)
    # fiber2out = fiber1 * eta_fil
    
    # k3 = (eth2 * (1/eta_dis - 1)) / (sugar2 + water2 + fiber2)
    k_3 = (0.51 * eta_fer * sugar0 * (1/eta_dis - 1)) / ((1 - eta_fer) * sugar0 + water0 + fiber0 * (1 - eta_fil))
    # eth3 = eth2
    # sugar3 = sugar2 * k3
    # water3 = water2 * k3
    # fiber3 = fiber2 * k3
    
    # eth4 = eth3
    # sugar4 = sugar3
    # water4 = water3 * (1 - eta_deh)
    # fiber4 = fiber3
    # water4out = water3 * eta_deh
    
    eth_final = 0.51 * eta_fer * sugar0
    sugar_final = (1 - eta_fer) * sugar0 * k_3
    water_final = water0 * k_3 * (1 - eta_deh)
    fiber_final = fiber0 * (1 - eta_fil) * k_3
    
    mass_final = eth_final + sugar_final + water_final + fiber_final
    
    eth_percent = eth_final / mass_final
    
    rho_final = (eth_final * rho_eth + sugar_final * rho_sugar + water_final * rho_water + fiber_final * rho_fiber) / mass_final
    
    m3_final = mass_final / rho_final
    
    gal_final = m3_final * 264.172
    
    # print(f"Ethanol Mass: {eth_final}")
    # print(f"Sugar Mass: {sugar_final}")
    # print(f"Water Mass: {water_final}")
    # print(f"Fiber Mass: {fiber_final}")
    # print(f"Ethanol Percentage: {eth_percent}")
    # print(f"Final Volume (gal) {gal_final}")
    return (eth_percent, 100000 / 86400 / gal_final)

def density(sugar, water, fiber, eth):
    """Mass-weighted average density (course method)."""
    total = sugar + water + fiber + eth
    return (sugar * RHO_SUGAR + water * RHO_WATER + fiber * RHO_FIBER + eth * RHO_ETH) / total

def vol_flow(sugar, water, fiber, eth):
    """Volumetric flow (m^3/s) from mass flows (kg/s). Same as volume if inputs are kg."""
    total = sugar + water + fiber + eth
    return total / density(sugar, water, fiber, eth)

def fermenter(input_mass, eta_fer):
    sugar = 0.2 * input_mass
    water = 0.6 * input_mass
    fiber = 0.2 * input_mass
    converted = eta_fer * sugar
    sugar_out = sugar - converted
    eth_out = 0.51 * converted
    #co2_out = 0.49 * converted
    return sugar_out, water, fiber, eth_out

def filt(sugar, water, fiber, eth, eta_fil):
    fiber_out = fiber * (1 - eta_fil)
    return sugar, water, fiber_out, eth

def distiller(sugar, water, fiber, eth, eta_dis):
    # Keep all ethanol; scale everything else by k so eth / total = eta_dis
    k = eth * (1 / eta_dis - 1) / (sugar + water + fiber)
    k = min(k, 1)    # can't add impurities if the stream is already purer than eta_dis
    sugar_out, water_out, fiber_out = sugar * k, water * k, fiber * k
    return sugar_out, water_out, fiber_out, eth

def dehydrator(sugar, water, fiber, eth, eta_deh):
    water_out = water * (1 - eta_deh)
    return sugar, water_out, fiber, eth

def capital_cost(option):
    fermented = fermenter(option[4], FERMENTERS[option[0]][0])
    cost = vol_flow(option[4]*0.2,option[4]*0.6,option[4]*0.2,0) * FERMENTERS[option[0]][1]
    filtered = filt(*fermented, FILTERS[option[1]][0])
    cost += vol_flow(*fermented) * FILTERS[option[1]][1]
    distilled = distiller(*filtered, DISTILLERS[option[2]][0])
    cost+= vol_flow(*filtered) * DISTILLERS[option[2]][1]
    cost+= vol_flow(*distilled) * DEHYDRATORS[option[3]][1]
    return cost

def flows(option):
    feed = (option[4]*0.2, option[4]*0.6, option[4]*0.2, 0)
    fermented = fermenter(option[4], FERMENTERS[option[0]][0])
    filtered = filt(*fermented, FILTERS[option[1]][0])
    distilled = distiller(*filtered, DISTILLERS[option[2]][0])
    dehydrated = dehydrator(*distilled, DEHYDRATORS[option[3]][0])
    return [(vol_flow(*row), density(*row)) for row in (feed, fermented, filtered, distilled, dehydrated)]

def pipe_loss(friction, flow, diameter, length):
    return friction * 8 /(math.pi**2 * 9.81) * flow**2 * length / diameter**5

def attachment_loss(loss, flow, diameter):
    return loss * (flow / (math.pi * diameter**2 / 4))**2 / 2 / 9.81

def segment_loss(segment, stage, option, diameter, qualities):
    flow, rho = flows(option)[stage]
    return segment_head(segment, flow, diameter, qualities)

def segment_head(segment, flow, diameter, qualities):
    head = 0
    for i, part in enumerate(segment):
        match part[0]:
            case 0:   # valve
                K = VALVE_FLOW_COEFF[qualities[i]]
                head += attachment_loss(K, flow, diameter)
            case 1:   # pipe
                f = PIPE_FRICTION[qualities[i]]
                head += pipe_loss(f, flow, diameter, part[1])
            case 2:   # bend
                xi = ANGLE_TO_LOSS[part[1]]
                head += attachment_loss(xi, flow, diameter)
    return head

def segment_cost(segment, diameter, qualities):
    cost = 0
    for i, part in enumerate(segment):
        match part[0]:
            case 0:
                cost += part_cost(0, diameter, qualities[i])
            case 1:
                cost += part_cost(1, diameter, qualities[i], length=part[1])
            case 2:
                cost += part_cost(2, diameter, 0, angle=part[1])
    return cost

def part_cost(kind, diameter, quality, length = 0, angle = 90):
    row = DIAMETERS.index(diameter)
    match kind:
        case 0:
            cost = VALVE_COST[row, quality]
        case 1:
            cost = PIPE_COST_PER_M[row, quality] * length
        case 2:
            cost = BEND_COST[row, list(ANGLE_TO_LOSS).index(angle)]
    return cost

def energy_efficiency(option, segments, pump_eff):
    stage_flows = flows(option)          # [(Q, rho), ...] for stages 0-4
    # Lift + losses in every segment: head (m) -> power (W)
    # A downhill drop (dz < 0) pays for that segment's own losses, but any leftover
    # can't flow back to the pump, so a segment never contributes less than zero
    segment_power = 0
    for segment, stage, diameter, qualities, dz in segments:
        flow, rho = stage_flows[stage]
        head = segment_loss(segment, stage, option, diameter, qualities)
        segment_power += rho * G * flow * max(0, dz + head)
    # Kinetic energy of the feed and product is left out: it's ~0.1 kW vs ~8,000 kW total
    pump_power = segment_power / pump_eff
    # Unit operations: kWh/day -> W
    i, j, k, l, feed = option
    unit_kwh_day = FERMENTERS[i][2] + FILTERS[j][2] + DISTILLERS[k][2] + DEHYDRATORS[l][2]
    unit_power = unit_kwh_day * 3_600_000 / 86_400
    # Usable energy out: product volume flow -> gal/s -> W
    q_out, rho_out = stage_flows[4]
    usable_power = q_out / GAL_TO_M3 * J_PER_GAL_ETH    
    return usable_power / (pump_power + unit_power)

def waste_cost(waste_segments):
    cost = CO2_DUCT_M * DUCT_COST_PER_M
    for segment in waste_segments:
        qualities = [WASTE_PIPE_Q if p[0] == 1 else None for p in segment]
        cost += segment_cost(segment, WASTE_DIAMETER, qualities)
    return float(cost)

def system_cost(option, segments, pump, waste_segments):
    stage_flows = flows(option)
    # unit ops
    unit_cost = capital_cost(option) + waste_cost(waste_segments)
    # pipe cost
    piping_cost = 0
    for segment, stage, diameter, qualities, dz in segments:
        piping_cost += segment_cost(segment, diameter, qualities)
    # pump cost
    rating, tier = pump
    q_feed, rho_feed = stage_flows[0]
    pump_cost = PUMP_COST[rating, tier] * q_feed
    return unit_cost + piping_cost + pump_cost

def keep_best(items):
    #remove strictly worse items
    front = []
    best_loss = float("inf")
    for item in sorted(items, key=lambda x: (x[0], x[1])):
        if item[1] < best_loss:
            front.append(item)
            best_loss = item[1]
    return front

def segment_choices(segment, flow, rho, dz):
    choices = []
    for d, pipe_q, valve_q in product(DIAMETERS, range(len(PIPE_FRICTION)), range(len(VALVE_FLOW_COEFF))):
        qualities = [valve_q if p[0] == 0 else pipe_q if p[0] == 1 else None for p in segment]
        cost = segment_cost(segment, d, qualities)
        head = segment_head(segment, flow, d, qualities)
        power = rho * G * flow * max(0, dz + head)    # lift + losses, gravity can offset losses
        choices.append((cost, power, (d, pipe_q, valve_q)))
    return keep_best(choices)

def find_optimal(layout, waste_segments):
    fixed_waste_cost = waste_cost(waste_segments)
    #read segments to find optimal pump lift
    height = 0
    max_height = 0
    for segment, stage, dz in layout:
        height += dz
        max_height = max(max_height, height)
    rating = next(i for i, r in enumerate(PUMP_RATINGS) if r >= max_height)
    
    #computes stuff about a unit op combo once
    results = []
    for option in options:
        stage_flows = flows(option)
        i, j, k, l, feed = option
        unit_cost = capital_cost(option) + fixed_waste_cost
        unit_kwh_day = FERMENTERS[i][2] + FILTERS[j][2] + DISTILLERS[k][2] + DEHYDRATORS[l][2]
        unit_power = unit_kwh_day * 3_600_000 / 86_400
        usable_power = stage_flows[4][0] / GAL_TO_M3 * J_PER_GAL_ETH
        q_feed = stage_flows[0][0]
        #pipe/pump choices (each segment's power already includes its lift)
        per_segment = [segment_choices(seg, *stage_flows[st], dz) for seg, st, dz in layout]
        #merge segments one at a time, dropping dominated combos after each merge
        #(trying every combo at once runs out of memory with many segments)
        piping = [(0, 0, ())]
        for choices in per_segment:
            piping = keep_best([(c1 + c2, p1 + p2, d1 + (d2,))
                                for c1, p1, d1 in piping
                                for c2, p2, d2 in choices])
        option_results = []
        for piping_cost, segment_power, pipe_choices in piping:
            for tier, eta_p in enumerate(PUMP_EFFICIENCY):
                pump_power = segment_power / eta_p
                efficiency = usable_power / (pump_power + unit_power)
                cost = float(unit_cost + piping_cost + PUMP_COST[rating, tier] * q_feed)
                design = (option, pipe_choices, (rating, tier))
                option_results.append((cost, -efficiency, design))
        
        results.extend(keep_best(option_results))
    #neg efficiency because keep_best assumes lower is better for both
    return [(-neg_eff, cost, design) for cost, neg_eff, design in keep_best(results)]

options = []

for fer in FERMENTERS:
    for fil in FILTERS:
        for dis in DISTILLERS:
            for deh in DEHYDRATORS:
                result = eth_percentage_mass_req(fer[0], fil[0], dis[0], deh[0])
                if result[0] >= 0.98:
                    options.append((FERMENTERS.index(fer),FILTERS.index(fil),DISTILLERS.index(dis),DEHYDRATORS.index(deh),result[1]))

#0 = valve
#1 = pipe
#2 = bend

pipe_segment_0 = ((1, 0.25), (0,))          # pump -> fermenter inlet valve
pipe_segment_1 = ((0,) , (1,9.75), (0,))
pipe_segment_2 = ((0,) , (1, 3.35), (0,))
pipe_segment_3 = ((0,) , (1, 3.35), (2, 90), (1, 1.5), (0,))
pipe_segment_4 = ((0,), (1, 0.25))          # dehydrator outlet valve -> product out

layout = [
    (pipe_segment_0, 0, 0),
    (pipe_segment_1, 1, +9.75),
    (pipe_segment_2, 2, -3.35),
    (pipe_segment_3, 3, -3.35),
    (pipe_segment_4, 4, 0),
]

FILTER_WASTE_OUTLET = 10.75       # m above ground
DISTILLER_WASTE_OUTLET = 7.40
DEHYDRATOR_WASTE_OUTLET = 4.05

waste_fiber      = ((2, 90), (1, FILTER_WASTE_OUTLET - WASTE_EXIT_HEIGHT))
waste_distiller  = ((2, 90), (1, DISTILLER_WASTE_OUTLET - WASTE_EXIT_HEIGHT))
waste_dehydrator = ((2, 90), (1, DEHYDRATOR_WASTE_OUTLET - WASTE_EXIT_HEIGHT))

waste_segments = [waste_fiber, waste_distiller, waste_dehydrator]

#Description of 1 item in full_designs
#(Efficiency, Cost, ((Fermenter, Filter, Distiller, Dehydrator, Feed (kg/s)), ((diameter, pipe_q, valve_q) for each segment), (pump_lift, pump_q)))

recalc = False

if recalc == True:
    full_designs = find_optimal(layout, waste_segments)
    with open("full_designs.txt", "w") as f:
        for item in full_designs:
            f.write(repr(item) + "\n")
else:
    with open("full_designs.txt", 'r') as f:
         full_designs = [ast.literal_eval(line) for line in f if line.strip()]

# for eff, cost, design in full_designs:
#     print(f"{cost}\t{eff}")

effs = [design[0] for design in full_designs]
costs = [design[1] for design in full_designs]

plt.plot(costs, effs)
plt.xscale("log")
plt.xlabel("Total Capital Cost ($)")
plt.ylabel("Energy Efficiency (usable energy out / energy in)")
plt.title("Cost vs. Efficiency")
plt.grid(True, which="both", alpha=0.3)
plt.show()

# normalize axes and find the "knee", point where the curve is starting to flatten out
effs_array = np.array([eff for eff, cost, design in full_designs])
costs_array = np.array([cost for eff, cost, design in full_designs])
x_norm = (costs_array - costs_array.min()) / (costs_array.max() - costs_array.min())
y_norm = (effs_array - effs_array.min()) / (effs_array.max() - effs_array.min())

diff = y_norm - x_norm
knee_index = np.argmax(diff)
knee = full_designs[knee_index]
print(knee)
print(capital_cost(knee[2][0]))