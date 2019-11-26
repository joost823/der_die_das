import csv
import random
import datetime
import argparse

LOG_FILE = 'attempts.csv'
GERMAN_DICTIONARY_FILE = 'german_dict.csv'  # modified from http://frequencylists.blogspot.com/2016/01/the-2980-most-frequently-used-german.html
KEYBOARD_INPUT_TO_ARTICLE = {'a': 'Der', 'r': 'Die', 's': 'Das'}
PRINT_EN_INPUT_KEY = 't'
QUIT_KEY = 'q'


class _Getch:
    """Gets a single character from standard input.  Does not echo to the screen.
    Source: https://stackoverflow.com/a/510364"""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    """Source: https://stackoverflow.com/a/510364"""
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    """Source: https://stackoverflow.com/a/510364"""
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()


class bcolors:
    """Source: https://stackoverflow.com/a/287944"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Word:
    getch = _Getch()

    def __init__(self, id, D, EN, article):
        self.D = D
        self.EN = EN
        self.id = id
        self.article = article
        self.prev_attempts = []


    def __repr__(self):
        return(f'{self.article} {self.D} -- {self.probability} {self.prev_attempts}')

    def calc_probability(self):
        self.probability = 1
        for n, was_attempt_correct in enumerate(self.prev_attempts[-4:]):
            if not was_attempt_correct:
                self.probability *= (n + 2)

    def play(self):
        print(self.D, end="\r")
        while True:
            single_letter_input = self.getch()
            if single_letter_input == PRINT_EN_INPUT_KEY:
                print(f'{self.D} means {self.EN}', end='\r')
            if single_letter_input in KEYBOARD_INPUT_TO_ARTICLE:
                inputted_article = KEYBOARD_INPUT_TO_ARTICLE[single_letter_input]
                break
            if single_letter_input == QUIT_KEY:
                exit('\n\nExiting...')
        is_correct_article = inputted_article == self.article
        if is_correct_article:
            print(f'{bcolors.OKGREEN}{self.article} {self.D} {bcolors.ENDC}',)
        else:
            print(f'{bcolors.FAIL}{self.article} {self.D} {bcolors.ENDC}')

        self.prev_attempts.append(is_correct_article)
        self.calc_probability()

        with open(LOG_FILE, 'a') as fout:
            writer = csv.writer(fout)
            writer.writerow([self.id,
                             self.D,
                             self.EN,
                             self.article,
                             inputted_article,
                             is_correct_article,
                             datetime.date.today(),
                             datetime.datetime.now().time()])


def filter_dicty_by_command_line_args(dicty):
    probabilities = [dicty[id].probability for id in dicty.keys()]
    max_probability = max(probabilities)

    starting_letters = [dicty[id].D[0] for id in dicty.keys()]

    def check_range(value):
        try:
            start, stop = value.split(':')
            start =  int(start)
            stop = int(stop)
            if len([key for key in dicty.keys() if key >= start and key <= stop]) == 0:
                raise Exception('No words within this word id range')
        except Exception:
            raise argparse.ArgumentTypeError(f'please input word id range as follows 123:345')

        return start, stop


    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--range', help='an lowerlimit:upperlimit range of word_ids to focus on', required=False, type=check_range)
    parser.add_argument('-p', '--probability', help='only pick words with at least this probability', required=False, type=int, choices=range(0, max_probability))
    parser.add_argument('-l', '--letter', help='only pick words starting with this letter (in Capital)', required=False, choices=list(set(starting_letters)))
    args = parser.parse_args()
    if args.range:
        dicty = {k: dicty[k] for k in dicty.keys() if k >= args.range[0] and k <= args.range[1]}
    if args.probability:
        dicty = {k: dicty[k] for k in dicty.keys() if dicty[k].probability >= args.probability}
    if args.letter:
        dicty = {k: dicty[k] for k in dicty.keys() if dicty[k].D[0] == args.letter}
    return dicty


def main():
    dicty = parse_dictionary_file()
    add_log_file_info_to_dict(dicty)

    for word_id, word in dicty.items():
        word.calc_probability()

    dicty = filter_dicty_by_command_line_args(dicty)

    print(f'starting game with a total of {len(dicty)} words')

    while True:
        probabilities_list = [dicty[id].probability for id in dicty.keys()]
        word_id = random.choices(list(dicty.keys()), weights=probabilities_list)[0]
        word = dicty[word_id]
        word.play()


def add_log_file_info_to_dict(dicty):
    with open(LOG_FILE) as fin:
        reader = csv.reader(fin)
        next(reader)  # skip header
        for n, row in enumerate(reader):
            word_id = int(row[0])
            was_correct = row[5] == 'True'
            if word_id in dicty:
                dicty[word_id].prev_attempts.append(was_correct)


def parse_dictionary_file():
    dicty = {}

    with open(GERMAN_DICTIONARY_FILE) as csvfile:
         reader = csv.reader(csvfile, delimiter='\t')
         for row in reader:
             id = int(row[0])
             english_word = row[1].strip()
             german_word = row[2].strip()
             article = german_word.split(' ')[0]
             german_word_without_article = ' '.join(german_word.split(' ')[1:])
             if german_word_without_article:
                 word = Word(id, german_word_without_article, english_word, article)
                 dicty[id] = word

    return dicty


if __name__ == '__main__':
    main()
