import fitbit
import json, pathlib
from datetime import datetime
import arrow
import config

token_file = "tokens.json"
intraday_file_format_string = 'data/{}_intraday.json'
activity_file_format_string = 'data/{}_activity.json'
sleep_file_format_string = 'data/{}_sleep.json'
full_day_log = 'data/_gather_log.json'

def update_tokens(token_dict):
    print('tokens refreshing')
    with open(token_file, 'w') as outfile:
        json.dump(token_dict, outfile)

def get_tokens():
    p = pathlib.Path(token_file)
    try:
        with p.open() as f:
            return json.load(f)
    except OSError:
        print('No tokens file found, using manually-collected defaults...')
        d = {}
        d['access_token'] = 'YOUR TOKEN HERE - use gather_keys_oauth2.py'
        d['refresh_token'] = 'YOUR TOKEN HERE'
        #d['scope'] = ['weight', 'location', 'heartrate', 'profile', 'settings', 'activity', 'nutrition', 'sleep', 'social']
        #d['user_id'] = '5WYKXC'
        d['expires_at'] = 1501906494.5773776 #Replace with value from gather_keys
        with open(token_file, 'w') as outfile:
            json.dump(d, outfile)
        return d

def save_json(fn, data):
    with open(fn, 'w') as outfile:
            json.dump(data, outfile)

def gather_data(day):
    print("Gathering fitbit data for {:YYYY-MM-DD}...".format(day))
    tokens = get_tokens()
    fbc = fitbit.Fitbit(config.client_id, config.client_secret,access_token=tokens['access_token'], refresh_token=tokens['refresh_token'], expires_at=tokens['expires_at'], refresh_cb=update_tokens)
    
    range = day.span('day')
    day_str = day.format('YYYY-MM-DD')

    id = fbc.intraday_time_series('activities/steps', detail_level='15min', start_time = range[0], end_time=range[1])
    data_file = intraday_file_format_string.format(day_str)
    save_json(data_file, id)

    s = fbc.sleep()
    data_file = sleep_file_format_string.format(day_str)
    save_json(data_file, s)

    act = fbc.activity_stats()
    data_file = activity_file_format_string.format(day_str)
    save_json(data_file, act)

def get_devices():
    tokens = get_tokens()
    fbc = fitbit.Fitbit(config.client_id, config.client_secret,access_token=tokens['access_token'], refresh_token=tokens['refresh_token'], expires_at=tokens['expires_at'], refresh_cb=update_tokens)
    devs = fbc.get_devices()
    return devs

def last_sync_date():
    devs = get_devices()
    last_sync = max([arrow.get(d['lastSyncTime']) for d in devs])
    return last_sync

def gather_recent_full_data():
    '''
    Gets all full daily fitbit data available in between the last full date and the most recent full date.
    Intended to be run once (or more) a day.
    '''
    data_days = []
    try:
        with open(full_day_log) as f:
            data_days = json.load(f)
    except OSError:
        pass#data_days.append(arrow.now().shift(days=-1).span("day")[0].for_json())
    try:
        last_full_day = max([arrow.get(d) for d in data_days])
    except ValueError:
        #First run, hack last full day
        print("First run detected.")
        last_full_day = arrow.now().shift(days=-2).span("day")[0]
    last_sync = last_sync_date()
    print("Last gathered data: {:YYYY-MM-DD}, Last sync: {:YYYY-MM-DD HH:mm}".format(last_full_day, last_sync))
    ranges = arrow.Arrow.span_range('day', last_full_day.shift(days=1), last_sync.shift(days=-1))
    print("Plan to gather data for {} days...".format(len(ranges)))
    for r in ranges:
        gather_data(r[0])
        data_days.append(r[0].for_json())
        with open(full_day_log, 'w') as outfile:
            json.dump(data_days, outfile)


if __name__ == '__main__':
    #realtime data
    #gather_data(arrow.now())
    #daily data
    gather_recent_full_data()