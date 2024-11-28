# brute search data as test set
import numpy as np
import copy
import time
import os
from datetime import datetime
import multiprocessing as mp


def gen_grid(size, cls_n, elim_n):
    # randomly generate init grid
    grid = np.concatenate(
            [np.arange(cls_n),
             np.random.randint(0, cls_n, size=(size**2 // elim_n - cls_n,), dtype=int)
             ])
    grid = np.repeat(grid, elim_n)
    np.random.shuffle(grid)
    grid = grid.reshape(size, size)
    return grid


def init_grid_loc(size, cls_n, elim_n):
    grid = gen_grid(size, cls_n, elim_n)
    loc = np.random.randint(0, size, size=2, dtype=int)
    return grid, loc


def have_loop(path):
    if 4 in path: 
        idx = len(path)  - 1 - path[::-1].index(4) + 1
    else:
        idx = 0
    pure_move = path[idx:]
    if (1 in pure_move) and (3 in pure_move):
        return True
    if (0 in pure_move) and (2 in pure_move):
        return True
    return False


def dfs(grid, arrival, loc, bag, path, rew, not_collect_first):
    # search for grid where not collect when first arrival in best_path 
    # grid: current grid
    # bag: {cls: n}
    # path: current action sequence
    # rew: current cum reward
    # not_collect_first: not collect exist in path
    #if path == [1,4,1,4,0,4,3,4,0,4,1,4,0,4,3,4,3,4,3,4,2,4,1,4,2,4,3,4,2,4]:
    #    print(path)
    if (arrival!=0).sum() > 3 and arrival.sum() / (arrival!=0).sum() > 1.1:
        return path, -1e6, not_collect_first
    if (len(path) > 3) and (path.count(4) / len(path)< 0.3):
        return path, -1e6, not_collect_first
    if (len(path) > 9) and (path.count(4) / len(path)< 0.4):
        return path, -1e6, not_collect_first
    if have_loop(path):
        #print(path)
        return path, -1e6, not_collect_first
    if (grid > -1).sum() == 0:
        #print(path, rew)
        return path, rew, not_collect_first
    if len(path) > 3 * size**2:
        #print(path)
        return path, rew -3 * ((grid>-1).sum()), not_collect_first
    row, col = loc
    best_path, best_rew, best_flag = None, -1e6, None
    normal_cost = -0.1 - sum(bag.values()) / grid.size
    max_arrival = 3  # max arrival times on the same loc
    cls_i = grid[row, col]
    cur_n = bag.get(cls_i, 0)
    elim_cur = cur_n + 1 == elim_n
    if (row < grid.shape[0]-1) and (arrival[row+1, col] < max_arrival) and not elim_cur:
        # action 0, transition
        new_arrival = arrival.copy()
        new_arrival[row+1, col] += 1
        path_, rew_, flag = dfs(grid, new_arrival, (row+1, col), bag, path+[0], rew+normal_cost, not_collect_first or grid[row, col]>-1)
        if rew_ > best_rew:
            best_path, best_rew, best_flag = path_, rew_, flag
    if (row > 0) and (arrival[row-1, col] < max_arrival) and  not elim_cur:
        # action 2,
        new_arrival = arrival.copy()
        new_arrival[row-1, col] += 1
        path_, rew_, flag = dfs(grid, new_arrival, (row-1, col), bag, path+[2], rew+normal_cost, not_collect_first or grid[row, col]>-1)
        if rew_ > best_rew:
            best_path, best_rew, best_flag = path_, rew_, flag
    if (col < grid.shape[1]-1) and (arrival[row, col+1] < max_arrival) and  not elim_cur:
        # action 1
        new_arrival = arrival.copy()
        new_arrival[row, col+1] += 1
        path_, rew_, flag = dfs(grid, new_arrival, (row, col+1), bag, path+[1], rew+normal_cost, not_collect_first or grid[row, col]>-1)
        if rew_ > best_rew:
            best_path, best_rew, best_flag = path_, rew_, flag
    if (col > 0) and (arrival[row, col-1] < max_arrival) and not elim_cur:
        # action 3
        new_arrival = arrival.copy()
        new_arrival[row, col-1] += 1
        path_, rew_, flag = dfs(grid, new_arrival, (row, col-1), bag, path+[3], rew+normal_cost, not_collect_first or grid[row, col]>-1)
        if rew_ > best_rew:
            best_path, best_rew, best_flag = path_, rew_, flag
    if grid[row, col] > -1:
        # action 4
        # update bag, grid
        new_bag = copy.deepcopy(bag)
        cur_n = new_bag.get(cls_i, 0)
        if elim_cur:
            normal_cost += 1
            del new_bag[cls_i]
        else:
            new_bag[cls_i] = cur_n + 1
        new_grid = grid.copy()
        new_grid[row, col] = -1
        path_, rew_, flag = dfs(new_grid, arrival.copy(), loc, new_bag, path+[4], rew+normal_cost, not_collect_first)
        if rew_ > best_rew:
            best_path, best_rew, best_flag = path_, rew_, flag
    return best_path, best_rew, best_flag


def random_init_search(size, cls_n, elim_n, seed=0):
    np.random.seed(int(time.time()*10-173e8+seed))
    grid, loc = init_grid_loc(size, cls_n, elim_n)
    arrival = np.zeros_like(grid)
    #grid = np.array([[1,2,2,],[3,2,3],[1,3,1]])
    #loc = (0,1)
    #arrival[loc[0], loc[1]] = 1
    print(grid, loc)
    st = time.time()
    best_path, best_rew, best_flag = dfs(grid, arrival, loc, dict(), [], 0, False)
    print(f'Time: {time.time()-st:.1f}')
    print('Best', best_path, best_rew, best_flag)
    if best_flag:
        save_game_solution(grid, loc, best_path, best_rew)


def save_game_solution(grid, loc, best_path, best_rew):
    while True:
        try:
            now = datetime.now()
            time_key = now.strftime("%Y%m%d-%H%M%S")
            data_dir = f'../non_greedy_grid/{time_key}/'
            os.makedirs(data_dir, exist_ok=False)
            break
        except Exception as e:
            time.sleep(1)
    print(f'Saving to {data_dir}')
    np.save(f'{data_dir}/grid.npy', grid)
    np.save(f'{data_dir}/loc.npy', loc)
    np.save(f'{data_dir}/action_seq.npy', np.array(best_path))
    np.save(f'{data_dir}/best_rew.npy', np.array(best_rew))


if __name__ == "__main__":
    size = 4
    cls_n = 4
    elim_n = 4
    cpu_cnt = mp.cpu_count()
    print(f'CPU count: {cpu_cnt}')
    params = [(size, cls_n, elim_n, i) for i in range(10000)]
    with mp.Pool(cpu_cnt//2-10) as pool:
        result = pool.starmap_async(random_init_search, params)
        results = result.get()
    #random_init_search(size, cls_n, elim_n)
