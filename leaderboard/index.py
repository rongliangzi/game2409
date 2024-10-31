from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)

# 读取CSV文件
# df = pd.read_csv('score.csv', index_col =0)
df = pd.read_csv('../team_game_data/20241029/daily_stats.csv',)
df.columns = ['teamid', 'idx', 'cum_score','begin', 'rounds','acc']
df = df[['teamid','cum_score','acc']]
df = df.groupby('teamid').mean()
df = df.reset_index()
df.loc[0, 'teamid'] = '红鲤鱼与绿鲤鱼与驴'


@app.route('/')
def index():
    # 将CSV数据传递到HTML模板
    teams = df.to_dict(orient='records')
#     print(teams)
    return render_template('index.html', teams=teams)

if __name__ == '__main__':
    app.run(debug=True)
