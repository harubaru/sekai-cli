from transformers import AutoTokenizer
from .sukima_api import Sukima_API
from .editor import edit_multiline
from .utils import *
from .prefix import prefix
import json

tokenizer = AutoTokenizer.from_pretrained('gpt2')

banner = """
  S E K A I

  ⠀⠀⣤⠀⢰⡆⠀⣴⠀⠀⠀⢠⣤⣤⣤⣤⣤⣤⠀⠀
  ⢀⣀⣿⣀⣸⣇⣀⣿⣀⡀⠀⢸⡧⠤⣿⠤⠤⣿⠀⠀
  ⠈⠉⣿⠉⢹⡏⠉⣿⠉⠁⠀⢸⣧⣤⣿⣤⣤⣿⠀⠀
  ⠀⠀⣿⠀⢸⡧⠤⣿⠀⠀⢀⣠⡶⣏⠀⠈⣷⣦⣄⠀
  ⠀⠀⣿⣀⣈⣁⣀⣈⣀⠀⠈⠁⣰⡏⠀⠀⣿⠀⠉⠀
  ⠀⠀⠿⠉⠉⠉⠉⠉⠉⠁⠀⠺⠋⠀⠀⠀⠟⠀⠀⠀

  Story-telling with Lit-6B

  https://github.com/harubaru/sekai
"""

def list_items(items):
    while True:
        try:
            for i in range(len(items)):
                print(f"{i + 1} >", items[i])
            option = int(input('Input a number: '))
            if option > len(items) + 1:
                return -1
            else:
                return option
        except ValueError:
            return -2

# function returns settings, but with changed values
def list_settings(labels, settings):
    while True:
        try:
            for i in range(len(settings)):
                print(f"{i + 1} >", labels[i], settings[i])
            option = int(input('Input a number: '))
            if option > len(settings) + 1:
                raise ValueError
            else:
                new_setting = input(f"Input new value for {labels[option - 1]}: ")
                settings[option - 1] = new_setting
                return settings
        except ValueError:
            return settings


class Story:
    def __init__(self):
        self.title = ''
        self.author1 = ''
        self.author2 = ''
        self.memory = ''
        self.authors_note = ''
        self.entries = []
        self.lore = []

    def action(self, text, aitext=0):
        self.entries.append((text, aitext))
    
    def undo(self):
        if len(self.entries) > 0:
            self.entries.pop()

    def save(self, filename):
        with open(filename, 'w') as f:
            fmt = {
                'title': self.title,
                'author1': self.author1,
                'author2': self.author2,
                'memory': self.memory,
                'authors_note': self.authors_note,
                'entries': self.entries,
                'lore': self.lore
            }
            f.write(json.dumps(fmt))

    def context(self, max_tokens=1024):
        needed_tokens = len(tokenizer.encode(self.memory + self.authors_note))
        context_str = ''
        context_str += self.memory
        story_str = ''
        if not self.entries:
            context_str = '***\n'
        for i, v in enumerate(self.entries):
            story_str += v[0]
        if story_str:
            ends_with_newline = story_str[-1] == '\n'
        else:
            ends_with_newline = False
        x = story_str.splitlines()
        if self.authors_note:
            x.insert(-3, self.authors_note)
        story_str = ''
        for i in x:
            story_str += i + '\n'
        if not ends_with_newline:
            story_str = story_str[:-1]
        story_tokens = tokenizer.encode(story_str)
        if len(story_tokens) > max_tokens-needed_tokens:
            context_str += tokenizer.decode(story_tokens[:max_tokens-needed_tokens])
        else:
            context_str += story_str
        return context_str
    
    # return story formatted for console
    def get_formatted(self, truncate_last=False):
        story_str = ''
        entries = self.entries
        if truncate_last:
            entries = self.entries[:-1]
        for i, v in enumerate(entries):
            if v[1] == 0:
                # bolden user text
                story_str += '\033[1m' + v[0] + '\033[0m'
            elif v[1] == 1:
                story_str += v[0]
            elif v[1] == 2:
                # dim altered text
                story_str += '\033[2m' + v[0] + '\033[0m'
        if story_str:
            ends_with_newline = story_str[-1] == '\n'
        else:
            ends_with_newline = False
        x = story_str.splitlines()
        story_str = ''
        for i in x:
            story_str += '    ' + i + '\n'
        if not ends_with_newline:
            story_str = story_str[:-1]
        return story_str

    def load(self, filename):
        with open(filename, 'r') as f:
            data = json.load(f)
            if 'title' in data:
                self.title = data['title']
            if 'author1' in data:
                self.author1 = data['author1']
            if 'author2' in data:
                self.author2 = data['author2']
            if 'memory' in data:
                self.memory = data['memory']
            if 'authors_note' in data:
                self.authors_note = data['authors_note']
            if 'entries' in data:
                self.entries = data['entries']
            if 'lore' in data:
                self.lore = data['lore']

