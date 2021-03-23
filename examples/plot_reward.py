import numpy as np
import matplotlib.pyplot as plt

def plt_rwrd(time_str):
    rewards = np.load('./logs/' + time_str + '/rewards.npz')

    plt.plot(rewards['total_r'])

    return len(rewards['total_r'])

#time_str1 = '23-03-2021-14:48:29'
#time_str2 = '23-03-2021-15:08:01'
time_str3 = '23-03-2021-15:20:33'

l = plt_rwrd(time_str3)

plt.xticks(range(l))
plt.xlabel('Trail [-]')
plt.ylabel('Reward [-]')
plt.show()