import argparse as ap
import pathlib as plib
import sys
import parse_csv

def parse_args(raw_args):
    parser = ap.ArgumentParser()
    parser.add_argument('result_file')
    parser.add_argument('guess_dir')
    parser.add_argument('out_dir')
    
    return parser.parse_args(raw_args)


def collect_result(result_fpath, guess_fpath, out_dir):
    file_name = guess_path.name
    first_underscore = guess_path.find('_')

    assert first_underscore != -1, file_name

    player_name = file_name[:first_underscore]
    
    total_score, total_score_delta, scoring_log = parse_csv.main([result_fpath.as_posix(), guess_fpath.as_posix(), out_dir])
    previous_score = total_score - total_score_delta

    return [player_name, {"previous_score": previous_score, "current_score": total_score, "scoring_log": scoring_log}]


def determine_positions(results_dict):
    current_scores_sorted = reversed(sorted(result_dict.keys(), key=lambda x: results_dict[x]['current_score']))
    previous_scores_sorted = reversed(sorted(result_dict.keys(), key=lambda x: results_dict[x]['previous_score']))

    position = 1
    last_counted_score = None
    for name in current_scores_sorted:
        results_dict[name]["current_position"] = position
        this_score = results_dict[name]["current_score"]
        if last_counted_score is None:
            last_counted_score = this_score 
        else if last_counted_score != this_score:
            position = position + 1

    for name in previous_scores_sorted:
        results_dict[name]["previous_position"] = position
        this_score = results_dict[name]["previous_score"]
        if last_counted_score is None:
            last_counted_score = this_score 
        else if last_counted_score != this_score:
            position = position + 1

    return current_scores_sorted


def build_leaderboard(current_scores_sorted, results_dict):
    leaderboard = []
    for name in current_scores_sorted:
        current_position = results_dict[name]["current_position"]
        previous_position = results_dict[name]["previous_position"]
        position_delta = previous_position - current_position

        leaderboard.append(str(current_position) + ". " + name + "(" + str(position_delta) + ")")

    return leaderboard

def main(raw_args):
    args = parse_args(raw_args)

    result_fpath = plib.Path(args.result_file).resolve()
    assert result_fpath.is_file(), result_fpath.as_posix()

    guess_dpath = plib.Path(args.guess_dir).resolve()
    assert guess_dpath.is_dir(), guess_dpath.as_posix()

    guess_fpaths = [file for file in guess_dpath.glob('*.csv')]
    results_list = [collect_result(result_fpath, guess_fpath, out_dir) for guess_fpath in guess_fpaths]
    results_dict = {res[0]: res[1] for res in results_list}
    current_scores_sorted = determine_positions(results_dict)
    print(build_leaderboard(current_scores_sorted, results_dict))


if __name__ == '__main__':
    main(sys.argv[1:])
