import numpy as np
import os
import sys

def can_end(a, b, th=0.1):
    asum = sum(a.values())
    bsum = sum(b.values())
    total_prob_diff = 0
    for k in a.keys():
        prob_diff = abs(a[k]/asum - b[k]/bsum)
        #print('prob_diff', prob_diff)
        total_prob_diff += prob_diff
    print(f'total_prob_diff: {total_prob_diff:.3f}, th:{th:.3f}')
    return total_prob_diff < th

    
def adjust_one_pair(grid_li, cur, tgt):
    cursum = sum(cur.values())
    tgtsum = sum(tgt.values())
    h_cls = -1  # class whose cur prob over target max
    max_diff = -1  # max value
    l_cls = -1  # class whose cur prob below target min
    min_diff = 1  # min value diff
    for k in cur.keys():
        p_diff = cur[k]/cursum - tgt[k]/tgtsum
        if p_diff > max_diff:
            max_diff = p_diff
            h_cls = k
        if p_diff < min_diff:
            min_diff = p_diff
            l_cls = k
    do_adjust = False
    for i, grid_i in enumerate(grid_li):
        h_cnt = (grid_i == h_cls).sum()
        l_cnt = (grid_i == l_cls).sum()
        #print(f'i{i} h cls{h_cls}, cnt {h_cnt}, l cls{l_cls}, cnt {l_cnt}')
        if h_cnt > l_cnt:
            cur[h_cls] -= (h_cnt - l_cnt)
            cur[l_cls] += (h_cnt - l_cnt)
            grid_i[grid_i == h_cls] = -1
            grid_i[grid_i == l_cls] = -2
            grid_i[grid_i == -1] = l_cls
            grid_i[grid_i == -2] = h_cls
            do_adjust = True
            break
    return do_adjust


if __name__ == '__main__':
    # set 1. root_dir, game_data_dir. 2. threshold 3. target_cls_distribution (now fixed)
    # to make class distribution close to target class distribution
    root_dir = '/root/Desktop/hunter/init_game_data/round1_test/2/'
    game_data_dirs = [os.path.join(root_dir, f'{i:05}') for i in range(0, 100)]
    class_num = dict()
    target_cls_distribution = dict()
    for i in range(20):
        target_cls_distribution[i] = 700
    target_cls_distribution[20] = 1750
    print('target_cls_distribution', target_cls_distribution)
    grid_li = []
    for gdd in game_data_dirs:
        grid_i = np.load(os.path.join(gdd, 'grid.npy'))
        grid_li.append(grid_i)
        unique_v = np.unique(grid_i)
        for v in unique_v:
            if v not in class_num:
                class_num[v] = 0
            class_num[v] += (grid_i == v).sum()
    print('class num', class_num)
    grid_sum = sum(class_num.values())
    print('class sum on all grids:', grid_sum)
    for _ in range(3000):
        if can_end(class_num, target_cls_distribution, 0.05):
            break
        do_adjust = adjust_one_pair(grid_li, class_num, target_cls_distribution)
        if not do_adjust:
            break
    print('class num', class_num, sum(class_num.values()))
    #sys.exit(0)
    # save new
    for i, gdd in enumerate(game_data_dirs):
        np.save(os.path.join(gdd, 'grid.npy'), grid_li[i])
