from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)

df = pd.read_csv('../team_game_data/20241029/daily_stats.csv',)
df.columns = ['teamid', 'idx', 'cum_score','begin', 'rounds','acc']
df = df[['teamid','cum_score','acc']]                                                                                     
df = df.groupby('teamid').mean()                                                                                          
df = df.reset_index()
df = df.sort_values(by='cum_score', ascending=False, inplace=False)
#     teamid  cum_score       acc
#     0   ferrari  -4.164640  0.994213
#     1  maserati -16.548700  0.006432
#     2    xiaomi -20.444871  1.000000


@app.route('/')
def index():
    teams = df.to_dict(orient='records')
    return render_template('index.html', teams=teams)

if __name__ == '__main__':
    app.run(host="0.0.0.0")
