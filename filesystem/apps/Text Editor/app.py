
from virtualOS import *
from random import randint

class MyApp(NodeApp):
    def __init__(self, name, vos, resolution=(400, 600)):
        name += str(randint(0,1000))

        super().__init__(name, vos, resolution)

        self.can_minimize = False
        
        self.font = pg.font.SysFont("monospace", 17)
        self.tabh = 17
        self.tabc = (10, 10, 10)
        self.bg = (30, 30, 30)
        self.color = (255, 255, 255)
        self.resize()

        self.btnnewfile()
        
        self.at_x = 0
        self.at_y = 0

        self.interval = 100
        self.first_interval_mul = 2
        self.blink = 1000

        self.cursor = "\u2588"

        self.savepath = None
        self.saved = True

    def btnsaveas(self):
        print("SAVING FILE")
        def cb(name):
            self.vos.save("tmp/"+name, self.get_text())
            self.vos.run("Files")
            filesapp = self.vos.get_app("Files")
            print("saving file as", name)
            filesapp.save_file(name)
            self.vos.delete("tmp/"+name)
        PromptApp("prompt", self.vos, "Enter file name below (including type).", cb).run()

    def btnsave(self):
        if self.savepath: self.vos.save(self.savepath, self.get_text())

    def btnnewfile(self):
        self.savepath = None
        self.lines = ['']
        self.reset_cursor()

    def openfile(self, path):
        self.savepath = path
        self.lines = self.vos.load(path).split('\n')
        self.reset_cursor()

    def reset_cursor(self):
        self.old_text = ""
        self.scroll = 0
        self.at_x = 0
        self.at_y = 0

    def get_text(self):
        return '\n'.join(self.lines)

    def resize(self, tabh = None, line_height = None):
        self.line_height = line_height
        if tabh:
            self.tabh = tabh

        self.children = []

        self.tab = RectNode(self, (0,0), (self.res[0], self.tabh), color = self.tabc)
        self.add(self.tab)
        
        self.text = ScrollTextNode(self, (0, self.tabh), (self.res[0], self.res[1] - self.tabh),
                                   font = self.font, color = self.color, background = self.bg,
                                   line_height = self.line_height, draw_srf = None)
        self.line_height = self.text.line_height
        self.add(self.text)

        self.buttons = {}

        btndata = {
            "save": self.btnsave,
            "save as": self.btnsaveas,
            "new": self.btnnewfile,
            }

        x = 0
        w = self.tab.size[0] // len(btndata)

        for text, fun in btndata.items():
            btn = ButtonNode(self, (x, 0), (w, self.tabh), text, self.font,
                                    on_press=fun, center = True)
            self.buttons[text] = btn
            self.tab.add(btn)
            x += w

        self.changed_at = 0

    def handle_cursor(self):
        inp = self.vos.input
        if pg.K_LEFT in inp.keys_inst:
            self.at_x -= 1
            self.changed_at = self.vos.time + self.interval * self.first_interval_mul
        elif pg.K_RIGHT in inp.keys_inst:
            self.at_x += 1
            self.changed_at = self.vos.time + self.interval * self.first_interval_mul
        elif pg.K_DOWN in inp.keys_inst:
            self.at_y += 1
            self.changed_at = self.vos.time + self.interval * self.first_interval_mul
        elif pg.K_UP in inp.keys_inst:
            self.at_y -= 1
            self.changed_at = self.vos.time + self.interval * self.first_interval_mul
        else:
            at_x, at_y = self.at_x, self.at_y
                
            changed = True
            if pg.K_LEFT in inp.keys:
                at_x -= 1
            elif pg.K_RIGHT in inp.keys:
                at_x += 1
            else:
                changed = False
            if changed and self.vos.time - self.changed_at > self.interval:
                self.at_x = at_x
                self.changed_at = self.vos.time

        self.at_y = min(max(0, self.at_y), len(self.lines)-1)
        if pg.K_LEFT in inp.keys or pg.K_RIGHT in inp.keys:
            if self.at_x > len(self.lines[self.at_y]):
                self.at_x = 0
                if self.at_y - 1 < len(self.lines): self.at_y += 1
            elif self.at_x < 0:
                if self.at_y: self.at_y -= 1
                self.at_x = len(self.lines[self.at_y])
        self.at_y = min(max(0, self.at_y), len(self.lines)-1)
        self.at_x = min(max(0, self.at_x), len(self.lines[self.at_y]))

    def update_typing(self):
        inp = self.vos.input
        
        if inp.text:
            line = self.lines[self.at_y]
            self.lines[self.at_y] = line[:self.at_x] + inp.text + line[self.at_x:]
            inp.keys_inst.append(pg.K_RIGHT)
            self.saved = False
        inp.text = ""

        if pg.K_RETURN in inp.keys_inst:
            line, remains = self.lines[self.at_y][self.at_x:],\
                self.lines[self.at_y][:self.at_x]
            self.lines.insert(self.at_y+1, line)
            self.lines[self.at_y] = remains
            inp.keys_inst.append(pg.K_RIGHT)
            inp.keys.append(pg.K_RIGHT)
            self.saved = False
            
        if pg.K_BACKSPACE in inp.keys_inst:
            if self.at_x == 0:
                lines = self.lines
                self.at_x = len(lines[self.at_y-1])
                self.lines[self.at_y-1] += lines[self.at_y]
                self.lines = lines[:self.at_y] + lines[self.at_y+1:]
            else:
                line = self.lines[self.at_y]
                if line:
                    self.lines[self.at_y] = line[:self.at_x-1] + line[self.at_x:]
            inp.keys_inst.append(pg.K_LEFT)
            inp.keys.append(pg.K_LEFT)
            self.saved = False

        self.handle_cursor()

        if pg.K_RETURN in inp.keys_inst:
            inp.keys.remove(pg.K_RIGHT)
        if pg.K_BACKSPACE in inp.keys_inst:
            inp.keys.remove(pg.K_LEFT)

    def update_click(self):
        inp = self.vos.input
        if inp.click_inst and point_within_rect(inp.mouse, self.rect):
            mx, my = self.mouse
            my -= self.tabh
            current_line = (my - self.text.scroll) // self.line_height
            self.at_y = min(max(0, current_line), len(self.lines)-1)
            

    def update(self):
        super().update()

        self.update_typing()

        self.update_click()

    def render(self):
        self.buttons['save'].text = "save" if self.saved else "save*"
        self.srf.fill(self.bg)
        if self.vos.time % self.blink < self.blink//2:
            text = [str(s) for s in self.lines]
            line = text[self.at_y]
            try:line = line[:self.at_x] + self.cursor + line[self.at_x + 1:]
            except IndexError:pass
            text[self.at_y] = line
            self.text.text = '\n'.join(text)
        else:
            self.text.text = self.get_text()
        super().render()
