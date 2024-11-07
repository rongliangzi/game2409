import numpy as np
import os
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
    print('h_cls', h_cls, 'l_cls', l_cls)
    for grid_i in grid_li:
        print(grid_i.shape)
        h_cnt = (grid_i == h_cls).sum()
        l_cnt = (grid_i == l_cls).sum()
        print('h_cnt', h_cnt, 'l_cnt', l_cnt)
        if h_cnt > l_cnt:
            cur[h_cls] -= (h_cnt - l_cnt)
            cur[l_cls] += (h_cnt - l_cnt)
            grid_i[grid_i == h_cls] = -1
            grid_i[grid_i == -1] = l_cls
            grid_i[grid_i == l_cls] = h_cls
            break


if __name__ == '__main__':
    root_dir = '/root/Desktop/hunter/init_game_data/debug/4/'
    game_data_dirs = [os.path.join(root_dir, f'{i:05}') for i in range(19995, 20000)]
    class_num = dict()
    target_cls_distribution = dict()
    for i in range(20):
        target_cls_distribution[i] = 200
    target_cls_distribution[20] = 560
    print('target_cls_distribution', target_cls_distribution)
    target_sum = sum(target_cls_distribution.values())
    for k in target_cls_distribution.keys():
        target_cls_distribution[k] /= target_sum
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
    print('grid_sum', grid_sum)
    while not can_end(class_num, target_cls_distribution, 0.1):
        adjust_one_pair(grid_li, class_num, target_cls_distribution)
    print('class num', class_num)
