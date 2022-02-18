import os
import pickle
import itertools

import pandas as pd
import numpy as np
from tqdm import tqdm


# modify these paths
DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
ALL_WORDS_ENTROPY_FILE = os.path.join(DATA_DIR, "df_all_words_entropy.pickle")
NEXT_GUESS_DICT_FILE = os.path.join(DATA_DIR, "next_guess_map.pickle")


#########################
# Game Basic Operations
#########################

def matching(guess, answer):
    """
    given the guessed word and answer, returns the matching result (pattern).

    guess:  string, a five-letter word.
    answer: string, a five-letter word.

    returns the matching pattern, a tuple of 5 elements.
    each element is composed of a single-letter string: 'C', 'M', or 'X'.

    - C (correct)   the guessed letter is in the word and in the correct spot.
    - M (misplaced) the guessed letter is in the word but in the wrong spot.
    - X (excluded)  the guessed letter is not in the word in any spot.

    matching mechanism:
    1. finding CORRECT spots
    2. search the not-correct letters, in the not-correct spots of the answer:
       1) if exist, the letter it is MISPLACED
       2) if the letter does not exist in the not-correct spots of the answer,
          the letter is EXCLUDED
    """

    not_used = [c for c in answer]
    matching_result = ['' for _ in range(5)]

    # CORRECT 🟩
    for i in range(5):
        if guess[i] == answer[i]:
            matching_result[i] = 'C'
            not_used.remove(guess[i])

    for i in range(5):
        if matching_result[i] == '':
            # MISPLACED 🟨
            if guess[i] in not_used:
                matching_result[i] = 'M'
                not_used.remove(guess[i])

            # EXCLUDED ⬜️
            else:
                matching_result[i] = 'X'

    return tuple(matching_result)


def pattern_to_emoji(pattern, print_it=True):
    """ convert the pattern to color emojis """

    color_map = {"C": "🟩", "M": "🟨", "X": "⬛️"}

    emojis = list()
    for pat in pattern:
        emojis.append(color_map.get(pat))

    if print_it:
        print(' '.join(emojis))
    else:
        return emojis


#########################
# Solver
#########################

def generate_all_patterns():
    """ get all the 3^5 wordle patterns (correct, misplaced, excluded) """
    return list(itertools.product(('C', 'M', 'X'), repeat=5))


def brute_solve(guess, answer, prev_result=None,
                num_attempt=1, to_print=True, show_zh=True):

    print(f'\n#{num_attempt} guess:') if to_print else ''
    if to_print:
        text = ' '.join(guess)
        text += ' ' + df_all_words[df_all_words['zhuyin'] ==
                                   guess].iloc[0]['word'] if show_zh else ''
        print(text)
    pattern = matching(guess, answer)
    pattern_to_emoji(pattern, print_it=to_print)

    # if found the answer
    if pattern == ('C', 'C', 'C', 'C', 'C'):
        print(f'\nsolved! attempt =', num_attempt) if to_print else ''
        return num_attempt

    # get possible answers that matched the pattern
    pat_id = all_patterns.index(pattern) + 1
    next_guess_options = all_next_guess[guess][f'p{pat_id}'].split(', ')
    matched_this_iter = df_answer[df_answer['zhuyin'].isin(
        next_guess_options)].sort_values(by=['entropy'], ascending=False)

    # find the intersection of possible answers of this & previous iteration
    if prev_result is not None:
        intersect = prev_result['zhuyin'][prev_result['zhuyin'].isin(
            matched_this_iter['zhuyin'])]
        result_this_iter = df_answer[df_answer['zhuyin'].isin(
            intersect)].sort_values(by=['entropy'], ascending=False)
    else:
        result_this_iter = matched_this_iter

    # select the next guess from pattern-matched possible answers
    next_guess = result_this_iter.iloc[0]['zhuyin']

    num_attempt = brute_solve(next_guess, answer, result_this_iter,
                              num_attempt+1, to_print)
    return num_attempt


#########################
# Simulator
#########################

def generate_first_guess(optimal=False):
    if optimal:
        return df_all_words.sort_values(by=['entropy'],
                                        ascending=False).iloc[0]['zhuyin']
    else:
        return df_all_words.sample().iloc[0]['zhuyin']


def generate_answer():
    return df_answer.sample().iloc[0]['zhuyin']


def play(first_guess=None, answer=None, optimal_guess=True,
         to_print=True, show_zh=True):
    """
    simulate the wordle game.

    optimal_guess: boolean. if first_guess is not provided, 
                   this variable controls the generate_first_guess() behavior.
    to_print:      boolean. show the solver step-by-step or not.
    show_zh:       boolean. if to_print is set to True, this variable determines
                   whether to print the Chinese of the guessed word or not.
    """

    if first_guess is None:
        first_guess = generate_first_guess(optimal=optimal_guess)
    if answer is None:
        answer = generate_answer()

    ans = answer
    ans += ' ' + df_answer[df_answer['zhuyin'] ==
                           answer].iloc[0]['word'] if show_zh else answer
    if to_print:
        print('注音dle:', ans)
    num_attempt = brute_solve(first_guess, answer,
                              to_print=to_print, show_zh=show_zh)

    return num_attempt


df_all_words = pd.read_pickle(ALL_WORDS_ENTROPY_FILE)
all_next_guess = pickle.load(open(NEXT_GUESS_DICT_FILE, 'rb'))

df_answer = df_all_words[df_all_words['in_answers'] == True]

all_patterns = generate_all_patterns()


if __name__ == '__main__':
    best_start = input('use the best first guess? (y/n) ')
    if best_start.lower() == 'y':
        play(optimal_guess=True)
    else:
        play(optimal_guess=False)
