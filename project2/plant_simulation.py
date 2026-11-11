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
import math, ast, time

G = 9.81
# waste parameters
WASTE_EXIT_HEIGHT = 1.0 #waste pipes flow this height
CO2_DUCT_M = 0.25 #alloted length for CO2 ductwork leaving the side of building
DUCT_COST_PER_M = 228 # 1.0m diameter duct (cheapest bc waste doesn't need factor into energy)
WASTE_DIAMETER = 0.10 #smallest diameter because the energy is already lost
WASTE_PIPE_Q = 0 #worst quality because the energy is already lost

def eth_percentage_mass_req(eta_fer, eta_fil, eta_dis, eta_deh, waste_mass = 1):
    """goes through stages one by one and computes the ethanol efficiency 
    and required input mass given a set of unit op efficiences"""
    
    #initial
    sugar0 = 0.2 * waste_mass
    water0 = 0.6 * waste_mass
    fiber0 = 0.2 * waste_mass
    #densities
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
    #calculates density of the stream at a certain point given the masses of the 4 components
    total = sugar + water + fiber + eth
    return (sugar * RHO_SUGAR + water * RHO_WATER + fiber * RHO_FIBER + eth * RHO_ETH) / total

def vol_flow(sugar, water, fiber, eth):
    #calculates the volumetric flow of the stream at a certain point given the mass flow rates
    total = sugar + water + fiber + eth
    return total / density(sugar, water, fiber, eth)

def fermenter(input_mass, eta_fer):
    #takes input mass, returns mass flow rates of the four components
    sugar = 0.2 * input_mass
    water = 0.6 * input_mass
    fiber = 0.2 * input_mass
    converted = eta_fer * sugar
    sugar_out = sugar - converted
    eth_out = 0.51 * converted
    #co2_out = 0.49 * converted
    return sugar_out, water, fiber, eth_out

def filt(sugar, water, fiber, eth, eta_fil):
    #returns the mass flow rates after being filtered
    fiber_out = fiber * (1 - eta_fil)
    return sugar, water, fiber_out, eth

def distiller(sugar, water, fiber, eth, eta_dis):
    #returns the mass flow rates after being distilled
    k = eth * (1 / eta_dis - 1) / (sugar + water + fiber)
    k = min(k, 1)    #if the stream is purer already it won't make it impure
    sugar_out, water_out, fiber_out = sugar * k, water * k, fiber * k
    return sugar_out, water_out, fiber_out, eth

def dehydrator(sugar, water, fiber, eth, eta_deh):
    #returns the mass flow rates after being dehydrated
    water_out = water * (1 - eta_deh)
    return sugar, water_out, fiber, eth

def capital_cost(option):
    #returns the capital cost of a combination of unit ops stored in a tuple
    fermented = fermenter(option[4], FERMENTERS[option[0]][0])
    cost = vol_flow(option[4]*0.2,option[4]*0.6,option[4]*0.2,0) * FERMENTERS[option[0]][1]
    filtered = filt(*fermented, FILTERS[option[1]][0])
    cost += vol_flow(*fermented) * FILTERS[option[1]][1]
    distilled = distiller(*filtered, DISTILLERS[option[2]][0])
    cost+= vol_flow(*filtered) * DISTILLERS[option[2]][1]
    cost+= vol_flow(*distilled) * DEHYDRATORS[option[3]][1]
    return cost

def flows(option):
    #returns the volumetric flows and densities of each stage of a combination of unit ops
    feed = (option[4]*0.2, option[4]*0.6, option[4]*0.2, 0)
    fermented = fermenter(option[4], FERMENTERS[option[0]][0])
    filtered = filt(*fermented, FILTERS[option[1]][0])
    distilled = distiller(*filtered, DISTILLERS[option[2]][0])
    dehydrated = dehydrator(*distilled, DEHYDRATORS[option[3]][0])
    return [(vol_flow(*row), density(*row)) for row in (feed, fermented, filtered, distilled, dehydrated)]

def pipe_loss(friction, flow, diameter, length):
    #computes head loss of a length of pipe
    return friction * 8 /(math.pi**2 * 9.81) * flow**2 * length / diameter**5

def attachment_loss(loss, flow, diameter):
    #computes head loss of a valve or bend
    return loss * (flow / (math.pi * diameter**2 / 4))**2 / 2 / 9.81

def segment_loss(segment, stage, option, diameter, qualities):
    #computes the net head loss for a segment of pipe
    flow, rho = flows(option)[stage]
    return segment_head(segment, flow, diameter, qualities)

