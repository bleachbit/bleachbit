# markovify
# Copyright (c) 2015, Jeremy Singer-Vine
# Origin: https://github.com/jsvine/markovify
# MIT License: https://github.com/jsvine/markovify/blob/master/LICENSE.txt

import random
import operator
import bisect
import json

# Python3 compatibility
try: # pragma: no cover
    basestring
except NameError: # pragma: no cover
    basestring = str

BEGIN = "___BEGIN__"
END = "___END__"

def accumulate(iterable, func=operator.add):
    """
    Cumulative calculations. (Summation, by default.)
    Via: https://docs.python.org/3/library/itertools.html#itertools.accumulate
    """
    it = iter(iterable)
    total = next(it)
    yield total
    for element in it:
        total = func(total, element)
        yield total

class Chain(object):
    """
    A Markov chain representing processes that have both beginnings and ends.
    For example: Sentences.
    """
    def __init__(self, corpus, state_size, model=None):
        """
        `corpus`: A list of lists, where each outer list is a "run"
        of the process (e.g., a single sentence), and each inner list
        contains the steps (e.g., words) in the run. If you want to simulate
        an infinite process, you can come very close by passing just one, very
        long run.

        `state_size`: An integer indicating the number of items the model
        uses to represent its state. For text generation, 2 or 3 are typical.
        """
        self.state_size = state_size
        self.model = model or self.build(corpus, self.state_size)
        self.precompute_begin_state()

    def build(self, corpus, state_size):
        """
        Build a Python representation of the Markov model. Returns a dict
        of dicts where the keys of the outer dict represent all possible states,
        and point to the inner dicts. The inner dicts represent all possibilities
        for the "next" item in the chain, along with the count of times it
        appears.
        """

        # Using a DefaultDict here would be a lot more convenient, however the memory
        # usage is far higher.
        model = {}

        for run in corpus:
            items = ([ BEGIN ] * state_size) + run + [ END ]
            for i in range(len(run) + 1):
                state = tuple(items[i:i+state_size])
                follow = items[i+state_size]
                if state not in model:
                    model[state] = {}

                if follow not in model[state]:
                    model[state][follow] = 0

                model[state][follow] += 1
        return model

    def precompute_begin_state(self):
        """
        Caches the summation calculation and available choices for BEGIN * state_size.
        Significantly speeds up chain generation on large corpuses. Thanks, @schollz!
        """
        begin_state = tuple([ BEGIN ] * self.state_size)
        choices, weights = zip(*self.model[begin_state].items())
        cumdist = list(accumulate(weights))
        self.begin_cumdist = cumdist
        self.begin_choices = choices

    def move(self, state):
        """
        Given a state, choose the next item at random.
        """
        if state == tuple([ BEGIN ] * self.state_size):
            choices = self.begin_choices
            cumdist = self.begin_cumdist
        else:
            choices, weights = zip(*self.model[state].items())
            cumdist = list(accumulate(weights))
        r = random.random() * cumdist[-1]
        selection = choices[bisect.bisect(cumdist, r)]
        return selection

    def gen(self, init_state=None):
        """
        Starting either with a naive BEGIN state, or the provided `init_state`
        (as a tuple), return a generator that will yield successive items
        until the chain reaches the END state.
        """
        state = init_state or (BEGIN,) * self.state_size
        while True:
            next_word = self.move(state)
            if next_word == END: break
            yield next_word
            state = tuple(state[1:]) + (next_word,)

    def walk(self, init_state=None):
        """
        Return a list representing a single run of the Markov model, either
        starting with a naive BEGIN state, or the provided `init_state`
        (as a tuple).
        """
        return list(self.gen(init_state))

    def to_json(self):
        """
        Dump the model as a JSON object, for loading later.
        """
        return json.dumps(list(self.model.items()))

    @classmethod
    def from_json(cls, json_thing):
        """
        Given a JSON object or JSON string that was created by `self.to_json`,
        return the corresponding markovify.Chain.
        """

        if isinstance(json_thing, basestring):
            obj = json.loads(json_thing)
        else:
            obj = json_thing

        if isinstance(obj, list):
            rehydrated = dict((tuple(item[0]), item[1]) for item in obj)
        elif isinstance(obj, dict):
            rehydrated = obj
        else:
            raise ValueError("Object should be dict or list")

        state_size = len(list(rehydrated.keys())[0])

        inst = cls(None, state_size, rehydrated)
        return inst
