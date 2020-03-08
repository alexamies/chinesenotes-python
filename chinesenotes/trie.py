# -*- coding: utf-8 -*-
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Tools for processing of prefixes of dictionary entries

References:
1. Crochemore, M, Hancart, C, and Lecroq, T, 2007, Algorithms on Strings,
   Cambridge University Press, e-book.
2. Sipser, M 2012, Introduction to the Theory of Computation, Cengage Learning,
   e-book.
3. Stephens, R 2019, Essential Algorithms: A Practical Approach to Computer
   Algorithms Using Python and C#, John Wiley & Sons, Kindle ed.
"""

from typing import List, Set, Union

class State:
  """State of a finite state machine"""

  def __init__(self, value: int, accepting: bool):
    """Constructor
    Params:
      value: A primitive value acting as a label for the state
      accepting: A Boolean value, true if accepting
    """
    self._value = value
    self._accepting = accepting

  @property
  def accepting(self):
    """True if the state is accepting for the FSM"""
    return self._accepting

  @accepting.setter
  def accepting(self, accepting: bool):
    """Set to True if the state is accepting for the FSM"""
    self._accepting = accepting

  @property
  def value(self):
    """The value of the state"""
    return self._value

  def __repr__(self):
    return '{}'.format(self.value)


class Transition:
  """State transition in a non-deterministic finite state machine"""

  def __init__(self, start: State, inval: str, next_states: Set[State]):
    """Constructor
    Params:
      start: The starting state of a transition
      inval: The input symbol of a transition
      next_states: The set of next state of a transition (0 or 1)
    """
    self._start = start
    self._next_states = next_states
    self._inval = inval

  def add_next_state(self, next_state: State):
    """ Adds a next state to the transition table"""
    self._next_states.add(next_state)

  @property
  def inval(self) -> str:
    """The input symbol of a transition"""
    return self._inval

  @property
  def next_states(self) -> Set[State]:
    """The next state of a transition"""
    return self._next_states

  @property
  def start(self):
    """The starting state of a transition"""
    return self._start

  def __repr__(self):
    return '{} --{}-> {}'.format(self.start, self.inval, self.next_states)

class FSMException(Exception):
  """Exception thrown if the FSM does not know how to proceed

  This will be thrown if the FSM tries to recognize a string but encounters
  multiple next states in a transition function.
  """


class FSM:
  """Implements a non-deterministic finite state machine.

  A finite state machine is also known as an automaton. It is non-deterministic
  to allow for easier construction and for early rejection if the transition
  function leads to an empty set of next nodes. However, the implementation does
  not know how to recognizes transitions that return more than one state.
  Transitions for empty are not allowed.

  References:
    1. Sipser 2012, pp. 31-47
    2. Stephens 2019, ch. 15
  """
  def __init__(self):
    self._trans_table = {}
    self._start = State(0, False)
    self._states = {self._start}
    self._alphabet = set()

  @property
  def alphabet(self) -> Set:
    """The set of symbols in the alphabet"""
    return self._alphabet

  @property
  def accepting_states(self) -> Set:
    """The set of accepting states"""
    states = set()
    for state in self._states:
      if state.accepting:
        states.add(state)
    return states

  def add_transitions(self, start: State, symbol: str, next_states: Set[State]):
    """Creates a new transition, adding it to transition table.

    Params:
      start: Start node
      symbol: Symbol leading to the state transition
      next_states: Set of next states
    Raise: FSMException if symbol is an empty string
    """
    trans = Transition(start, symbol, next_states)
    key = '{}{}'.format(start.value, symbol)
    if symbol == '':
      raise FSMException('Transitions based on empty strings are not allowed, '
                         'state: {}'.format(start))
    if key in self._trans_table:
      print('Transition from state {} with {} already exists'.format(start,
                                                                     symbol))
      trans = self._trans_table[key]
      for state in next_states:
        trans.add_next_state(state)
    else:
      self._trans_table[key] = trans
      self._alphabet.add(symbol)

  def add_transition(self, start: State, symbol: str, next_state: State):
    """Creates a new transition, adding it to transition table.

    Params:
      start: Start node
      symbol: Symbol leading to the state transition
      next_state: The next state
    Raise: FSMException if symbol is an empty string
    """
    self.add_transitions(start, symbol, {next_state})

  def new_state(self, accepting=False) -> State:
    """Creates a new state, adding it to the list of states"""
    state = State(len(self._states), accepting)
    self._states.add(state)
    # print('new_state {}: {}'.format(state, self._states))
    return state

  def recognizes(self, to_test: str) -> bool:
    """Tests whether the given string is recognized by the FSM

    If no transition then for part of the string then it will reject it
    immediately.

    Param:
      to_test: the string to test
    Return: True if the string is recognized by the FSM
    Raise: FSMException if multiple next states are found for any state
    """
    state = self._start
    for character in to_test:
      next_states = self.transition(state, character)
      # print('recognizes c {}, next_states {}'.format(c, next_states))
      if len(next_states) == 0: # If no transition then reject immediately
        return False
      if len(next_states) > 1:
        # don't know what to do
        FSMException('Encountered multiple states for state {}, symbol {}, '
                     'next: {}'.format(state, character, next_states))
      else:
        state = next(iter(next_states))
    return state.accepting

  @property
  def start(self) -> State:
    """The start node"""
    return self._start

  @property
  def states(self) -> Set:
    """The set of states"""
    return self._states

  def transition(self, state: State, inval: str) -> Set[State]:
    """Transition function to read input and give next state or None

    This implementation of a FSM is non-deterministic in the sense that it
    allows for a transition from a state for a a given symbol to multiple
    next states or an empty set. If no transition is found an empty set will be
    returned.

    Param:
      state: The current state
      inval: The input symbol to be read
    Return: The set of next state an empty if there is no transition table entry
    """
    #print('transition state: {}, inval: {}'.format(state, inval))
    key = str(state.value) + str(inval)
    if key in self._trans_table:
      return self._trans_table[key].next_states
    return set()

  @property
  def transitions(self) -> Set:
    """The set of state transitions"""
    return self._trans_table

  def __repr__(self):
    return """
      Alphabet: {}
      States: {}
      Start state: {}
      Accepting states: {}
      Transition table: {}'
      """.format(self._alphabet,
                 self._states,
                 self._start,
                 self.accepting_states,
                 self._trans_table)


class Trie(FSM):
  """Recognizes a set of words in a dictionary by following prefixes in an FSM

    Implements the trie building algorithm described in Crochemore,
    Hancart= and Lecroq (2007, p. 56). More details about tries discussed in
    Stephens 2019, ch. 15.

    Example use:

    trie = Trie()
    dict_entries = ['zha', 'zhang', 'zhan', 'zhao', 'fang']
    trie.build(dict_entries)
    prefix = 'zh'
    terms = trie.find_with_prefix(prefix)
    print('Prefix {} has terms {}'.format(prefix, terms))

    Output:
    Prefix zh has terms ['zha', 'zhan', 'zhao', 'zhang']
  """

  def __init__(self):
    """Constructor

    Params:
      alphabet: The alphabet for the trie
    """
    FSM.__init__(self)

  def build(self, dict_entries: List[str]):
    """Builds a dictionary matching trie

    Params:
      dict_entries: A list of dictionary entries
    """
    for term in dict_entries:
      state = self.start
      for character in term:
        next_states = self.transition(state, character)
        if len(next_states) == 0:
          new_state = self.new_state()
          self.add_transition(state, character, new_state)
        else:
          new_state = next(iter(next_states))
        state = new_state
      state.accepting = True

  def find_with_prefix(self, prefix: str) -> List[str]:
    """Finds the all the dictionary terms with the given prefix

    Params:
      prefix: the string to test
    Return: dictionary terms with the given prefix
    Raises: FSMException if multiple states encountered following the FSM
    """
    prefix_state = self._read_prefix(prefix)
    #print('Prefix {} has state {}'.format(prefix, prefix_state))
    terms = [] # Terms to return
    if prefix_state and prefix_state.accepting:
      terms.append(prefix)
    stack = []
    stack.append((prefix_state, prefix))
    while len(stack) > 0:
      # Remove next candidate state and prefix from stack
      (state, candidate_term) = stack.pop()
      for character in self.alphabet:
        next_term = '{}{}'.format(candidate_term, character)
        next_states = self.transition(state, character)
        for next_state in next_states:
          if next_state.accepting:
            terms.append(next_term)
          stack.append((next_state, next_term))
    return terms

  def _read_prefix(self, prefix: str) -> Union[State, None]:
    """Finds the states for the given prefix

    Param:
      prefix: the string to test
    Return: the states found by following the FSM or None
    Raises: FSMException if multiple states encountered
    """
    state = self._start
    for character in prefix:
      next_states = self.transition(state, character)
      # print('read_prefix c {}, next_states {}'.format(c, next_states))
      if len(next_states) == 0: # If no transition then return immediately
        return None
      if len(next_states) > 1:
        FSMException('Encountered multiple states for state {}, symbol {}, '
                     'next: {}'.format(state, character, next_states))
      else:
        state = next(iter(next_states))
    return state

def main():
  """Command line entry pont for example usage"""
  trie = Trie()
  dict_entries = ['zha', 'zhang', 'zhan', 'zhao', 'fang']
  trie.build(dict_entries)
  prefix = 'zh'
  terms = trie.find_with_prefix(prefix)
  print('Prefix {} has terms {}'.format(prefix, terms))

if __name__ == '__main__':
  main()
