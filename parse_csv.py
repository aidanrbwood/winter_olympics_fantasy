import csv
import argparse as ap
import pathlib as plib
import sys
import copy
import datetime
import itertools

EVENT_STR = 'Event'
GENDER_STR = 'Gender'
CLASS_STR = 'Class'

GOLD_STR = 'Gold_Country'
SILVER_STR = 'Silver_Country'
BRONZE_STR = 'Bronze_Country'
MEDAL_STRS = [BRONZE_STR, SILVER_STR, GOLD_STR]
SCORE_STR = "Score"

CORRECT_GUESS_POINTS = 4

def lookup_medal_from_country(event_data, country):
    for medal in MEDAL_STRS:
        if country in event_data[medal]:
            return medal.replace("_Country", "")
    assert False, "Didn't find: " + country + " in " + str(event_data)

def score_event_helper(event_result, event_guess):
    assert event_result[EVENT_STR] == event_guess[EVENT_STR]
    assert event_result[GENDER_STR] == event_guess[GENDER_STR]
    assert event_result[CLASS_STR] == event_guess[CLASS_STR]

    incorrect_country_result_list = []
    incorrect_country_guess_list = []
    points = 0
    scoring_log = []

    # Handle perfect scores first, produce lists of incorrect guesses that can then be used to determine near guesses
    for medal_str in MEDAL_STRS:
        result_country = event_result[medal_str]
        guessed_country = event_guess[medal_str]
        assert isinstance(result_country, str)
        assert isinstance(guessed_country, str)

        if guessed_country == result_country:
            #scoring_log.append("Scored " + str(CORRECT_GUESS_POINTS) + " points for perfect guess " + medal_str.replace("_Country", "") + " for " + guessed_country)
            points = points + CORRECT_GUESS_POINTS
        else:
            incorrect_country_result_list.append(result_country)
            incorrect_country_guess_list.append(guessed_country)

    num_incorrect = len(incorrect_country_guess_list)
    assert(num_incorrect == len(incorrect_country_result_list))

    if num_incorrect == 0:
        # Perfect guess, extra points
        scoring_log.append("Scored 8 points for a perfect podium")
        points = points + 8
    else:
        # Now we check if any countries that were guessed incorrectly were just in a different medal position
        for incorrect_country_guess in incorrect_country_guess_list:
            if incorrect_country_guess in incorrect_country_result_list:
                #scoring_log.append("Scored 2 points for near guess " + incorrect_country_guess + " was guessed as " + lookup_medal_from_country(event_guess, incorrect_country_guess) + " but was actually " + lookup_medal_from_country(event_result, incorrect_country_guess))
                points = points + 2
                incorrect_country_result_list.remove(incorrect_country_guess)

    scoring_log = "Scored " + str(points) + " from MEDAL/RESULT/GUESS: " + ", ".join([medal_str[:1] + "/" + event_result[medal_str] + "/" + event_guess[medal_str] for medal_str in reversed(MEDAL_STRS)])
    print(scoring_log)

    return [scoring_log, points]

def generate_perms(existing_perms, new_perms):
    if len(new_perms) == 0:
        return existing_perms
    if len(existing_perms) == 0:
        return new_perms

    res = []
    for existing_perm in existing_perms:
        for new_perm in new_perms:
            res.append(existing_perm + new_perm)
    return res


# Handle ties
# If the results were:
# Gold: Canada, USA
# Silver: China
# Bronze: 
#
# Generate the two following permutations, score them both, and then take the highest
# Gold: Canada
# Silver: USA
# Bronze: China

# Gold: USA
# Silver: Canada
# Bronze: China
def get_result_permutations(event_result):
    perms = []

    for medal_str in reversed(MEDAL_STRS):
        perms = generate_perms(perms, [list(it) for it in itertools.permutations(event_result[medal_str])])

    print("From: " + str(event_result[GOLD_STR]) + ", " + str(event_result[SILVER_STR]) + ", " + str(event_result[BRONZE_STR]) + " generated: " + str(perms))
    res = []
    for perm in perms:
        assert(len(perm) == 3), str(perm)
        new_result = event_result.copy()
        new_result[GOLD_STR] = perm[0]
        new_result[SILVER_STR] = perm[1]
        new_result[BRONZE_STR] = perm[2]
        res.append(new_result)

    return res

