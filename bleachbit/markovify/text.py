# markovify
# Copyright (c) 2015, Jeremy Singer-Vine
# Origin: https://github.com/jsvine/markovify
# MIT License: https://github.com/jsvine/markovify/blob/master/LICENSE.txt

import re
import json
import random
from .splitters import split_into_sentences
from .chain import Chain, BEGIN, END
# BleachBit does not use unidecode
#from unidecode import unidecode

DEFAULT_MAX_OVERLAP_RATIO = 0.7
DEFAULT_MAX_OVERLAP_TOTAL = 15
DEFAULT_TRIES = 10

class ParamError(Exception):
    pass

class Text(object):

    def __init__(self, input_text, state_size=2, chain=None, parsed_sentences=None, retain_original=True):
        """
        input_text: A string.
        state_size: An integer, indicating the number of words in the model's state.
        chain: A trained markovify.Chain instance for this text, if pre-processed.
        parsed_sentences: A list of lists, where each outer list is a "run"
              of the process (e.g. a single sentence), and each inner list
              contains the steps (e.g. words) in the run. If you want to simulate
              an infinite process, you can come very close by passing just one, very
              long run.
        """
        can_make_sentences = parsed_sentences is not None or input_text is not None
        self.retain_original = retain_original and can_make_sentences
        self.state_size = state_size

        if self.retain_original:
            # not used in BleachBit
            pass
        else:
            if not chain:
                # not used in BleachBit
                pass
            self.chain = chain or Chain(parsed, state_size)

    def to_dict(self):
        """
        Returns the underlying data as a Python dict.
        """
        # not used in BleachBit
        pass

    def to_json(self):
        """
        Returns the underlying data as a JSON string.
        """
        # not used in BleachBit
        pass

    @classmethod
    def from_dict(cls, obj, **kwargs):
        return cls(
            None,
            state_size=obj["state_size"],
            chain=Chain.from_json(obj["chain"]),
            parsed_sentences=obj.get("parsed_sentences")
        )

    @classmethod
    def from_json(cls, json_str):
        # not used in BleachBit
        pass

    def sentence_split(self, text):
        """
        Splits full-text string into a list of sentences.
        """
        return split_into_sentences(text)

    def sentence_join(self, sentences):
        """
        Re-joins a list of sentences into the full text.
        """
        return " ".join(sentences)

    word_split_pattern = re.compile(r"\s+")
    def word_split(self, sentence):
        """
        Splits a sentence into a list of words.
        """
        return re.split(self.word_split_pattern, sentence)

    def word_join(self, words):
        """
        Re-joins a list of words into a sentence.
        """
        return " ".join(words)

    def test_sentence_input(self, sentence):
        """
        A basic sentence filter. This one rejects sentences that contain
        the type of punctuation that would look strange on its own
        in a randomly-generated sentence.
        """
        # not used in BleachBit
        pass

    def generate_corpus(self, text):
        """
        Given a text string, returns a list of lists; that is, a list of
        "sentences," each of which is a list of words. Before splitting into
        words, the sentences are filtered through `self.test_sentence_input`
        """
        # not used in BleachBit
        pass

    def test_sentence_output(self, words, max_overlap_ratio, max_overlap_total):
        """
        Given a generated list of words, accept or reject it. This one rejects
        sentences that too closely match the original text, namely those that
        contain any identical sequence of words of X length, where X is the
        smaller number of (a) `max_overlap_ratio` (default: 0.7) of the total
        number of words, and (b) `max_overlap_total` (default: 15).
        """
        # not used in BleachBit
        pass


    def make_sentence(self, init_state=None, **kwargs):
        """
        Attempts `tries` (default: 10) times to generate a valid sentence,
        based on the model and `test_sentence_output`. Passes `max_overlap_ratio`
        and `max_overlap_total` to `test_sentence_output`.

        If successful, returns the sentence as a string. If not, returns None.

        If `init_state` (a tuple of `self.chain.state_size` words) is not specified,
        this method chooses a sentence-start at random, in accordance with
        the model.

        If `test_output` is set as False then the `test_sentence_output` check
        will be skipped.

        If `max_words` is specified, the word count for the sentence will be
        evaluated against the provided limit.
        """
        tries = kwargs.get('tries', DEFAULT_TRIES)
        mor = kwargs.get('max_overlap_ratio', DEFAULT_MAX_OVERLAP_RATIO)
        mot = kwargs.get('max_overlap_total', DEFAULT_MAX_OVERLAP_TOTAL)
        test_output = kwargs.get('test_output', True)
        max_words = kwargs.get('max_words', None)

        if init_state != None:
            prefix = list(init_state)
            for word in prefix:
                if word == BEGIN:
                    prefix = prefix[1:]
                else:
                    break
        else:
            prefix = []

        for _ in range(tries):
            words = prefix + self.chain.walk(init_state)
            if max_words != None and len(words) > max_words:
                continue
            if test_output and hasattr(self, "rejoined_text"):
                if self.test_sentence_output(words, mor, mot):
                    return self.word_join(words)
            else:
                return self.word_join(words)
        return None

    def make_short_sentence(self, max_chars, min_chars=0, **kwargs):
        """
        Tries making a sentence of no more than `max_chars` characters and optionally
        no less than `min_chars` charcaters, passing **kwargs to `self.make_sentence`.
        """
        tries = kwargs.get('tries', DEFAULT_TRIES)

        for _ in range(tries):
            sentence = self.make_sentence(**kwargs)
            if sentence and len(sentence) <= max_chars and len(sentence) >= min_chars:
                return sentence

    def make_sentence_with_start(self, beginning, strict=True, **kwargs):
        """
        Tries making a sentence that begins with `beginning` string,
        which should be a string of one to `self.state` words known
        to exist in the corpus.
        
        If strict == True, then markovify will draw its initial inspiration
        only from sentences that start with the specified word/phrase.

        If strict == False, then markovify will draw its initial inspiration
        from any sentence containing the specified word/phrase.

        **kwargs are passed to `self.make_sentence`
        """
        split = tuple(self.word_split(beginning))
        word_count = len(split)

        if word_count == self.state_size:
            init_states = [ split ]

        elif word_count > 0 and word_count < self.state_size:
            if strict:
                init_states = [ (BEGIN,) * (self.state_size - word_count) + split ]

            else:
                init_states = [ key for key in self.chain.model.keys()
                    # check for starting with begin as well ordered lists
                    if tuple(filter(lambda x: x != BEGIN, key))[:word_count] == split ]

                random.shuffle(init_states)
        else:
            err_msg = "`make_sentence_with_start` for this model requires a string containing 1 to {0} words. Yours has {1}: {2}".format(self.state_size, word_count, str(split))
            raise ParamError(err_msg)

        for init_state in init_states:
            output = self.make_sentence(init_state, **kwargs)
            if output is not None:
                return output

        return None

    @classmethod
    def from_chain(cls, chain_json, corpus=None, parsed_sentences=None):
        """
        Init a Text class based on an existing chain JSON string or object
        If corpus is None, overlap checking won't work.
        """
        chain = Chain.from_json(chain_json)
        return cls(corpus or None, parsed_sentences=parsed_sentences, state_size=chain.state_size, chain=chain)


class NewlineText(Text):
    """
    A (usable) example of subclassing markovify.Text. This one lets you markovify
    text where the sentences are separated by newlines instead of ". "
    """
    def sentence_split(self, text):
        return re.split(r"\s*\n\s*", text)
