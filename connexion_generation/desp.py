# Code for Dynamic Equilibrium Structural Plasticity

import numpy as np
from connexion_generation.utility import change_connexion, determine_pruning_pairs, determine_connection_pairs
from reservoir.reservoir import update_reservoir
import matplotlib.pyplot as plt
from tqdm import tqdm


def compute_variance(states, growth_parameter, average="WHOLE", queue_size=10):
    # Calculate the synaptic change based on variance as per user requirement
    states = np.array(states)
    delta_z = states / growth_parameter

    # we compute variance over a time window
    if average == "WHOLE":
        delta_z = np.var(delta_z, axis=0)
    # else we take the variance of the last value from the time window, which doesn't make sense for a single value
    # so for LAST, it's either not applicable or we keep as is, because variance of a single value is always 0.
    # else we take the variance of the last queue_size values from the time window
    elif average == "QUEUE":
        delta_z = np.var(delta_z[-queue_size:], axis=0)

    return np.trunc(delta_z)  # Apply truncation similar to the original implementation


def bounded_desp(W_e, states, variance, value, W_inhibitory_connexions=np.array([]), max_partners=12, mi_based=False):
    neurons = np.arange(len(states[0]))
    total_prun = 0
    total_add = 0

    # DECREASE THE RATE
    need_pruning = neurons[variance <= 0.1]
    # We prune excitatory connexion to decrease the rate

    new_prune_pairs = determine_pruning_pairs(need_pruning, W_e, mi_based=False)

    for connexion in new_prune_pairs:
        W_e = change_connexion(W_e, connexion[0], connexion[1], -value)
        total_prun += 1
    # We add inhibitory connexion to decrease the rate
    if min(W_inhibitory_connexions.shape) > 0:
        new_connexion_pairs = determine_connection_pairs(need_pruning, W_inhibitory_connexions, True)
        for connexion in new_connexion_pairs:
            W_inhibitory_connexions = change_connexion(W_inhibitory_connexions, connexion[0], connexion[1], value)
            total_add += 1

    # INCREASE THE RATE
    need_increase = neurons[variance >= 1]
    # We add an excitatory connexion to increase the rate
    new_connexion_pairs = determine_connection_pairs(need_increase, W_e, max_partners=max_partners)
    for connexion in new_connexion_pairs:
        W_e = change_connexion(W_e, connexion[0], connexion[1], value)
        total_add += 1
    # If needed we prune inhibitory connexion to increase the rate
    if min(W_inhibitory_connexions.shape) > 0:
        new_prune_pairs = determine_pruning_pairs(need_pruning, W_inhibitory_connexions)
        for connexion in new_prune_pairs:
            W_inhibitory_connexions = change_connexion(W_inhibitory_connexions, connexion[0], connexion[1], -value)
            total_prun += 1

    return W_e, W_inhibitory_connexions, total_add, total_prun


def run_desp_algorithm(W, Win, bias, leaky_rate, activation_function, input_data, time_increment, weight_increment,
                       min_variance, max_variance, max_increment=None, mi_based=False, average="WHOLE", visualize=False):
    state = np.random.uniform(0, 1, bias.size)
    state_history = []

    total_add = 0
    total_prun = 0
    add = [0]
    prun = [0]
    step = 0
    steps = []

    if max_increment is None:
        int_logspace = [time_increment]
        max_increment = time_increment
    else:
        logspace = np.logspace(np.log10(time_increment), np.log10(max_increment), num=10)
        int_logspace = np.round(logspace).astype(int)

    # initialization
    init_length = time_increment * 5
    for i in range(init_length):
        state = update_reservoir(W, Win, input_data[i], state, leaky_rate, bias, activation_function)
        state_history.append(state)
    input_data = input_data[init_length:]

    pbar = tqdm(total=input_data.size)
    while input_data.size > max_increment:
        # randomly select the increment size
        inc = np.random.choice(int_logspace)

        for i in range(inc):
            state = update_reservoir(W, Win, input_data[i], state, leaky_rate, bias, activation_function)
            state_history.append(state)
        input_data = input_data[inc:]

        variance = compute_variance(state_history[-inc:], average=average)
        W, _, nb_new_add, nb_new_prun = bounded_desp(W, state_history[-inc:], min_variance,  max_variance, weight_increment, mi_based=mi_based)

        total_add += nb_new_add
        total_prun += nb_new_prun
        add.append(total_add)
        prun.append(total_prun)
        step += inc
        steps.append(step)
        pbar.update(inc)

    add = np.array(add)
    prun = np.array(prun)
    pbar.close()

    if visualize:
        plt.figure()
        plt.plot(steps, add, label="total number of added connexion")
        plt.plot(steps, prun, label="total number of prunned connexion")
        plt.plot(steps, add - prun, label="difference")
        plt.plot(steps, steps, linestyle=(0, (1, 10)))
        plt.legend()
        plt.grid()
    return W, state_history