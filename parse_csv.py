import csv
import argparse as ap
import pathlib as plib
import sys
import copy

EVENT_STR = 'Event'
GENDER_STR = 'Gender'
CLASS_STR = 'Class'

GOLD_STR = 'Gold_Country'
SILVER_STR = 'Silver_Country'
BRONZE_STR = 'Bronze_Country'
MEDAL_STRS = [BRONZE_STR, SILVER_STR, GOLD_STR]
SCORE_STR = "Score"

CORRECT_GUESS_POINTS = 4

def handle_ties(event_result, event_guess_raw):
    event_guess = event_guess_raw.copy()

    if len(event_result[BRONZE_STR]) == 0:
        event_guess[SILVER_STR] = event_guess[SILVER_STR] + event_guess[BRONZE_STR]
        event_guess[BRONZE_STR] = []
    if len(event_result[SILVER_STR]) == 0:
        event_guess[GOLD_STR] = event_guess[GOLD_STR] + event_guess[SILVER_STR]
        event_guess[SILVER_STR] = []

    return event_guess

def lookup_medal_from_country(event_data, country):
    for medal in MEDAL_STRS:
        if country in event_data[medal]:
            return medal.replace("_Country", "")
    assert False, "Didn't find: " + country + " in " + str(event_data)

def score_event(event_result, event_guess_raw):
    assert event_result[EVENT_STR] == event_guess_raw[EVENT_STR]
    assert event_result[GENDER_STR] == event_guess_raw[GENDER_STR]
    assert event_result[CLASS_STR] == event_guess_raw[CLASS_STR]

    event_guess = handle_ties(event_result, event_guess_raw)

    incorrect_country_result_list = []
    incorrect_country_guess_list = []
    points = 0
    scoring_log = []

    # Handle perfect scores first, produce lists of incorrect guesses that can then be used to determine near guesses
    for medal_str in MEDAL_STRS:
        result_countries = event_result[medal_str].copy()
        guessed_countries = event_guess[medal_str].copy()


        if len(result_countries) == 0:
            assert(len(guessed_countries) == 0)
            continue
        
        for guessed_country in guessed_countries.copy():
            if guessed_country in result_countries:
                scoring_log.append("Scored " + str(CORRECT_GUESS_POINTS) + " points for perfect guess " + medal_str.replace("_Country", "") + " for " + guessed_country)
                points = points + CORRECT_GUESS_POINTS
                result_countries.remove(guessed_country)
                guessed_countries.remove(guessed_country)

        incorrect_country_result_list = incorrect_country_result_list + result_countries
        incorrect_country_guess_list = incorrect_country_guess_list + guessed_countries

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
                scoring_log.append("Scored 2 points for near guess " + incorrect_country_guess + " was guessed as " + lookup_medal_from_country(event_guess, incorrect_country_guess) + " but was actually " + lookup_medal_from_country(event_result, incorrect_country_guess))
                points = points + 2
                incorrect_country_result_list.remove(incorrect_country_guess)

    return [scoring_log, points]


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
        print("Score: " + str(score) + " from:\n" + "\n".join(scoring_log) + "\n")
        
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
        new_guess_path = guess_path.with_name(guess_path.stem + "_updated").with_suffix(guess_path.suffix)
        write_csv(new_guess_path, updated_guess_data)
    

if __name__ == '__main__':
    main()
