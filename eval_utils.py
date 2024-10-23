from datetime import datetime


def eval_episode_rule(policy, env, ):
    transition = 0
    print(datetime.now(), f'Begin')
    obs, info = env.reset()
    action = policy(obs)
    print(datetime.now(), f'Action: {action}')
    obs, rew, term, _, info = env.step(action)
    transition += 1
    print(transition, term,)
    while not term:
        action = policy(obs)
        print(datetime.now(), f'Action: {action}')
        obs, rew, term, _, info = env.step(action)
        transition += 1
        print(datetime.now(), transition, term)
    print()
