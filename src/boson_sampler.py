# Orquestra usable example of a boson sampling simulation
import photonic
import tequila as tq
import numpy
import json

from itertools import combinations, permutations

def simulate_crespi_setup(trotter_steps):
    return simulate_setup(trotter_steps)

def simulate_setup(trotter_steps=5, initial_state=None, samples=None, bs_parameters=None, phases=None):
    # Default is the same as in the Paper
    if bs_parameters is None:
        bs_parameters = [0.19,0.55,0.4,0.76,0.54,0.95,0.48,0.99,0.51,0.44]
    if phases is None:
        phases = [2.21,0.64,1.08,1.02,1.37,2.58,2.93,1.1]
    if initial_state is None:
        initial_state = "1.0|1>_a|1>_c|1>_e"
    
    setup = photonic.PhotonicSetup(pathnames=["a", "b", "c", "d", "e"], S=0, qpm=2)
    a = "a"
    b = "b"
    c = "c"
    d = "d"
    e = "e"

    # transform phases to pi*t form
    phase_parameters = [phase / numpy.pi for phase in phases]
    # transform beam-splitter parameters to pi*t
    bs_parameters = [numpy.arcsin(p)/numpy.pi for p in bs_parameters]

    initial_state = setup.initialize_state(initial_state)
    U = tq.circuit.QCircuit()
    assert (len(initial_state.state.keys()) == 1)
    for k, v in initial_state.state.items():
        for i, v in enumerate(k.array):
            if v == 1:
                U += tq.gates.X(target=i)


    setup.add_circuit(U=U)
    
    setup.add_beamsplitter(path_a=a, path_b=b, t=bs_parameters[0], phi=0, steps=trotter_steps)
    setup.add_phase_shifter(path=a, t=-1)
    setup.add_phase_shifter(path=b, t=-1)
    
    setup.add_phase_shifter(path=b, t=-phase_parameters[0])
    setup.add_beamsplitter(path_a=b, path_b=c, t=bs_parameters[1], phi=0, steps=trotter_steps)
    
    setup.add_phase_shifter(path=a, t=-phase_parameters[1])
    setup.add_beamsplitter(path_a=a, path_b=b, t=bs_parameters[2], phi=0, steps=trotter_steps)
    
    setup.add_phase_shifter(path=c, t=-phase_parameters[2])
    setup.add_beamsplitter(path_a=c, path_b=d, t=bs_parameters[3], phi=0, steps=trotter_steps)
    
    setup.add_phase_shifter(path=c, t=-phase_parameters[3])
    setup.add_beamsplitter(path_a=b, path_b=c, t=bs_parameters[4], phi=0, steps=trotter_steps)
    
    setup.add_beamsplitter(path_a=d, path_b=e, t=bs_parameters[5], phi=0, steps=trotter_steps)
    
    setup.add_phase_shifter(path=b, t=-phase_parameters[4])
    setup.add_beamsplitter(path_a=a, path_b=b, t=bs_parameters[6], phi=0, steps=trotter_steps)
    
    setup.add_phase_shifter(path=c, t=-phase_parameters[5])
    setup.add_beamsplitter(path_a=c, path_b=d, t=bs_parameters[7], phi=0, steps=trotter_steps)
    
    setup.add_phase_shifter(path=b, t=-phase_parameters[6])
    setup.add_beamsplitter(path_a=b, path_b=c, t=bs_parameters[8], phi=0, steps=trotter_steps)
    
    setup.add_phase_shifter(path=b, t=-phase_parameters[7])
    setup.add_beamsplitter(path_a=a, path_b=b, t=bs_parameters[9], phi=0, steps=trotter_steps)
    
    result = setup.simulate_wavefunction()
    result._state = {k:numpy.abs(v)**2 for k,v in result.state.state.items()} 

    message = "Boson Sampling Simulation" 
    message_dict = {}
    message_dict["message"] = message
    message_dict["schema"] = "message"
    message_dict["S"] = 0
    message_dict["qpm"]=2
    message_dict["distribution"] = str(result)
    message_dict["parameters"] = {"trotter_steps":trotter_steps, "samples":samples, "initial_state":str(initial_state)}
    
    with open("result.json",'w') as f:
        f.write(json.dumps(message_dict, indent=2))

def filter_one_photon_counts(state: photonic.PhotonicStateVector, n_photons=3):
    result = dict()
    pathnames = [k for k in state.paths.keys()]

    for comb in combinations(pathnames, n_photons):
        key = ""
        label = ""
        for i in comb:
            key += "|1>_" + str(i)
            label += str(i)
        result[label] = state.get_basis_state(string=key)

    return result

def filter_three_photon_counts(state):
    pathnames = [k for k in state.paths.keys()]

    result = {}
    for comb in combinations(pathnames, 3):
        key = "|1>_" + str(comb[0]) + "|1>_" + str(comb[1]) + "|1>_" + str(comb[2])
        result[key] = state.get_basis_state(string=key)

    # all states with 2 photons in one path and 1 photon in another '21'
    for comb in permutations(pathnames, 2):
        key = "|2>_" + str(comb[0]) + "|1>_" + str(comb[1])
        result[key] = state.get_basis_state(string=key)

    # all states with 3 photons in one path
    for path in pathnames:
        key = "|3>_" + str(path)
        result[key] = state.get_basis_state(string=key)
    
    return result

def analyse(sim_result):
    with open(sim_result, 'r') as f:
        sim_result = json.load(f)
    setup = photonic.PhotonicSetup(pathnames=["a", "b", "c", "d", "e"], S=sim_result["S"], qpm=sim_result["qpm"])
    state = setup.initialize_state(sim_result["distribution"])
    
    three_photon_counts = filter_three_photon_counts(state) 
    one_photon_counts = filter_one_photon_counts(state) 
    three_photon_counts = {k: float(numpy.abs(v)) for k,v in three_photon_counts.items()} # numpy types are not json serializable, imaginary parts always zero
    one_photon_counts = {k: float(numpy.abs(v)) for k,v in one_photon_counts.items()} # numpy types are not json serializable, imaginary parts always zero
    
    checksum = sum(list(three_photon_counts.values()))

    message_dict = {}
    message_dict["schema"] = "message"
    message_dict["state"] = str(state)
    message_dict["one_photon_counts"] = one_photon_counts
    message_dict["three_photon_counts"] = three_photon_counts
    message_dict["samples"] = sim_result["parameters"]["samples"]
    message_dict["checksum"] = checksum

    with open("analyse.json",'w') as f:
        f.write(json.dumps(message_dict, indent=2))

