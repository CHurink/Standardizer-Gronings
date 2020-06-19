#!/usr/bin/python3
import sys
import unicodedata
import mmap
import re
import collections

from fuzzywuzzy import fuzz
from string import punctuation

total_words = change_count = unidentified = tiebreaker_count = tietiebreaker_count = 0
with open('./InputData/train/alles.txt', 'r', encoding='utf-8', newline='\n') as alles:
    c = collections.Counter(alles.read().lower().split())

class SuggestionTree: #Class for Levenshtein measusures

    def __init__(self, delimiter=';', ignore_case=False):
        self.contents = dict()
        self.delimiter = delimiter
        self.ignore_case = ignore_case

    def add_word(self, word):
        if self.contains_word(word):
            return
        if self.ignore_case:
            word = word.lower()
        word = self.delimiter + word + self.delimiter
        current_dict = self.contents
        for letter in word:
            if letter not in current_dict:
                current_dict[letter] = dict()
            current_dict = current_dict[letter]

    def add_words(self, list_of_words):
        for word in list_of_words:
            self.add_word(word)

    def contains_word(self, word):
        if self.ignore_case:
            word = word.lower()
        word = self.delimiter + word + self.delimiter
        try:
            current_dict = self.contents
            for letter in word:
                current_dict = current_dict[letter]
            return True
        except KeyError:
            return False

    def suggest(self, word, depth=2):
        if self.ignore_case:
            word = word.lower()
        word = word + self.delimiter
        # Position, current word, part of the tree, depth
        vowels = ['a','e','i','o','u']
        paths = [(0, '', self.contents.get(self.delimiter, dict()), 0)]
        results = set()
        while paths:
            index, current_part, current_dict, current_depth = paths.pop()
            if index == len(word):
                continue
            next_letter = word[index]
            for letter_option in current_dict:
                if letter_option == next_letter:
                    # Correct path
                    if letter_option == self.delimiter:
                        # Result found
                        if current_depth <= depth:
                            results.add(current_part)
                    else:
                        # Going towards goal
                        paths.append((index+1,
                                      current_part+next_letter,
                                      current_dict[next_letter],
                                      current_depth))
                elif current_depth < depth:
                    # Insertion
                    if letter_option in vowels:
                        paths.append((index,
                                  current_part+letter_option,
                                  current_dict[letter_option],
                                  current_depth+0.5))
                    else:
                        paths.append((index,
                                  current_part+letter_option,
                                  current_dict[letter_option],
                                  current_depth+1))

                    # Substitution
                    if letter_option in vowels and next_letter in vowels:
                        paths.append((index+1,
                                  current_part+letter_option,
                                  current_dict[letter_option],
                                  current_depth+0.5))

                    else:
                        paths.append((index+1,
                                  current_part+letter_option,
                                  current_dict[letter_option],
                                  current_depth+1))
            if current_depth < depth:
                # Deletion
                if next_letter in vowels:
                    paths.append((index+1,
                              current_part,
                              current_dict,
                              current_depth+0.5))

                else:
                    paths.append((index+1,
                              current_part,
                              current_dict,
                              current_depth+1))
        if len(results) > 1:
            best = tiebreaker_fuz(word,results)
            results.clear()
            results.add(best)
        return results

def tiebreaker_fuz(word, results):#Final tiebreaker after Levenshtein fails
    global tiebreaker_count
    tiebreaker_count +=0.5
    best = ""
    best_ratio = 0
    best_count = 0
    for i in range(len(results)):
        option = results.pop()
        ratio = fuzz.ratio(word,option)
        if ratio > best_ratio:
            best_ratio = ratio
            best = option
        elif ratio == best_ratio:
            if c[option] > c[best]:
                best = option
            elif c[option] == c[best]:
                best =  best + '!'
    if best[-1] == '!':
        global tietiebreaker_count
        tietiebreaker_count +=0.5
        best = best[:-1]
    return best


levenshtein = SuggestionTree(ignore_case=True)
with open('woordenlijst.txt', 'r', encoding='utf-8', newline='\n') as woordenlijst:
    for line in woordenlijst:
        levenshtein.add_word(line.rstrip())

def wordlist_check(word): #Checks if word in wordlist and calls Levenshtein function
    global change_count
    global unidentified
    with open('woordenlijst.txt','r') as woordenlijst:
        with mmap.mmap(woordenlijst.fileno(), 0, access=mmap.ACCESS_READ) as s:
            if s.find(word.strip(punctuation).encode()) != -1:
                return word
            elif s.find(word.lower().strip(punctuation).encode()) != -1:
                return word
            elif len(levenshtein.suggest(word, depth=0)) != 0:
                change_count += 1
                return levenshtein.suggest(word, depth=0).pop()
            elif len(levenshtein.suggest(word, depth=0.5)) != 0:
                change_count += 1
                return levenshtein.suggest(word, depth=0.5).pop()
            elif len(levenshtein.suggest(word, depth=1)) != 0:
                change_count += 1
                return levenshtein.suggest(word, depth=1).pop()
            elif len(levenshtein.suggest(word, depth=1.5)) != 0:
                change_count += 1
                return levenshtein.suggest(word, depth=1.5).pop()
            elif len(levenshtein.suggest(word, depth=2)) != 0:
                change_count += 1
                return levenshtein.suggest(word, depth=2).pop()
            else:
                unidentified += 1
                return word

def strip_accents(word): #Removes all diacritics

    try:
        word = unicode(word, 'utf-8')
    except NameError:
        pass

    word = unicodedata.normalize('NFD', word)\
           .encode('ascii', 'ignore')\
           .decode("utf-8")

    return str(word)

def article_check(word): #Hardcoded article changer
    global change_count
    if word == 'een':
        word = 'n'
        change_count += 1
    elif word == 'Een':
        word = 'N'
        change_count += 1
    elif word == 'Het':
        word = 't'
        change_count += 1
    elif word == 'het':
        word = 't'
        change_count += 1
    elif word == 'd’':
        word = 'de'
        change_count += 1
    elif word == 'D’':
        word = 'De'
        change_count += 1
    elif word =='e':
        word = 'de'
        change_count += 1
    elif word =='E':
        word = 'De'
        change_count += 1
    else:
        word = word
    return word


def standardise(line,f): #Handles the sentences by combining the other functions
    global total_words
    standardised_line = ''
    line = re.findall(r"\w+|[^\w]", line, re.UNICODE)
    for word in line:
        total_words +=1
        if re.search(r"[^\w]|[\d+]", word):
            standardised_line = standardised_line +  word
        else:
            word = article_check(word)
            word = wordlist_check(word)
            standardised_line =  standardised_line + strip_accents(word)
    f.write(standardised_line[:-1]+ '\n')

def main(argv):
    dialect_text = sys.argv[1]
    filename = (dialect_text.split('/'))[-1]
    #Read file
    with open(dialect_text,'r') as d:
        try:
            #Open new file
            with open('./OutputData/output_' + filename , 'w') as f:
                #Work with open file
                for line in d.readlines():
                    standardise(line,f)
                f.close()
        #Error handling file creation
        except FileExistsError:
            d.close()
    #Feedback for user
    print('Total words:', total_words)
    print('Changed:',change_count)
    print('Unidentified:', unidentified)
    print('Needed a tiebreaker:', int(tiebreaker_count))
    print('Still unsolved after tiebreaker:', int(tietiebreaker_count))
if __name__ == '__main__':
    main(sys.argv)