def segment_head(segment, flow, diameter, qualities):
    """computes the head loss if you know the flows so they're 
    not recalculated in the main loop, saves a ton of time"""
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
    #computes the cost of a segment of pipe
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
    #computes the cost of a single component
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
    stage_flows = flows(option)
    #converts head loss (m) to power (W)
    """downhill drops can offset that segment's own losses but not less than 0
    because energy doesn't flow back into the pump"""
    segment_power = 0
    for segment, stage, diameter, qualities, dz in segments:
        flow, rho = stage_flows[stage]
        head = segment_loss(segment, stage, option, diameter, qualities)
        segment_power += rho * G * flow * max(0, dz + head)
    pump_power = segment_power / pump_eff
    i, j, k, l, feed = option
    #convert unit ops from kWh/day to W
    unit_kwh_day = FERMENTERS[i][2] + FILTERS[j][2] + DISTILLERS[k][2] + DEHYDRATORS[l][2]
    unit_power = unit_kwh_day * 3_600_000 / 86_400
    q_out, rho_out = stage_flows[4]
    usable_power = q_out / GAL_TO_M3 * J_PER_GAL_ETH * purity(option) #ethanol chemical energy
    return usable_power / (pump_power + unit_power)

def waste_cost(waste_segments):
    #computes fixed cost of waste segments
    cost = CO2_DUCT_M * DUCT_COST_PER_M
    for segment in waste_segments:
        qualities = [WASTE_PIPE_Q if p[0] == 1 else None for p in segment]
        cost += segment_cost(segment, WASTE_DIAMETER, qualities)
    return float(cost)

def system_cost(option, segments, pump, waste_segments):
    #computes the net cost of an entire system
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

def purity(option):
    #returns the output ehtanol purity given an option of unit ops
    i, j, k, l, feed = option
    return eth_percentage_mass_req(FERMENTERS[i][0], FILTERS[j][0], DISTILLERS[k][0], DEHYDRATORS[l][0])[0]

def keep_best(items):
    #remove strictly worse items (lower eff, higher cost)
    ls = []
    best_loss = float("inf")
    #sorts items by cost, uses loss to break ties
    """each new item must be more expensive than the previous ones checked
    so if it's efficiency is worse get rid of it"""
    for item in sorted(items, key=lambda x: (x[0], x[1])):
        if item[1] < best_loss:
            ls.append(item)
            best_loss = item[1]
    return ls

def segment_choices(segment, flow, rho, dz):
    #for a given segment computes the viable choices with keep_best
    #saves compute to do the segments independently
    choices = []
    #product builds a list of tuples of all the combinations
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
        usable_power = stage_flows[4][0] / GAL_TO_M3 * J_PER_GAL_ETH * purity(option)
        q_feed = stage_flows[0][0]
        #pipe/pump choices (each segment's power already includes its lift)
        per_segment = [segment_choices(seg, *stage_flows[st], dz) for seg, st, dz in layout]
        #merge segments one at a time, remove strictly worse combos after each merge
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
    #negative efficiency because keep_best assumes lower is better for both
    return [(-neg_eff, cost, design) for cost, neg_eff, design in keep_best(results)]

