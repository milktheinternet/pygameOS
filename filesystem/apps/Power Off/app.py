from virtualOS import App

class MyApp(App):
    def __init__(self, name, vos):
        super().__init__(name, vos)
    def run(self):
        self.vos.input.quit = True
