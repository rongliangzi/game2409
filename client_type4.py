import requests
import numpy as np
import time
import matplotlib
matplotlib.rcParams['toolbar'] = 'None'
import matplotlib.pyplot as plt
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from policy import *


url = 'http://52.81.28.203:8081/'
url = 'http://69.230.243.237:8081/'

def random_policy(action_shape):
    return np.random.randint(action_shape)
    
    
def send_recv(url, data):
    # send action, receive new game data
    try:
        st = time.time()
        response = requests.post(url, json=data)
        #print(f'client get data time: {(time.time()-st):.1f}s')
        if response.status_code == 200:
            # 检查返回的 JSON 数据
            json_response = response.json()
            is_end = json_response.get('is_end')
            score = json_response.get('score')
            img = json_response.get('img', None)
            if img is not None:
                img = np.array(img, dtype=np.uint8)
            bag = np.array(json_response.get('bag'), dtype=np.int32)
            grid = np.array(json_response.get('grid'), dtype=np.int32)
            game_id = json_response.get('game_id')
            return is_end, score, img, bag, grid, game_id
        else:
            print(f'Response invalid. {response.text}, Status code: {response.status_code}')
            return None, None, None, None, None, None
    except Exception as e:
        print(f'Error occurred: {e}')
        return None, None, None, None, None, None
    

def check_init_grid(grid, elim_n, cls_n):
    v = np.unique(grid)
    for v_ in v:
        if v_ < 0:
            continue
        v_n = (grid == v_).sum() + (grid == v_-(cls_n+1)).sum()
        assert v_n % elim_n ==0, f'{v_}, {v_n}, elim_n: {elim_n}'
        #print(f'{v_}, {v_n}')


def modify_grid(grid, cls_n, random_mask):
    new_grid = grid.copy()
    for i in range(new_grid.shape[0]):
        for j in range(new_grid.shape[1]):
            if new_grid[i, j] in [-1, -1 - (cls_n + 1)]:
                continue
            new_grid[i, j] = min(new_grid[i, j] + random_mask[i, j], cls_n-1)
    return new_grid


def team_play_game(team_id, url, begin):
    print('='*40 + f'\nTeam id: {team_id} game begin!!!')
    # grid: grid[i,j] is the cls ground truth of (i,j). After collect, grid[i, j] becomes -1. For agent current loc, grid[i,j]-=cls_n+1
    cls_n = 21
    is_end, score, init_img, bag, grid, game_id = send_recv(url, {'team_id': team_id, 'begin': begin, })
    
    if is_end is None:
        return None, None
    #check_init_grid(grid, 3, cls_n)
    init_grid = grid.copy()
    min_index = np.unravel_index(np.argmin(init_grid), grid.shape)
    init_grid[min_index] += cls_n + 1
    acc = 1.0  # 模拟的识别正确率，在真实grid基础上加1再clip，作为识别错误
    # 使用方法: new_grid = modify_grid(grid, cls_n, random_mask)
    random_mask = (np.random.uniform(size=grid.shape) >= acc).astype(int)
    cum_score = score
    rounds = 0
    game_fig_dir = f'./game_fig/{game_id}/'
    os.makedirs(game_fig_dir, exist_ok=False)
    assert init_img is not None
    #plt.imsave(f'{game_fig_dir}/rounds{rounds}.png', init_img)
    while (is_end is not None) and (not is_end):
        #print(is_end, score, game_id)
        # take an act
        rounds += 1
        # action: 0: down, 1: right, 2: up, 3: left, 4: collect
        # cls: when take action 4, server will judge if cls is the same as grid[i,j], if wrong, score += -0.1
        action = random_policy(5)
        action = greedy_policy(grid, bag, cls_n=cls_n, random_mask=random_mask)
        cls = int(grid.min() + cls_n + 1)
        data = {'game_id': game_id, 'action': action, 'cls': cls, 'team_id': team_id, 'grid_cls': init_grid.tolist()}
        print(f'{game_id}, rounds: {rounds}, action: {data["action"]}, current score: {score:.3f}, cum_score: {cum_score:.3f}')
        # transition to new status
        is_end, score, _, bag, grid, game_id_ = send_recv(url, data)
        cum_score += score
        assert game_id == game_id_, f'{game_id}, {game_id_}'
    #print(f'Team id: {team_id} game id {game_id} end, score: {cum_score:.3f}\n')
    return game_id, cum_score


if __name__=="__main__":
    team_play_game('toyota', url, '300000')
    team_id = 'xiaomi'
    # begin must be {game_type}{game_data_id}
    # 1: {size:6, cls_n:21, elim_n:3}, not used for now
    # 2: {size:12, cls_n:21, elim_n:4}
    # 3: {size:12, cls_n:21, elim_n:3}
    # 4: {size:16, cls_n:21, elim_n:4}
    # 5: {size:20, cls_n:21, elim_n:5}
    # 6: {size:20, cls_n:21, elim_n:4}
    game_type = '3'
    game_n = 5
    stats = dict()
    st = time.time()
    with ProcessPoolExecutor(max_workers=1) as executor:
        futures = [executor.submit(team_play_game, team_id, url, f'{game_type}{game_i:05}') for game_i in range(game_n)]
        for future in as_completed(futures):
            game_id, cum_score = future.result()
            if game_id is not None:
                stats[game_id] = cum_score
    team_score = dict()
    for k,v in stats.items():
        team_id = k.split('_')[0]
        if team_id not in team_score:
            team_score[team_id] = []
        team_score[team_id].append(v)
    for k, v in team_score.items():
        print(f'Team {k} get avg score: {np.mean(v):.2f}, std: {np.std(v):.2f} in {len(v)} games')
    print(f'Total time: {(time.time()-st):.1f}s')
    
