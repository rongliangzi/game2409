import os
import numpy as np
import sys

def get_cls_img_path(img_dir):
    img_cls = os.listdir(img_dir)
    cls_img_path = dict()  # {int(cls_name): [full_img_path]}
    for cls_name in img_cls:
        if not os.path.isdir(os.path.join(img_dir, cls_name)):
            continue
        img_paths = os.listdir(os.path.join(img_dir, cls_name))
        cls_img_path[int(cls_name)] = []
        for ipath in img_paths:
            cls_img_path[int(cls_name)].append(os.path.join(img_dir, cls_name, ipath))
    for k in cls_img_path.keys():
        print('cls', k, 'num', len(cls_img_path[k]))
    return cls_img_path


if __name__ == "__main__":
    # assign img_path to each init_game_data
    game_data_root_dir = '/root/Desktop/hunter/init_game_data/round0_eval/2/'
    # read all img_paths of each class under img_dir
    img_dir = '/root/Desktop/hunter/data_v1107/round0_eval/'
    cls_img_path = get_cls_img_path(img_dir)
    game_data_dirs = [os.path.join(game_data_root_dir, f'{i:05}') for i in range(0, 100)]
    cls_cnt = {k: 0 for k in cls_img_path.keys()}  # current use img count for each class
    for gdd in game_data_dirs:
        grid_i = np.load(os.path.join(gdd, 'grid.npy'))
        img_path_i = [[] for _ in range(grid_i.shape[0])]  # (size, size)
        for row in range(grid_i.shape[0]):
            for col in range(grid_i.shape[1]):
                cls_rc = grid_i[row, col]
                idx = cls_cnt[cls_rc]%len(cls_img_path[cls_rc])
                img_path_rc = cls_img_path[cls_rc][idx]
                img_path_i[row].append(img_path_rc)
                cls_cnt[cls_rc] += 1
        np.save(os.path.join(gdd, 'img_path.npy'), np.array(img_path_i))
        img_path_i = np.load(os.path.join(gdd, 'img_path.npy'))
    print(cls_cnt, sum(cls_cnt.values()))
