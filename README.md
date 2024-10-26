## app.py
Main entrance of server
Run 
```
gunicorn -w 4 -b 0.0.0.0:8081 app:app
```
## daily_stats_team.py

Run py file without any change to get team stats ::yesterday:: . Generate and save csv in `{save_dir}/{yyyymmdd}/daily_stats.csv` 
```
python daily_stats_team.py
```
## client_type4.py
Client demo

## cfg
- `cfg/chusai_eval_cfg.yaml`, Configuration for chusai eval phase.

- `cfg/chusai_test_cfg.yaml`, Configuration for chusai test phase.

- `cfg/fusai_eval_cfg.yaml1, Configuration for fusai eval phase.

- `cfg/fusai_test_cfg.yaml`, Configuration for fusai test phase.