def validate_model():
    S_PER_DAY = 86_400
    D = 0.10
    #inputs
    
    feed = 835_200 * GAL_TO_M3 * 1180.2 / S_PER_DAY
    option = (0, 0, 0, 0, feed)
    stage_flows = flows(option)
    
    #formatted layout of validation model
    val_segments = [
        (((1, 15.24), (2, 90), (2, 90), (0,)), 0, [3, None, None, 0]),
        (((0,), (0,)), 1, [0, 0]),
        (((0,), (0,)), 2, [0, 0]),
        (((0,), (1, 3.048), (2, 90), (2, 90), (0,)), 3, [0, 3, None, None, 0]),
        (((0,),), 4, [0]),]
    
    #mass flows
    s0 = (0.2 * feed, 0.6 * feed, 0.2 * feed, 0)
    s1 = fermenter(feed, FERMENTERS[0][0])
    s2 = filt(*s1, FILTERS[0][0])
    s3 = distiller(*s2, DISTILLERS[0][0])
    s4 = dehydrator(*s3, DEHYDRATORS[0][0])
    
    #losses
    area = math.pi * D**2 / 4
    v = [q / area for q, rho in stage_flows]
    loss_power = sum(stage_flows[st][1] * G * stage_flows[st][0] * segment_head(seg, stage_flows[st][0], D, q)
                     for seg, st, q in val_segments)
    co2 = 0.49 * FERMENTERS[0][0] * s0[0]
    fiber_waste = s1[2] - s2[2]
    dist_waste = sum(s2) - sum(s3)
    deh_waste = s3[1] - s4[1]
    carried_power = (co2 * G * 12.192 + 0.5 * co2 * v[1]**2
                     + fiber_waste * G * 6.096 + 0.5 * fiber_waste * v[2]**2
                     + 0.5 * dist_waste * v[3]**2
                     + 0.5 * deh_waste * v[4]**2
                     + sum(s4) * G * 3 + 0.5 * sum(s4) * v[4]**2)
    pump_power = (loss_power + carried_power) / 0.80
    unit_power = (FERMENTERS[0][2] + FILTERS[0][2] + DISTILLERS[0][2] + DEHYDRATORS[0][2]) * 3_600_000 / S_PER_DAY
    usable_power = stage_flows[4][0] / GAL_TO_M3 * J_PER_GAL_ETH * purity(option)
    
    #site + mold + unit ops + pump + pipe + duct + valves + bends
    cost = (1_760_000 + 12_000
            + capital_cost(option)
            + PUMP_COST[PUMP_RATINGS.index(18), 0] * stage_flows[0][0]
            + PIPE_COST_PER_M[0, 3] * 18.288
            + 228 * 3.048
            + 8 * VALVE_COST[0, 0]
            + 4 * BEND_COST[0, list(ANGLE_TO_LOSS).index(90)])
    
    print(f"Fluid velocity into filter: {v[1]:.2f}")
    print(f"KE of dehydrator waste stream: {0.5 * deh_waste * v[4]**2 * S_PER_DAY / 1000:.2f}")
    print(f"Sugar leaving as distiller waste: {(s2[0] - s3[0]) * S_PER_DAY:.2f}")
    print(f"Capital cost: {cost:.2f}")
    print(f"Energy ROI: {usable_power / (pump_power + unit_power):.2f}")
    print(f"Volume of ethanol out: {stage_flows[4][0] / GAL_TO_M3 * S_PER_DAY:.2f} ")
    print(f"Ethanol Purity: {purity(option):.2f}")

start = time.monotonic()

#builds list of possible unit op combos (eth% > 98)
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

#pipes come with lengths, bends come with angles
pipe_segment_0 = ((1, 0.25), (0,)) #pump -> fermenter
pipe_segment_1 = ((0,) , (1,9.75), (0,)) #fermenter -> filter
pipe_segment_2 = ((0,) , (1, 3.35), (0,)) #filter -> distiller
pipe_segment_3 = ((0,) , (1, 3.35), (2, 90), (1, 1.5), (0,)) #distiller -> dehydrator
pipe_segment_4 = ((0,), (1, 0.25)) # dehydrator -> output

layout = [ #segment, stage, height change
    (pipe_segment_0, 0, 0),
    (pipe_segment_1, 1, +9.75),
    (pipe_segment_2, 2, -3.35),
    (pipe_segment_3, 3, -3.35),
    (pipe_segment_4, 4, 0),
]

FILTER_WASTE_OUTLET = 10.75 # m above ground
DISTILLER_WASTE_OUTLET = 7.40
DEHYDRATOR_WASTE_OUTLET = 4.05

waste_fiber      = ((2, 90), (1, FILTER_WASTE_OUTLET - WASTE_EXIT_HEIGHT))
waste_distiller  = ((2, 90), (1, DISTILLER_WASTE_OUTLET - WASTE_EXIT_HEIGHT))
waste_dehydrator = ((2, 90), (1, DEHYDRATOR_WASTE_OUTLET - WASTE_EXIT_HEIGHT))

waste_segments = [waste_fiber, waste_distiller, waste_dehydrator]

#Description of 1 item in full_designs
#(Efficiency, Cost, ((Fermenter, Filter, Distiller, Dehydrator, Feed (kg/s)), ((diameter, pipe_q, valve_q) for each segment), (pump_lift, pump_q)))
#only recalculates if True, otherwise reads from text file
recalc = True

if recalc == True:
    full_designs = find_optimal(layout, waste_segments)
    with open("full_designs.txt", 'w') as f:
        for item in full_designs:
            f.write(repr(item) + "\n")
else:
    with open("full_designs.txt", 'r') as f:
         full_designs = [ast.literal_eval(line) for line in f if line.strip()]

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
#use arrays to do operations on the entire data set at once
effs_array = np.array([eff for eff, cost, design in full_designs])
costs_array = np.array([cost for eff, cost, design in full_designs])
x_norm = (costs_array - costs_array.min()) / (costs_array.max() - costs_array.min())
y_norm = (effs_array - effs_array.min()) / (effs_array.max() - effs_array.min())

diff = y_norm - x_norm
knee_index = np.argmax(diff)
knee = full_designs[knee_index]
print(knee)
time = time.monotonic() - start
print(f"Elapsed Simluation Time: {time:.2f}")
print(len(options))

#validate_model()