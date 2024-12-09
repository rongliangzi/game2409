import pandas as pd
import os
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--team', type=str)
    args = parser.parse_args()
    a = pd.read_csv(f'team_game_data/{args.team}/team_stats_st20241208ed20241208.csv', header=[0], index_col=[0,1])
    type2 = {}
    correct_n = {i: 0 for i in range(21)}
    total_num = {i: 664 for i in range(8)}
    total_num[8] = 652
    for i in range(9, 16):
        total_num[i] = 664
    total_num[16] = 644
    total_num[17] = 664
    total_num[18] = 668
    total_num[19] = 632
    total_num[20] = 1180
    for i in range(a.shape[0]):
        row = a.iloc[i]
        if row['game_type'] == '2':
            gid = row['game_data_id']
            if gid not in type2.keys():
                type2[gid] = {}
                for j in range(21):
                    type2[gid][j] = row[f'correct_{j}']
                    correct_n[j] += row[f'correct_{j}']
    for k in correct_n.keys():
        print(f'class {k:2}: {correct_n[k] / total_num[k]:.4f}, {correct_n[k]}/{total_num[k]}')
