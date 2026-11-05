from new_catalog import FERMENTERS, FILTERS, DISTILLERS, DEHYDRATORS

#densities (kg)
RHO_SUGAR = 1599
RHO_WATER = 997
RHO_FIBER = 1311
RHO_ETH = 789

GAL_TO_M3 = 0.003785411784

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

#with open("UnitOpCombos.txt", 'w') as fid:
    
options = []

for fer in FERMENTERS:
    for fil in FILTERS:
        for dis in DISTILLERS:
            for deh in DEHYDRATORS:
                result = eth_percentage_mass_req(fer[0], fil[0], dis[0], deh[0])
                if result[0] >= 0.98:
                    options.append((FERMENTERS.index(fer),FILTERS.index(fil),DISTILLERS.index(dis),DEHYDRATORS.index(deh),result[1]))

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

cost_best = min(options, key=capital_cost)
feed_best = min(options, key=lambda o: o[4])

pairs = [(option[4], capital_cost(option)) for option in options]

by_feed = sorted(pairs, key=lambda o: o[1])
by_cost = sorted(pairs, key=lambda o: o[0])

print(by_feed)
print("\n\n\n")
print(by_cost)

print(cost_best)