"""کلاس پایه صحنه."""


class Scene:
    def __init__(self, game):
        self.game = game
        self.next_scene = None
        self.done = False

    def handle_event(self, e):
        pass

    def update(self):
        pass

    def draw(self, surf):
        pass

    def goto(self, scene):
        self.next_scene = scene