class App:
    def __init__(self):
        self.api = None
        self.current_story = None
        self.story_mode = False
        self.args = {
                'model': None,
                'prompt': '',
                'softprompt': prefix,
                'sample_args': {
                    'temp': 0.6,
                    'top_p': 0.95,
                    'top_k': 140,
                    'tfs': 0.993,
                    'rep_p': 1.25,
                    'rep_p_range': 1024,
                    'rep_p_slope': 0.18,
                    'bad_words': ['***', "Author's Note", 'Deleted', ' [Image attached]', ':', ' :'],
                },
                'gen_args': {
                    'max_length': 40
                }
            }
    
    def play(self):
        clearConsole()
        if not self.api:
            while True:
                ip = input('Server IP: ')
                username = input('Username: ')
                password = input('Password: ')
                try:
                    self.api = Sukima_API(ip=ip, username=username, password=password)
                except Exception:
                    print('Authentication failed.')
                    continue
                print('Authentication success.')
                print('Choose a model.')
                models = self.api.get_models()
                option = list_items(models)
                self.args['model'] = models[option - 1]
                self.play()
        if not self.current_story:
            print(banner+'\n')
            option = list_items(['New story','Load story','New chat','Load chat','Settings','Quit'])

            if option == 1:
                self.current_story = Story()
                self.story_mode = True
                self.play()
            elif option == 2:
                filename = input('Filename: ')
                self.current_story = Story()
                self.current_story.load(filename)
                self.story_mode = True
                self.play()
            elif option == 3:
                self.current_story = Story()
                self.current_story.author1 = input('What is your username?: ')
                self.current_story.author2 = input('Who are you talking to?: ')
                self.story_mode = False
                self.play()
            elif option == 4:
                filename = input('Filename: ')
                self.current_story = Story()
                self.story_mode = False
                self.current_story.load(filename)
                self.play()
            elif option == 5:
                pass
            elif option == 6:
                raise KeyboardInterrupt
            
            self.play()
        else:
            args = self.args
            print(self.current_story.get_formatted(), end='')
            if self.story_mode:
                action_str = input('\033[1m')
            if self.story_mode == False:
                action_str = input(f'\n    \033[1m{self.current_story.author1}: ')
                # append self.author1 to beginning of action_str if it does not have a '/' in it
                if not action_str.startswith('/'):
                    # if context does not end with a newline, add one
                    if self.current_story.context()[-1] != '\n':
                        action_str = '\n' + action_str
                    action_str = f'{self.current_story.author1}: {action_str}'
                if '/' not in action_str:
                    self.current_story.action(action_str)
                    self.current_story.action(f'\n{self.current_story.author2}:', 1)
                    args['prompt'] = self.current_story.context()
                    aitext = self.api.generate(args=args)
                    # truncate text after last newline, but make sure it is one whole string
                    aitext = aitext.split('\n')
                    aitext = aitext[0] + '\n'
                    self.current_story.action(aitext, 1)
            print('\033[0m')
            if '/save' in action_str:
                filename = input('Filename: ')
                self.current_story.save(filename)
            elif '/undo' in action_str:
                self.current_story.undo()
            elif '/redo' in action_str:
                self.current_story.undo()
                args['prompt'] = self.current_story.context()
                if self.story_mode == False:
                    aitext = self.api.generate(args=args)
                    # truncate text after last newline, but make sure it is one whole string
                    aitext = aitext.split('\n')
                    aitext = aitext[0] + '\n'
                    self.current_story.action(aitext, 1)
                else:
                    aitext = self.api.generate(args=args)
                    self.current_story.action(aitext, 1)
            elif '/exit' in action_str:
                self.current_story = None
            elif '/submit' in action_str:
                # remove /submit from action_str
                action_str = action_str.replace('/submit', '')
                self.current_story.action(action_str)
                args['prompt'] = self.current_story.context()
                aitext = self.api.generate(args=args)
                self.current_story.action(aitext, 1)
            elif '/authorsnote' in action_str:
                an = input('Authors Note: ')
                if an:
                    self.current_story.authors_note = f"[ A/N: {an} ]"
                else:
                    self.current_story.authors_note = ''
            elif '/memory' in action_str:
                self.current_story.memory = edit_multiline(self.current_story.memory)
            elif '/alter' in action_str:
                if not self.current_story.entries:
                    self.play()
                last_action = self.current_story.entries[-1][0]
                clearConsole()
                last_action = edit_multiline(last_action)
                self.current_story.undo()
                self.current_story.action(last_action, 2)
            elif '/context' in action_str:
                clearConsole()
                print(self.current_story.context())
                input()
            elif '/ban' in action_str:
                bad_word = input('Bad Word: ')
                if bad_word:
                    self.args['sample_args']['bad_words'].append(bad_word)
            elif '/unban' in action_str:
                bad_word = input('Bad Word: ')
                if bad_word in self.args['sample_args']['bad_words']:
                    self.args['sample_args']['bad_words'].remove(bad_word)
            elif '/banlist' in action_str:
                print(self.args['sample_args']['bad_words'])
                input()
            elif '/help' in action_str:
                clearConsole()
                print('/save - save story')
                print('/undo - undo last action')
                print('/redo - redo last action')
                print('/submit - submit action')
                print('/authorsnote - add authors note')
                print('/memory - edit memory')
                print('/alter - edit last action')
                print('/context - view context')
                print('/ban - add bad word')
                print('/unban - remove bad word')
                print('/banlist - list bad words')
                print('/exit - exit')
                input()
            else:
                if self.story_mode:
                    self.current_story.action(action_str + '\n')
            self.play()
