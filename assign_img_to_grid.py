import os
import numpy as np
import sys
import argparse


def get_cls_img_path(img_dir):
    # img_dir should be like 00/1.png, 00/2.png, 01/1.png, ...
    # return int(cls): list of img_path
    img_cls = sorted(os.listdir(img_dir))
    cls_img_path = dict()  # {int(cls_name): [full_img_path]}
    for cls_name in img_cls:
        cls_img_dir = os.path.join(img_dir, cls_name)
        if not os.path.isdir(cls_img_dir):
            continue
        img_paths = sorted(os.listdir(cls_img_dir))
        cls_img_path[int(cls_name)] = []
        for ipath in img_paths:
            cls_img_path[int(cls_name)].append(os.path.join(cls_img_dir, ipath))
    print('Available img cnt of each class:')
    for k, v in cls_img_path.items():
        print('cls', k, 'num', len(v))
    return cls_img_path


if __name__ == "__main__":
    # assign img_path to each init_game_data
    parser = argparse.ArgumentParser()
    parser.add_argument('--gd_dir', type=str, default='/root/Desktop/hunter/init_game_data/round0_test/2/')
    parser.add_argument('--img_dir', type=str, default='/root/Desktop/hunter/data_v1107_noise/round0_test/')
    parser.add_argument('--base_n', type=int)
    parser.add_argument('--open_n', type=int)
    args = parser.parse_args()
    game_data_root_dir = args.gd_dir
    # read all img_paths of each class under img_dir
    img_dir = args.img_dir
    cls_img_path = get_cls_img_path(img_dir)
    #game_data_dirs = [os.path.join(game_data_root_dir, f'{i:05}') for i in range(0, 200)]
    game_data_dirs = [os.path.join(game_data_root_dir, d) for d in sorted(os.listdir(game_data_root_dir))]
    cls_cnt = {k: 0 for k in cls_img_path.keys()}  # used img count of each class
    
    # img with index higher than target cnt will have mask =0, else 1
    target_cls_cnt = dict()
    for i in range(20):
        target_cls_cnt[i] = args.base_n
    target_cls_cnt[20] = args.open_n
    count_n = 0  # count of img with mask=1
    for gdd in game_data_dirs:
        print(f'Processsing {gdd}')
        grid_i = np.load(os.path.join(gdd, 'grid.npy'))
        img_path_i = [[] for _ in range(grid_i.shape[0])]  # (size, size)
        img_mask_i = []
        for row in range(grid_i.shape[0]):
            for col in range(grid_i.shape[1]):
                cls_rc = grid_i[row, col]
                img_idx_cls = cls_cnt[cls_rc] % len(cls_img_path[cls_rc])  # if need more img than available, loop
                # cnt higher than target, mask=0
                if cls_cnt[cls_rc] >= target_cls_cnt[cls_rc]:
                    img_mask_i.append(0)
                else:
                    img_mask_i.append(1)
                    count_n += 1
                img_path_rc = cls_img_path[cls_rc][img_idx_cls]
                img_path_i[row].append(img_path_rc)
                cls_cnt[cls_rc] += 1
        np.save(os.path.join(gdd, 'img_path.npy'), np.array(img_path_i))
        np.save(os.path.join(gdd, 'img_mask.npy'), np.array(img_mask_i))
    print('cnt of each cls img:\n', cls_cnt)
    print('total img num:', sum(cls_cnt.values()))
    print('img cnt with mask=1:', count_n)
