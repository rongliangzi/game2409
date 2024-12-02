# gen full game_data from sub grid
import os
import numpy as np


if __name__ == "__main__":
    root_dir = '../non_greedy_grid/'
    sub_grid_dirs = os.listdir(root_dir)
    cls_n = 21
    size = 12
    elim_n = 4
    sub_size = 4  # sub grid size
    game_data_dir = '../init_game_data/debug/a/'
    print('len(sub_grid_dirs)', len(sub_grid_dirs))
    for dir_id, sub_dir in enumerate(sorted(sub_grid_dirs)):
        save_dir = os.path.join(game_data_dir, f'{20000+dir_id}')
        os.makedirs(save_dir, exist_ok=True)
        data_dir = os.path.join(root_dir, sub_dir)
        print(dir_id, data_dir, 'game id:', 20000+dir_id)
        sub_grid = np.load(os.path.join(data_dir, 'grid.npy'))
        sub_loc = np.load(os.path.join(data_dir, 'loc.npy'))
        full_grid = np.zeros((size, size), dtype=int) - 1
        # put sub grid at a random loc
        sub_row, sub_col = np.random.randint(0, size-sub_size, size=2,)
        sub_loc[0] += sub_row
        sub_loc[1] += sub_col
        print('sub_loc', sub_loc)
        for i in range(sub_size):
            for j in range(sub_size):
                full_grid[sub_row + i, sub_col + j] = sub_grid[i, j]
        all_inclusive = dir_id < 100
        # fill other loc with random class
        if all_inclusive:
            other_ele = np.concatenate([np.arange(4, cls_n), np.random.randint(4, cls_n, size=(size**2 // elim_n - cls_n,), dtype=int)])
        else:
            open_set_n = np.random.choice(np.arange(6, 9))
            other_cls_n = np.random.randint(15, 21) - 5
            other_ele = np.concatenate([
                np.array([cls_n-1] * open_set_n, dtype=int), 
                np.random.randint(4, cls_n-1, size=(size**2)//elim_n - 4 - open_set_n, dtype=int)
                ])
        print('Unique cls:', len(np.unique(other_ele)) + 4, 'open_set_n:', (other_ele==cls_n-1).sum())
        other_ele = np.repeat(other_ele, elim_n)
        np.random.shuffle(other_ele)
        pos = 0
        for i in range(size):
            for j in range(size):
                if full_grid[i, j] == -1:
                    full_grid[i, j]  = other_ele[pos]
                    pos += 1
        assert pos == len(other_ele), f'{pos}, {len(other_ele)}'
        np.save(os.path.join(save_dir, f'grid.npy'), full_grid)
        np.save(os.path.join(save_dir, f'loc.npy'), sub_loc)
        if dir_id >= 199:
            break
