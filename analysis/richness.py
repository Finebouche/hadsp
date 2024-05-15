from scipy import sparse
import numpy as np


def spectral_radius(W):
    eigen = sparse.linalg.eigs(W, k=1, which="LM", maxiter=W.shape[0] * 20, tol=0.1, return_eigenvectors=False)
    return max(abs(eigen))


def compute_pearson(states1, states2):
    # Takes states and produces a pearson similarity
    mean1 = np.mean(states1)
    mean2 = np.mean(states2)

    numerator = np.sum((states1 - mean1) * (states2 - mean2))
    denominator = np.sqrt(np.sum((states1 - mean1) ** 2) * np.sum((states2 - mean2) ** 2))

    return numerator / denominator


# for a network of size n, compute pearson for every neuron
def pearson_matrix(states):
    n = states.shape[1]
    pearson_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            pearson_matrix[i, j] = pearson(states[:, i], states[:, j])
    return pearson_matrix


# Paper uses temp = 5000
def uncoupled_dynamics(STATE_H, temp=5000, A=0.9):
    # A : in (0, 1] and expresses the desired amount of explained variability
    # temps : int, the number of steps we want to evaluate the dynamics on
    STATE_H = np.array(STATE_H)[:temp, ]

    # compute the (sorted) singular values and the poucentage wise singular values
    _, singular_values, _ = np.linalg.svd(STATE_H)
    rel_sv = []
    for s in singular_values:
        rel_sv.append(s / np.sum(singular_values))

    # compute the number of singular values that explains A variability
    UD = 0
    frac = 0
    while frac < A:
        frac = frac + rel_sv[UD]
        UD += 1
    return UD, frac


# calculate estimator of Renyi’s quadratic entropy by the Parzen Window method using aGaussian kernel
def renyi_entropy(states, K=0.3):
    # K = 0.3 in the paper
    n = states.shape[1]
    states = states - np.mean(states, axis=0)
    states = states / np.std(states, axis=0)
    entropy = 0

    # the gaussian kernel use for approximation with the kernel size K
    def gaussian(x):
        return np.exp(-x ** 2 / (2 * K ** 2))

    for i in range(n):
        for j in range(n):
            entropy += gaussian(states[:, i] - states[:, j])
    return np.log(entropy / (n ** 2))
