import os
import numpy as np
import sys


if __name__ == "__main__":
    root_dir = '/root/Desktop/hunter/init_game_data/debug/4/'
    img_dir = '/root/Desktop/hunter/data_v1030/round0_eval/'
    img_cls = os.listdir(img_dir)
    cls_img_path = dict()
    for cls_name in img_cls:
        if not os.path.isdir(os.path.join(img_dir, cls_name)):
            continue
        img_paths = os.listdir(os.path.join(img_dir, cls_name))
        cls_img_path[int(cls_name)] = []
        for ipath in img_paths:
            cls_img_path[int(cls_name)].append(os.path.join(img_dir, cls_name, ipath))
    for k in cls_img_path.keys():
        print('cls', k, 'num', len(cls_img_path[k]))
    #sys.exit(0)
    game_data_dirs = [os.path.join(root_dir, f'{i:05}') for i in range(19999, 20000)]
    for gdd in game_data_dirs:
        grid_i = np.load(os.path.join(gdd, 'grid.npy'))
        print(grid_i[:3, :3])
        img_path_i = [[] for _ in range(grid_i.shape[0])]
        for row in range(grid_i.shape[0]):
            for col in range(grid_i.shape[1]):
                img_path_i[row].append(cls_img_path[grid_i[row, col]].pop(0))
        np.save(os.path.join(gdd, 'img_path.npy'), np.array(img_path_i))
        img_path_i = np.load(os.path.join(gdd, 'img_path.npy'))
        print(img_path_i[:3, :3])
        print(type(str(img_path_i[0, 0])))
