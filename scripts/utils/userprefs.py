import os


class UserPrefs:

    def __init__(self):
        self.base = self.get_base()
        
    def get_base(self):
        base = os.path.join(os.path.expanduser('~'), '.igea')
        if not os.path.exists(base):
            os.makedirs(base)
        return base


if __name__ == "__main__":
    print(UserPrefs().base)