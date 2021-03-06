import numpy as np
from gpflow import config
from gym import make
import os
import tensorflow as tf
from pilco.models import PILCO
from pilco.rewards import ExponentialReward
from pilco.controllers import RbfController
import gpflow
float_type = config.default_float()


def rollout(env, pilco, timesteps, verbose=True, random=False, SUBS=1, render=False):
        X = []; Y = [];
        x = env.reset()
        ep_return_full = 0
        ep_return_sampled = 0
        for timestep in range(timesteps):
            if render: env.render()
            u = policy(env, pilco, x, random)
            for i in range(SUBS):
                x_new, r, done, _ = env.step(u)
                ep_return_full += r
                if done: break
                if render: env.render()
            if verbose:
                print("Action: ", u)
                print("State : ", x_new)
                print("Return so far: ", ep_return_full)
            X.append(np.hstack((x, u)))
            Y.append(x_new - x)
            ep_return_sampled += r
            x = x_new
            if done: break
        return np.stack(X), np.stack(Y), ep_return_sampled, ep_return_full


def policy(env, pilco, x, random):
    if random:
        return env.action_space.sample()
    else:
        return pilco.compute_action(x[None, :])[0, :]

class Normalised_Env():
    def __init__(self, env_id, m, std):
        self.env = make(env_id).env
        self.action_space = self.env.action_space
        self.observation_space = self.env.observation_space
        self.m = m
        self.std = std

    def state_trans(self, x):
        return np.divide(x-self.m, self.std)

    def step(self, action):
        ob, r, done, _ = self.env.step(action)
        return self.state_trans(ob), r, done, {}

    def reset(self):
        ob =  self.env.reset()
        return self.state_trans(ob)

    def render(self):
        self.env.render()



def save_pilco(path, X, Y, pilco, sparse=False):
    os.makedirs(path)
    # Dit hoeft eigenlijk niet. Staat in pilco.controller.models[0].X & Y
    np.savetxt(path + 'X.csv', X, delimiter=',')
    np.savetxt(path + 'Y.csv', Y, delimiter=',')
    if sparse:
        with open(path+ 'n_ind.txt', 'w') as f:
            f.write('%d' % pilco.mgpr.num_induced_points)
            f.close()
    np.save(path + 'pilco_values.npy', gpflow.utilities.parameter_dict(pilco))
    #for i,m in enumerate(pilco.mgpr.models):
    #    np.save(path + "model_" + str(i) + ".npy", gpflow.utilities.parameter_dict(m))

def load_pilco(path, sparse=False, controller=None, reward=None, m_init=None, S_init=None):
    X = np.loadtxt(path + 'X.csv', delimiter=',').reshape(-1, 4)
    Y = np.loadtxt(path + 'Y.csv', delimiter=',').reshape(-1, 3)

    if not sparse:
        pilco = PILCO((X, Y), controller=controller, reward=reward, m_init=m_init, S_init=S_init)
    else:
        with open(path+ 'n_ind.txt', 'r') as f:
            n_ind = int(f.readline())
            f.close()
        pilco = PILCO((X, Y), controller=controller, reward=reward, m_init=m_init, S_init=S_init, num_induced_points=n_ind)
    params = np.load(path + "pilco_values.npy", allow_pickle=True).item()
    print(params)
    gpflow.utilities.multiple_assign(pilco, params)
    #for i,m in enumerate(pilco.mgpr.models):
    #    values = np.load(path + "model_" + str(i) + ".npy", allow_pickle=True).item()
    #    print(values)
    #    gpflow.utilities.multiple_assign(m, values)
    return pilco, X, Y