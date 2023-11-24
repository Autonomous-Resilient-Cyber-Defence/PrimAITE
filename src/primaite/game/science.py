from random import random


def simulate_trial(p_of_success: float) -> bool:
    """
    Simulates the outcome of a single trial in a Bernoulli process.

    This function returns True with a probability 'p_of_success', simulating a success outcome in a single
    trial of a Bernoulli process. When this function is executed multiple times, the set of outcomes follows
    a binomial distribution. This is useful in scenarios where one needs to model or simulate events that
    have two possible outcomes (success or failure) with a fixed probability of success.

    :param p_of_success: The probability of success in a single trial, ranging from 0 to 1.
    :returns: True if the trial is successful (with probability 'p_of_success'); otherwise, False.
    """
    return random() < p_of_success
