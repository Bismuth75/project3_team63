eta_fer_options = [0.5, 0.75, 0.9, 0.95]
eta_fil_options = [0.5, 0.75, 0.9, 0.98]
eta_dis_options = [0.81, 0.9, 0.915, 0.98]
eta_deh_options = [0.5, 0.75, 0.9, 0.98]

#densities (kg)
rho_sugar = 1599
rho_water = 997
rho_fiber = 1311
rho_eth = 789

def eth_percentage_mass_req(eta_fer, eta_fil, eta_dis, eta_deh, waste_mass = 1):
    sugar0 = 0.2 * waste_mass
    water0 = 0.6 * waste_mass
    fiber0 = 0.2 * waste_mass
    
    rho_sugar = 1599
    rho_water = 997
    rho_fiber = 1311
    rho_eth = 789
    # eth1 = 0.51 * eta_fer * sugar0
    # sugar1 = (1 - eta_fer) * eta_fer * sugar0
    # water1 = water0
    # fiber1 = fiber0
    # CO2out1 = 0.49 * eta_fer * sugar0
    
    # eth2 = eth1
    # sugar2 = sugar1
    # water2 = water1
    # fiber2 = fiber1 * (1 - eta_fil)
    # fiber2out = fiber1 * eta_fil
    
    # k3 = (eth2 * (1/eta_dis - 1)) / (sugar2 + water2 + fiber2)
    k_3 = (0.51 * eta_fer * sugar0 * (1/eta_dis - 1)) / ((1 - eta_fer) * eta_fer * sugar0 + water0 + fiber0 * (1 - eta_fil))
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
    sugar_final = (1 - eta_fer) * eta_fer * sugar0 * k_3
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
    return (eth_percent, 100000 / gal_final)

def req_mass(eta_fer, eta_fil, eta_dis, eta_deh, waste_mass = 1):
    sugar0 = 0.2 * waste_mass
    water0 = 0.6 * waste_mass
    fiber0 = 0.2 * waste_mass
    
    rho_sugar = 1599
    rho_water = 997
    rho_fiber = 1311
    rho_eth = 789
    # eth1 = 0.51 * eta_fer * sugar0
    # sugar1 = (1 - eta_fer) * eta_fer * sugar0
    # water1 = water0
    # fiber1 = fiber0
    # CO2out1 = 0.49 * eta_fer * sugar0
    
    # eth2 = eth1
    # sugar2 = sugar1
    # water2 = water1
    # fiber2 = fiber1 * (1 - eta_fil)
    # fiber2out = fiber1 * eta_fil
    
    # k3 = (eth2 * (1/eta_dis - 1)) / (sugar2 + water2 + fiber2)
    k_3 = (0.51 * eta_fer * sugar0 * (1/eta_dis - 1)) / ((1 - eta_fer) * eta_fer * sugar0 + water0 + fiber0 * (1 - eta_fil))
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
    sugar_final = (1 - eta_fer) * eta_fer * sugar0 * k_3
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
    return 100000 / gal_final


options = []

for i in range(4):
    for j in range(4):
        for k in range(4):
            for l in range(4):
                result = eth_percentage_mass_req(eta_fer_options[i], eta_fil_options[j], eta_dis_options[k], eta_deh_options[l])
                if result[0] >= 0.98:
                    options.append((i,j,k,l,result[1]))
    
print(options)

