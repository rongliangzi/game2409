import os
import yaml
import numpy as np
import pandas as pd
import pickle
from datetime import datetime
import shutil
import argparse


def add_not_finish_game(st, ed, mode, team_stats, df_index, team_id):
    assert mode in ['2', 'a'], f'mode must be 2/a, but {mode} provided'
    for i in range(st, ed):
        not_finish_v = {'cum_score': -2000, 'game_type': mode, 'game_data_id': f'{i:05}'}
        exist = any(gt+gi == f'{mode}{i:05}' for gt, gi in zip(team_stats['game_type'], team_stats['game_data_id']))
        if not exist:
            df_index.append((team_id, f'not_finish_{mode}{i:05}'))
            for k in team_stats.keys():
                team_stats[k].append(not_finish_v.get(k, 0))


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--st', type=int, default=0)
    parser.add_argument('--ed', type=int, default=0)
    parser.add_argument('--ast', type=int, default=0)
    parser.add_argument('--aed', type=int, default=-1)
    parser.add_argument('--st2', type=int, default=0)
    parser.add_argument('--ed2', type=int, default=-1)
    parser.add_argument('--verbose', type=int, default=0)
    parser.add_argument('--save_dir', type=str, default="./team_game_data/")
    args = parser.parse_args()
    # run this file to get game stats for each team
    save_dir = args.save_dir
    all_teams = os.listdir(save_dir)
    for team_id in all_teams:
        team_stats = {'cum_score': [], 'game_type': [], 'game_data_id': [], 'rounds': [], 'acc': [], 'correct_n': []}
        df_index = []
        # iterate on all teams
        team_dir = os.path.join(save_dir, team_id)
        if (not os.path.isdir(team_dir)) or team_id.startswith('20241'):
            continue
        now = datetime.now()
        # before round0, only use public dir data to generate team_stats
        if now < datetime(2024, 11, 11, 1, 47, 00) and not any(team_id.startswith(sp) for sp in ['lzrong', 'zzxu', 'zhli']):
            if os.path.exists(f'{team_dir}/team_stats.csv'):
                os.remove(f'{team_dir}/team_stats.csv')
            if os.path.exists(team_dir + '/public/game_result.pkl'):
                with open(f'{team_dir}/team_stats.csv', 'w') as f:
                    f.write(f',,cum_score,game_type,game_data_id,rounds,acc\n,,0,2,00000,0,0')
            continue
        # after public
        all_game_key = os.listdir(team_dir)
        for game_key in all_game_key:
            # all games of one team
            if (not game_key.startswith('20241')) or (int(game_key[:8]) < 20241111):
                continue
            if (args.st != 0) and (int(game_key[:8]) < args.st):
                continue
            if (args.ed != 0) and (int(game_key[:8]) > args.ed):
                continue
            cur_path = os.path.join(team_dir, game_key)
            if not os.path.isdir(cur_path):
                continue
            if not os.path.exists(os.path.join(cur_path, 'finish.txt')):
                continue
            game_result_path = os.path.join(team_dir, game_key, 'game_result.pkl')
            if not os.path.exists(game_result_path):
                continue
            try:
                with open(game_result_path, 'rb') as f:
                    game_result = pickle.load(f)
                if 'begin' not in game_result.keys():
                    continue
                game_result['game_type'] = game_result['begin'][0]
                game_result['game_data_id'] = game_result['begin'][1:]
                #del game_result['begin']
                for k in team_stats.keys():
                    team_stats[k].append(game_result.get(k, 0))
                df_index.append((team_id, game_key))
            except Exception as e:
                print(f'Exception {e} when loading {game_result_path}')
                #shutil.rmtree(os.path.join(team_dir, game_key))
        if args.verbose:
            print(f'Stats {team_id:>13}, game num: {len(df_index)}')
        if (args.ast >=0) and (args.aed > args.ast):
            add_not_finish_game(args.ast, args.aed, 'a', team_stats, df_index, team_id)
        if (args.st2 >=0) and (args.ed2 > args.st2):
            add_not_finish_game(args.st2, args.ed2, '2', team_stats, df_index, team_id)
        if (args.st != 0) or (args.ed != 0):
            save_csv_path = os.path.join(team_dir, f'team_stats_st{args.st}ed{args.ed}.csv')
        else:
            save_csv_path = os.path.join(team_dir, f'team_stats.csv')
        if len(df_index) == 0:
            with open(save_csv_path, 'w') as f:
                f.write(f',,cum_score,game_type,game_data_id,rounds,acc')
            continue
        df = pd.DataFrame(team_stats, index=pd.MultiIndex.from_tuples(df_index))
        df.to_csv(save_csv_path)

