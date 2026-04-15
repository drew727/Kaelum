import os
import discord

tokens = list(os.environ("TOKEN_LIST"))
tokens.sort()

class TokenStore():
  def __init__(self):
    self.tokens = tokens
    self.current_token = self.tokens[0]

  def next_token(self):
    self.tokens.remove(self.current_token)
    self.current_token = self.tokens[0]
    return self.current_token
