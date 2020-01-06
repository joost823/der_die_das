import csv
import random
import datetime
import argparse
import re
import subprocess
import os

LOG_FILE = 'attempts.csv'
GERMAN_DICTIONARY_FILE = 'german_dict.csv'  # modified from http://frequencylists.blogspot.com/2016/01/the-2980-most-frequently-used-german.html
KEYBOARD_INPUT_TO_ARTICLE = {'a': 'Der', 's': 'Die', 'd': 'Das'}
TRANSLATE_KEY = 'f'
QUIT_KEY = 'q'


class Word:
    def __init__(self, word_id, D, EN, article):
        self.D = D
        self.EN = EN
        self.id = word_id
        self.article = article
        self.prev_attempts = []

    def calc_probability(self):
        """The probabilily of a word being chosen to be played is calculated
        using the correctness of the previous 4 attempts. Recent wrong attempts
        will increase this probability (more or less) exponentially"""
        self.probability = 1
        for n, was_attempt_correct in enumerate(self.prev_attempts[-4:]):
            if not was_attempt_correct:
                self.probability *= (n + 2)

    def play(self):
        """Play a round where you have to enter the correct article. A single
        keypress is read and 5 keys correspond to 1) der, 2) die, 3) das, 4)
        displaying the English meaning of the word or 5) quitting the game.
        Each attempt is logged and will be used for future rounds/games"""

        # Present the word without the article
        print(self.D, end="\r")

        # Loop until a valid key is pressed
        while True:
            single_letter_input = getch()

            # Quit
            if single_letter_input == QUIT_KEY:
                exit('\n\nExiting...')

            # Print English meaning of the word
            if single_letter_input == TRANSLATE_KEY:
                print(f'{self.D} means {self.EN}', end='\r')

            # A letter corresponding to a German article was typed
            if single_letter_input in KEYBOARD_INPUT_TO_ARTICLE:
                inputted_article = KEYBOARD_INPUT_TO_ARTICLE[single_letter_input]
                break

        # Print the word + correct article and colour by the corectness of the users input
        is_correct_article = inputted_article == self.article
        if is_correct_article:
            print(f'{bcolors.OKGREEN}{self.article} {self.D} {bcolors.ENDC}',)
        else:
            print(f'{bcolors.FAIL}{self.article} {self.D} {bcolors.ENDC}')

        # Update previous attempts and probability after the current attempt
        self.prev_attempts.append(is_correct_article)
        self.calc_probability()

        # Log the attempts, including date, time and correctness
        with open(LOG_FILE, 'a', newline='', encoding='utf-8') as fout:
            writer = csv.writer(fout)
            writer.writerow([self.id,
                             self.D,
                             self.EN,
                             self.article,
                             inputted_article,
                             is_correct_article,
                             datetime.date.today(),
                             datetime.datetime.now().time()])


class bcolors:
    """Bash/command line colours. Source: https://stackoverflow.com/a/287944"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def main():
    # parse the file containig German words and articles
    word_id_to_word_dict = parse_dictionary_file()

    # parse the log file to add info regarding prev. games
    add_log_file_info_to_dict(word_id_to_word_dict)

    # filter to optionally reduce the size of the practice set
    word_id_to_word_dict = filter_word_id_to_word_dict_by_command_line_args(word_id_to_word_dict)

    print(f'Starting game with a total of {len(word_id_to_word_dict)} words\n\n'
        + '\n'.join([f'Press {k} for {v}' for k, v in KEYBOARD_INPUT_TO_ARTICLE.items()]) + '\n'
        + f'Press {TRANSLATE_KEY} to show the English translation of the word\n'
        + f'Press {QUIT_KEY} to quit\n')

    while True:
        probabilities_list = [word_id_to_word_dict[id].probability for id in word_id_to_word_dict.keys()]
        word_id = random.choices(list(word_id_to_word_dict.keys()), weights=probabilities_list)[0]
        word = word_id_to_word_dict[word_id]
        word.play()


def filter_word_id_to_word_dict_by_command_line_args(word_id_to_word_dict):
    """optionally filter the word dictionary by several types of filters provided as cmd arguments by the user"""

    def check_range(value):
        """check if the range arguments is passed as StartWordID:StopWordId"""
        if not re.search(r"^[0-9]+:[0-9]+$", value):
            raise argparse.ArgumentTypeError(f'please input word id range as follows 123:345')
        start, stop = value.split(':')

        return int(start), int(stop)

    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--range', help='an lowerlimit:upperlimit range of word_ids to focus on', required=False, type=check_range)
    parser.add_argument('-p', '--probability', help='only pick words with at least this probability', required=False, type=int)
    parser.add_argument('-l', '--letter', help='only pick words starting with this letter', required=False)
    args = parser.parse_args()

    # if providing the range argument, only keep words within a certain word_id range
    if args.range:
        word_id_to_word_dict = {k: v for k, v in word_id_to_word_dict.items() if k >= args.range[0] and k <= args.range[1]}

    # if providing the probabilily argument, only keep words with at least this probability
    if args.probability:
        word_id_to_word_dict = {k: v for k, v in word_id_to_word_dict.items() if v.probability >= args.probability}

    # if providing the letter argument, only keep words starting with this letter
    if args.letter:
        word_id_to_word_dict = {k: v for k, v in word_id_to_word_dict.items() if v.D[0].lower() == args.letter.lower()}

    if len(word_id_to_word_dict) == 0:
        exit('No words found after filtering by these values!')

    return word_id_to_word_dict


def add_log_file_info_to_dict(word_id_to_word_dict):
    """add information regarding correctness of previous attempts to the Word
       objects using the log file of previous attempts"""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, encoding='utf-8') as fin:
            reader = csv.reader(fin)
            for n, row in enumerate(reader):
                word_id = int(row[0])
                was_correct = row[5] == 'True'
                if word_id in word_id_to_word_dict:
                    word_id_to_word_dict[word_id].prev_attempts.append(was_correct)

    # After prev. attempts were added, calculate the probabily of choosing this word
    for word_id, word in word_id_to_word_dict.items():
        word.calc_probability()


def parse_dictionary_file():
    """add the Word instances of the words in the German dictionary file to a
    python dictionary"""
    word_id_to_word_dict = {}

    with open(GERMAN_DICTIONARY_FILE, encoding='utf-8') as csvfile:
         reader = csv.reader(csvfile, delimiter='\t')
         for row in reader:
             id = int(row[0])
             english_word = row[1].strip()
             german_word = row[2].strip()
             article = german_word.split(' ')[0]
             german_word_without_article = ' '.join(german_word.split(' ')[1:])
             if german_word_without_article:
                 word = Word(id, german_word_without_article, english_word, article)
                 word_id_to_word_dict[id] = word

    return word_id_to_word_dict


def _find_getch():
    """Returns a function which returns one char of user input.
    Source: https://stackoverflow.com/a/21659588"""
    try:
        import termios
    except ImportError:
        # Non-POSIX. Return msvcrt's (Windows') getch.
        import msvcrt

        # due to a bug (https://stackoverflow.com/a/51524239), windows console
        # won't show colours w/o calling subprocess.call
        subprocess.call('', shell=True)
        return msvcrt.getwch

    # POSIX system. Create and return a getch that manipulates the tty.
    import sys, tty
    def _getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    return _getch


getch = _find_getch()


if __name__ == '__main__':
    main()
