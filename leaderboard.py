import argparse as ap
import pathlib as plib
import sys
import parse_csv

def parse_args(raw_args):
    parser = ap.ArgumentParser()
    parser.add_argument('result_file')
    parser.add_argument('guess_dir')
    parser.add_argument('out_dir')
    parser.add_argument('--no-write', action='store_true')
    
    return parser.parse_args(raw_args)


def collect_result(result_fpath, guess_fpath, out_dir, no_write):
    file_name = guess_fpath.name
    first_underscore = guess_fpath.name.find('_')

    assert first_underscore != -1, file_name

    player_name = file_name[:first_underscore]
    
    parse_csv_flags = [result_fpath.as_posix(), guess_fpath.as_posix(), out_dir]

    if no_write:
        parse_csv_flags.append("--no-write")

    total_score, total_score_delta, scoring_log = parse_csv.main(parse_csv_flags)
    previous_score = total_score - total_score_delta

    tagged_scoring_log = [player_name + ": " + log for log in scoring_log]

    return [player_name, {"previous_score": previous_score, "current_score": total_score, "scoring_log": tagged_scoring_log}]


def determine_positions_helper(results_dict, key_str):
    score_key = key_str + "_score"
    position_key = key_str + "_position"

    scores_sorted = [item for item in reversed(sorted(results_dict.keys(), key=lambda x: results_dict[x][score_key]))]

    position = 1
    last_counted_score = None
    for name in scores_sorted:
        results_dict[name][position_key] = position
        this_score = results_dict[name][score_key]

        if last_counted_score is None:
            last_counted_score = this_score 
            position = position + 1
        elif last_counted_score != this_score:
            position = position + 1

    return scores_sorted


def determine_positions(results_dict):
    determine_positions_helper(results_dict, "previous")
    return determine_positions_helper(results_dict, "current")


def build_leaderboard(current_scores_sorted, results_dict):
    leaderboard = []
    for name in current_scores_sorted:
        current_position = results_dict[name]["current_position"]
        previous_position = results_dict[name]["previous_position"]
        position_delta = previous_position - current_position

        if position_delta >= 0:
            position_delta_str = "+" + str(position_delta)
        else:
            position_delta_str = str(position_delta)

        leaderboard.append(str(current_position) + ". " + name + ": " + str(results_dict[name]["current_score"]) + " (" + position_delta_str + ")")

    return leaderboard

def main(raw_args):
    args = parse_args(raw_args)

    result_fpath = plib.Path(args.result_file).resolve()
    assert result_fpath.is_file(), result_fpath.as_posix()

    guess_dpath = plib.Path(args.guess_dir).resolve()
    assert guess_dpath.is_dir(), guess_dpath.as_posix()

    guess_fpaths = [file for file in guess_dpath.glob('*_Guess.csv')]
    results_list = [collect_result(result_fpath, guess_fpath, args.out_dir, args.no_write) for guess_fpath in guess_fpaths]
    results_dict = {res[0]: res[1] for res in results_list}
    current_scores_sorted = determine_positions(results_dict)
    print("\n".join(build_leaderboard(current_scores_sorted, results_dict)))

    complete_scoring_log = []
    for val in results_dict.values():
        complete_scoring_log = complete_scoring_log + val["scoring_log"]

    print("\n\n\nFull scoring log: ")
    print("\n".join(complete_scoring_log))
if __name__ == '__main__':
    main(sys.argv[1:])
