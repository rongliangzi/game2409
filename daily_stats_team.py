import os
from datetime import datetime, timedelta
import yaml
import numpy as np
import pandas as pd


if __name__=="__main__":
    with open('./cfg.yaml') as f:
        cfg = yaml.load(f, Loader=yaml.FullLoader)
    yesterday = datetime.now() - timedelta(days=1)
    yesterday = yesterday.strftime("%Y%m%d")
    print(f'Stats leaderboard on {yesterday}')
    save_dir = cfg['save_dir']
    all_teams = os.listdir(save_dir)
    day_stats = {'cum_score': []}
    index = []
    for team_id in all_teams:
        team_dir = os.path.join(save_dir, team_id)
        all_game_key = os.listdir(team_dir)
        for game_key in all_game_key:
            if game_key.startswith(yesterday):
                cum_score_path = os.path.join(team_dir, game_key, 'cum_score.npy')
                if not os.path.exists(cum_score_path):
                    continue
                cum_score = np.load(cum_score_path)
                day_stats['cum_score'].append(cum_score)
                index.append((team_id, game_key))
    print(day_stats)
    df = pd.DataFrame(day_stats, index=pd.MultiIndex.from_tuples(index))
    print(df)
    df.to_csv(os.path.join(save_dir, yesterday, f'daily_stats.csv'))
