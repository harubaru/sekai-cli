from .utils import *
from .play import *

import traceback
import gc

def esave(app):
    if app.current_story:
        while True:
            try:
                option = input("Do you wish to save your story? (y/n): ")
                if option.startswith("y"):
                    filename = input("Please enter a filename: ")
                    app.current_story.save(filename)
                    print(f'Saved to {filename}')
                else:
                    print("Aborting.")
                break
            except Exception:
                clearConsole()
                print('Invalid filename.')
                continue

if (__name__ == "__main__" or __name__ == "sekai"):
    try:
        app = App()
        while True:
            gc.collect()
            app.play()
    except KeyboardInterrupt:
        clearConsole()
        esave(app)
        exit(0)
    except Exception:
        traceback.print_exc()
        print("A fatal error has occurred.")
        esave(app)

        exit(1)
