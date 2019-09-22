import random
from .lexigen import *
from .utils import *

class MarkovWordGenerator:
    common_words = ["the", "with", "in", "that", "not", "a", "an", "of", "for", "as", "like", "on", 'his', 'the',
                    'your', 'my', 'their']
    connector_choices = ['and', 'or', 'as', 'like', 'with']
    last_algorithms_used_to_reach_next_word = (None, None)
    previous_lines = []

    def __init__(self, previous_lines=[]):
        self.previous_lines = previous_lines

    def random_nonrhyme(self, previous_words: List[str], rhymable: bool = False) -> str:
        """Return a random result of a random function that hits Project Datamuse API (rhyme function excluded)

        This function is primarily designed for use by the poem_line_from_markov function, but it may have other
        interesting uses. This is why it is designed to take all the previous words of a line, rather than just the
        last word. Some words do not have many/any result values for some of these API calls because they are
        too weird "weird" input values (i.e. proper nouns or slang), so to ensure the function returns a value,
        the function will try different random functions from the lexigen module with different words until a word is
        found that is both not too similar to preceding words and not too similar to the last line's last word.

        :param previous_words: an ordered list of previous words of generated poem line
        :param rhymable: result must have a valid rhyme
        """
        result = None
        while result is None:
            # Randomly choose up to two algorithms the next word - one's repeated in this list for increased probability
            next_word_algorithms = [similar_sounding_word, similar_meaning_word, contextually_linked_word,
                                    frequently_following_word, frequently_following_word]
            nw_algorithms_copy = next_word_algorithms.copy()
            if self.last_algorithms_used_to_reach_next_word and self.last_algorithms_used_to_reach_next_word[0]:
                # Don't use the same algorithm for picking two successive words
                next_word_algorithms.remove(self.last_algorithms_used_to_reach_next_word[0])
            random_algorithm = random.choice(next_word_algorithms)
            # The frequently following function should always use the preceding word as input
            # But otherwise, this will randomly sometimes use a different preceding word as input
            input_word = previous_words[-1] if random.random() <= .75 else random.choice(previous_words)
            if random_algorithm != frequently_following_word and random.random() <= .25:
                if self.last_algorithms_used_to_reach_next_word and self.last_algorithms_used_to_reach_next_word[1]:
                    # Same goe for the 2nd algorithm used though this should be pretty rare
                    nw_algorithms_copy.remove(self.last_algorithms_used_to_reach_next_word[1])
                second_random_algorithm = random.choice(nw_algorithms_copy)
                possible_result = random_algorithm(input_word)
                possible_result = second_random_algorithm(possible_result) if possible_result else \
                    second_random_algorithm(input_word)
                self.last_algorithms_used_to_reach_next_word = (random_algorithm, second_random_algorithm)
            else:
                possible_result = random_algorithm(input_word)
                self.last_algorithms_used_to_reach_next_word = (random_algorithm, None)
            if possible_result and not too_similar(possible_result, previous_words) and \
                    not (len(self.previous_lines) > 0 and
                         too_similar(possible_result, self.previous_lines[-1].split(' '))
                         and not has_invalid_characters(possible_result)) and \
                    not (rhymable and not rhyme(possible_result)):
                # Is the word too similar to another word in the line or the previous line?
                # Does the word have numbers or spaces for some reason? (extremely rare)
                # If so, keep trying; otherwise exit the loop and return the word)
                result = possible_result
        return result

    def last_word_of_markov_line(self, previous_words: List[str], rhyme_with: Optional[str] = None,
                                 max_length: Optional[int] = None) -> str:
        """Get the last word of a poem line generated by the markov algorithm and optionally try to make it rhyme.

        :param previous_words: an ordered list of previous words of generated poem line
        :param rhyme_with: the last word of the last line of the poem, if it exists
        :param max_line_legnth: an upper limit in characters for the word
        """
        word = None
        if rhyme_with:
            word = word = rhyme(rhyme_with)
            # if the word is a common word or would be awkward to end a line with, keep trying
            while word in self.common_words or (max_length and len(word) > max_length):
                word = rhyme(rhyme_with)
            # But if there's no rhyme result try another method altogether
            if not word:
                while word is None or (max_length and len(word) > max_length) or word in self.common_words \
                        or too_similar(word, previous_words):
                    word = self.random_nonrhyme(previous_words)
        else:
            while word is None or (max_length and len(word) > max_length) or word in self.common_words \
                    or too_similar(word, previous_words):
                # Maybe revisit defaulting rhymable to true here
                word = self.random_nonrhyme(previous_words, rhymable=True)
        return word

    def nonlast_word_of_markov_line(self, previous_words: List[str], words_for_sampling: List[str] = []) -> str:
        """Get the next word of a poem line generated by the markov algorithm.

        :param previous_words: an ordered list of previous words of generated poem line
        :param param words_for_sampling: a list of other words to throw in to the poem.
        """
        word = None
        if previous_words[-1] in self.common_words:
            if random.random() >= .85 and len(previous_words) > 1:
                word = self.random_nonrhyme(previous_words[:-1])
            else:
                while word is None or too_similar(word, previous_words):
                    word = random.choice(words_for_sampling)
        else:
            threshold = .6 if len(words_for_sampling) else 1
            while word is None or too_similar(word,  previous_words):
                if random.random() > threshold:
                    if random.random() <= .5:
                        word = random.choice(self.connector_choices)
                    else:
                        word = random.choice(words_for_sampling)
                else:
                    word = self.random_nonrhyme(previous_words)
        return word