def format_event_guess(event_guess):
    res = event_guess.copy()
    for medal_str in MEDAL_STRS:
        assert len(res[medal_str]) <= 1
        if len(res[medal_str]) == 0:
            res[medal_str] = "NONE"
        else:
            res[medal_str] = res[medal_str][0]
    return res


def score_event(event_result, event_guess_raw):
    max_score = None
    event_guess = format_event_guess(event_guess_raw)
    for event_result_permutation in get_result_permutations(event_result):
        [log, new_score] = score_event_helper(event_result_permutation, event_guess)
        if max_score is None or new_score > max_score:
            max_score = new_score
    return ["", max_score]


def score_events(result_data, guess_data):
    # Check if result has data yet
    for event, event_result in result_data.items():
        event_guess = guess_data[event]
        
        # Check if there are results yet
        if len(event_result[GOLD_STR]) == 0:
            continue
        # If there are results, check if we've already scored it
        if event_guess[SCORE_STR] != "":
            continue

        [scoring_log, score] = score_event(result_data[event], event_guess)
        
        # Update the guess_data dict
        event_guess[SCORE_STR] = str(score)

    return guess_data


def parse_args(raw_args):
    parser = ap.ArgumentParser()
    parser.add_argument('result_file')
    parser.add_argument('guess_file')
    
    return parser.parse_args(raw_args)


def parse_csv(csv_path):
    with csv_path.open('r') as csv_file:
        dict_reader = csv.DictReader(csv_file)

        ret_dict = {}
        for row in dict_reader:
            for medal in MEDAL_STRS:
                if row[medal] == '':
                    row[medal] = []
                else:
                    row[medal] = row[medal].split(", ")

            key_str = "[" + row[EVENT_STR] + ", " + row[GENDER_STR] + ", " + row[CLASS_STR] + "]"
            ret_dict[key_str] = row
        return ret_dict

def parse_guess_csv(filename):
    guess_data = parse_csv(filename)
    # Initialize the Score column in the event its not there yet
    for guess, event_guess in guess_data.items():
        if SCORE_STR not in event_guess:
            event_guess[SCORE_STR] = ''

    return guess_data


def write_csv(filepath, data):
    with filepath.open('w') as f:
        fieldnames = [EVENT_STR, GENDER_STR, CLASS_STR, GOLD_STR, SILVER_STR, BRONZE_STR, SCORE_STR]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for event, event_data in data.items():
            # De-listify
            if len(event_data[GOLD_STR]) > 0:
                assert len(event_data[GOLD_STR]) == 1, str(event_data[GOLD_STR]) + str(type(event_data[GOLD_STR]))
                assert len(event_data[SILVER_STR]) == 1
                assert len(event_data[BRONZE_STR]) == 1
                event_data[GOLD_STR] = event_data[GOLD_STR][0]
                event_data[SILVER_STR] = event_data[SILVER_STR][0]
                event_data[BRONZE_STR] = event_data[BRONZE_STR][0]
            else:
                event_data[GOLD_STR] = None
                event_data[SILVER_STR] = None
                event_data[BRONZE_STR] = None


            writer.writerow(event_data) 

def main():
    args = parse_args(sys.argv[1:])
    result_path = plib.Path(args.result_file).resolve()
    guess_path = plib.Path(args.guess_file).resolve()

    result_data = parse_csv(result_path)
    guess_data = parse_guess_csv(guess_path)

    updated_guess_data = score_events(result_data, copy.deepcopy(guess_data))

    if guess_data == updated_guess_data:
        print("No updates")
    else:
        today_str = str(datetime.date.today()).replace("-", "_")
        current_name = guess_path.stem
        if "_updated_" in current_name:
            new_name = current_name[:current_name.find("_updated_")] + "_updated_" + today_str
        else:
            new_name = current_name + "_updated_" + today_str

        new_guess_path = guess_path.with_name(new_name).with_suffix(guess_path.suffix)
        write_csv(new_guess_path, updated_guess_data)
    

if __name__ == '__main__':
    main()
