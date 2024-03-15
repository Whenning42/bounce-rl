import UserKeyboard
import time

kb = UserKeyboard.UserKeyboard()
while not kb.is_halted():
    time.sleep(1)
    print(kb.key_state())
