
from virtualOS import *

class MyApp(NodeApp):
    def __init__(self, name, vos, resolution=(500, 800)):
        super().__init__(name, vos, resolution)
        self.font = pg.font.SysFont("monospace", 20)
        self.tabh = 50
        self.tabc = (10, 10, 10)
        self.bg = (30, 30, 30)
        self.color = (255, 255, 255)
        self.resize()

    def resize(self, tabh = None, line_height = None):
        self.line_height = line_height
        if tabh:
            self.tabh = tabh
            
        self.text = ScrollTextNode(self, (0, self.tabh), (self.res[0], self.res[1] - self.tabh),
                                   font = self.font, color = self.color, background = self.bg,
                                   line_height = self.line_height)
        self.text.text = '\n'.join([str(i) for i in range(200)])
        self.add(self.text)

        self.tab = RectNode(self, (0,0), (self.res[0], self.tabh), color = self.tabc)
        self.add(self.tab)
