from flask import Flask, render_template
import numpy as np
import pandas as pd

app = Flask(__name__)

@app.route('/')
def index():
    team_info = pd.read_csv('../team_game_data/team_info_20241104.csv', index_col = 0)
    tstats_df = []
    for tname, tid in zip(team_info['teamname'].values, team_info['teamid'].values):
        try:
            tstats = pd.read_csv(f'../team_game_data/{tid}/team_stats.csv', index_col = 0)
            tstats_type0 = tstats[tstats['game_type'].isin([2, '2'])]
            tstats_type1 = tstats[~tstats['game_type'].isin([2, '2'])]
            tstats_cum = tstats_type0.groupby(['game_data_id'])['cum_score'].max().reset_index()['cum_score'].mean()
            tstats_acc = tstats_type0.groupby(['game_data_id'])['acc'].max().reset_index()['acc'].mean()
            tstats_str = tstats_type1.groupby(['game_data_id'])['cum_score'].max().reset_index()['cum_score'].mean()
            tstats = pd.DataFrame(
                [[tname, tid, tstats_cum, tstats_acc, tstats_str]],
                columns = ['teamname', 'teamid', 'tstats_cum', 'tstats_acc', 'tstats_str']
            )
            tstats_df.append(tstats)
        except:
            continue
    if len(tstats_df) == 0:
        tstats_df = pd.DataFrame(
            columns = ['teamname', 'teamid', 'tstats_cum', 'tstats_acc', 'tstats_str']
        )
    else:
        tstats_df = pd.concat(tstats_df)
        tstats_df = tstats_df.sort_values(by='tstats_str', ascending=False)
        tstats_df = tstats_df.dropna(subset=['tstats_str'])

    # 将CSV数据传递到HTML模板
    teams = tstats_df.to_dict(orient='records')
    return render_template('index_str.html', teams=teams)

if __name__ == '__main__':
    app.run(debug=True)
