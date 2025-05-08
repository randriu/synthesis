

def get_intervals(interval_path):
    intervals = {}

    with open(interval_path) as file:
        for line in file:
            parts = line.split()
            name = parts[0]
            interval_str = parts[1]

            lower, upper = map(float, interval_str.strip('[]').split(','))
            decimal_digits = max(interval_str.find(',') - interval_str.find('.') - 1, interval_str.rfind(']') - interval_str.rfind('.') - 1)
            interval_complement_str = f'[{round(1-upper,decimal_digits)},{round(1-lower,decimal_digits)}]'

            intervals[name] = (interval_str, interval_complement_str)

    return intervals

def replace_intervals_aircraft(old_path, new_path, intervals):
    old_file = open(old_path, 'r')
    new_file = open(new_path, 'w')
    skip_params = False
    for line in old_file:
        if '/(1)' in line:
            parts = line.split(':')
            transition = parts[1].strip(' ()')
            if transition.startswith('-1'):
                start = transition.find('(') + 1
                end = transition.find('+')
                name = transition[start:end]
                interval = intervals[name][1]
            else:
                start = 0
                end = transition.find(')')
                name = transition[start:end]
                interval = intervals[name][0]
            line = f'{parts[0]}: {interval}\n'

        if not skip_params:
            new_file.write(line)
        else:
            new_file.write('\n')
            skip_params = False

        skip_params = '@parameters' in line

    old_file.close()
    new_file.close()

def replace_intervals_satallite(old_path, new_path, intervals):
    old_file = open(old_path, 'r')
    new_file = open(new_path, 'w')
    skip_params = False

    param_name = next(iter(intervals)) # get name of first (and only) parameter

    for line in old_file:
        if ' ' + param_name in line:
            line = line.replace(param_name, intervals[param_name][0])
        if '1-' + param_name in line:
            line = line.replace(f'1-{param_name}', intervals[param_name][1])

        if not skip_params:
            new_file.write(line)
        else:
            new_file.write('\n')
            skip_params = False

        skip_params = '@parameters' in line


def main():
    sufixes = ['big', 'nominal_eps', 'nominal', 'small']
    # model_path = 'models/ipomdp/idk/aircraft/aircraft.drn'
    # for sufix in sufixes:
    #     interval_path = f'models/ipomdp/idk/aircraft/aircraft_{sufix}.intervals'
    #     new_model_path = f'models/ipomdp/idk/aircraft/aircraft_{sufix}.drn'

    #     intervals = get_intervals(interval_path)
    #     replace_intervals_aircraft(model_path, new_model_path, intervals)

    model_path = 'models/ipomdp/idk/satellite/satellite_prob.drn'
    for sufix in sufixes:
        interval_path = f'models/ipomdp/idk/satellite/satellite_{sufix}.intervals'
        new_model_path = f'models/ipomdp/idk/satellite/satellite_prob_{sufix}.drn'

        intervals = get_intervals(interval_path)
        replace_intervals_satallite(model_path, new_model_path, intervals)



main()