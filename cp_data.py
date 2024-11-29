import os
import shutil

def copy_and_rename(src_dir, dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    for i in range(100):
        src_folder = os.path.join(src_dir, f'{i+100:05d}')
        dest_folder = os.path.join(dest_dir, f'{i:05d}')
        print(src_folder, dest_folder)
        if os.path.isdir(src_folder):
            shutil.copytree(src_folder, dest_folder)
        else:
            print('src not dir')

copy_and_rename('/root/Desktop/hunter/init_game_data/round0_test/2/', '/root/Desktop/hunter/init_game_data/round1_eval/2/')
copy_and_rename('/root/Desktop/hunter/init_game_data/round0_test/a/', '/root/Desktop/hunter/init_game_data/round1_eval/a/')
