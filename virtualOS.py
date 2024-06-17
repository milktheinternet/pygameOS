from os import environ, mkdir, listdir, remove, rename
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "TRUE"
from os.path import isdir, exists
from shutil import rmtree as rmdir

from pg_input import Input
from app_loader import import_app

import pygame as pg
pg.init()

#PONG, image viewer, text editor

def point_within_rect(point, rect):
    px, py = point
    x, y, w, h = rect
    return x <= px < x + w and y <= py < y + h

class VirtualOS:
    def __init__(self, resolution = (800, 600), background = None):
        self.bg = background
        self.res = resolution
        self.input = Input()
        self.fps = 60
        self.clock = pg.time.Clock()
        self.apps = []
        self.on_run = []

        self.time = 0

        self.font = pg.font.SysFont('monospace', 17)

        self.filesystem = 'filesystem/'
        
        self.appdir = 'apps/'
        for folder in self.list_folder(self.appdir):
            files = self.list_folder(self.appdir+folder)
            if not files:
                self.delete(self.appdir+folder)

        self.LOG = ""

        self.copied_text = ""

        self.tmpdir = 'tmp/'

    def log(self, text):
        #print(text)
        self.LOG += text
        
    def start(self):
        if not self.res:
            self.res = (0,0)
        self.screen = pg.display.set_mode(self.res)
        self.res = self.screen.get_size()
        self.run('desktop')
        while not self.input.quit:
            self.update()
            self.render()
            self.clock.tick(self.fps)
        for app in reversed(self.apps):
            app.close()
        pg.display.quit()

    def update(self):
        self.input.update()
        self.time += self.clock.get_time()
        for app in self.apps:
            if app.can_update:
                app.update()
        
    def render(self):
        if self.bg:
            self.screen.fill(self.bg)
        for app in self.apps:
            app.render()
        pg.display.update()

    def save(self, path, data):
        if isinstance(data, str):
            self.log(f"Invalid save data.")
        try:
            with open(self.filesystem + path, 'w') as f:
                f.write(data)
        except FileNotFoundError:
            self.log(f"Could not find parent folder for: {path}")
            return False
        except IsADirectoryError:
            self.log(f"Could not save file as a folder already has the same name: {path}")
            return False
        return True
            
    def load(self, path):
        try:
            return open(self.filesystem + path).read()
        except FileNotFoundError:
            self.log(f"File not found: {path}")
            return None

    def rename(self, from_path, to_path):
        try:
            rename(self.filesystem + from_path, self.filesystem + to_path)
            return True
        except FileNotFoundError:
            self.log(f"Invalid path: {from_path} or {to_path}")
        return False

    # from_path is a file, while to_path is a folder
    def copy(self, from_path, to_path):
        return self.save(to_path + '/' + from_path.split('/')[-1], self.load(from_path))


    def make_folder(self, path):
        try:
            mkdir(self.filesystem + path)
            return True
        except FileExistsError:
            self.log(f"Tried to create folder that already exists: {path}")
            return True # folder exists, but did not create it
        except FileNotFoundError:
            self.log(f"Could not find parent folder for: {path}")
            return False

    def delete(self, path):
        path = self.filesystem + path
        
        if not exists(path):
            return False

        if isdir(path):
            rmdir(path)
        else:
            remove(path)
        return True    
        

    def list_folder(self, path):
        try:
            return listdir(self.filesystem + path)
        except FileNotFoundError:
            self.log(f"Did not find file: {path}")
            return None

    # folder paths must not end in a "/"!
    def copy_folder(self, from_path, to_path):
        from_path = self.filesystem + from_path
        to_path = self.filesystem + to_path
        if isdir(from_path) and isdir(to_path):
            copied_path = to_path + '/' + from_path.split('/')[-1]
            self.make_folder(copied_path)
            for file in self.list_folder(from_path):
                if isdir(file):
                    self.copy_folder(from_path+'/'+file, copied_path)
                else:
                    self.copy(from_path+'/'+file, copied_path)
        else:
            self.log(f"A folder path was invalid: '{from_path}' or '{to_path}'")
            return False
        return True

    def load_image(self, path, transparent = False):
        path = self.filesystem + path
        if not exists(path):
            self.log(f"Image not found: {path}")
            return
        srf = pg.image.load(path)
        srf = srf.convert_alpha() if transparent else srf.convert()
        return srf

    def install(self, appfolder):
        name = file.split('/')[-1]
        return self.copy_folder(appfolder, self.appdir)

    def uninstall(self, app):
        return self.delete(self.appdir + name)

    @property
    def app_names(self):
        return [app.name for app in self.apps]

    def get_app(self, name):
        for app in self.apps:
            if app.name == name:
                return app

    def stop_all_window_apps(self):
        for app in self.apps:
            if "WindowApp" in app.flags:
                app.can_update = False

    def run(self, name):
        if name in self.app_names:
            self.log(f"{name} is currently running.")
            return 2
        path = self.filesystem + self.appdir + f'{name}/app.py'
        if exists(path):
            App = import_app(path, name)
            app = App(name, self)
            app.run()
            # on_run functions use the app run as a parameter
            for fun in self.on_run:
                fun(app)
            return 1
        self.log(f"Could not find app {name} to run.")
        return 0

class App:
    # vos short for virtual OS
    def __init__(self, name, vos):
        self.can_update = True
        self.name = name
        self.vos = vos
        self.path = self.vos.appdir + self.name + '/'
        self.vos.make_folder(self.path) # ensure app folder exists
        self.flags = []
        self.supported_types = []

    def open_path(self, path):
        return path.split('.')[-1] in self.supported_types

    def on_run(self):pass
    def on_close(self):pass
        
    def save(self, path, data):return self.vos.save(self.path + path, data)
    def load(self, path, data):return self.vos.load(self.path + path)
    def make_folder(self, path, data):return self.vos.make_folder(self.path + path)
    def delete(self, path):return self.vos.delete(self.path + path)
    def list_folder(self, path):return self.vos.list_folder(self.path + path)
    def copy_folder(self, from_path, to_path):return self.vos.list_folder(self.path + from_path, self.path + to_path)
    def load_image(self, path):return self.vos.load_image(self.path + path)
    
    def uninstall(self):
        self.vos.log(f'uninstalling {self.name}')
        self.vos.uninstall(self.name)
    
    def run(self):
        self.vos.log(f'running {self.name}')
        self.vos.apps.append(self)
        self.on_run()
        
    def close(self):
        self.vos.log(f'closing {self.name}')
        if self.on_close:
            self.on_close()
        if "app.py" not in self.list_folder(""):self.delete("")
        self.vos.apps.remove(self)
        
    def update(self):
        pass
    
    def render(self):
        pass

class SurfaceApp(App):
    def __init__(self, name, vos, resolution = None, pos = None):
        super().__init__(name, vos)
        self.res = resolution
        self.pos = pos
        self.srf = None
        self.visible = True

    @property
    def rect(self):
        return list(self.pos)+list(self.res)

    def center(self):
        w, h = self.res
        W, H = self.vos.res
        self.pos = (W//2-w//2, H//2-h//2)
        
    def run(self):
        if not self.res: self.res = self.vos.res
        if not self.pos: self.center()
        if not self.srf: self.srf = pg.Surface(self.res)
        super().run()
        
    def render(self):
        if self.visible:
            self.vos.screen.blit(self.srf, self.pos)


class WindowApp(SurfaceApp):
    def __init__(self, name, vos, resolution= None, pos = None):
        super().__init__(name, vos, resolution, pos)

        self.can_update = False

        self.flags.append("WindowApp")
        
        self.tab_height = 15
        self.tab_bg = (200, 200, 200)
        self.tab_close = (255, 0, 0)
        self.tab_minimize = (255, 200, 0)

        self.can_minimize = True

        self.dragging = False
        self.drag_from = (0, 0)

        self.bg = (50,50,50)

    def resize(self, resolution = None):
        if resolution:
            self.res = resolution
        else:
            self.res = self.vos.res
        self.center()
        self.srf = pg.Surface(self.res)

    def make_tab_srf(self):
        w, h = (self.res[0], self.tab_height)
        self.tab_srf = pg.Surface((w,h))
        self.tab_srf.fill(self.tab_bg)
        pg.draw.rect(self.tab_srf, self.tab_close, (w-h, 0, h, h))
        if self.can_minimize:
            pg.draw.rect(self.tab_srf, self.tab_minimize, (w-h*2, 0, h, h))

    def focus(self):
        self.vos.stop_all_window_apps()
        self.can_update = True
        self.vos.apps.remove(self)
        self.vos.apps.append(self)

    def on_run(self):
        self.srf.fill(self.bg)
        self.make_tab_srf()
        self.vos.input.on_click.append(self.on_click)
        self.focus()

    def on_close(self):
        self.vos.input.on_click.remove(self.on_click)

    def on_click(self):
        tabx, taby = self.tab_pos
        tabh = self.tab_height
        mx, my = self.vos.input.mouse

        w,h = self.res

        if point_within_rect((mx, my), (tabx, taby, w, h+tabh)):
            self.focus()
        
        if point_within_rect((mx, my), (tabx, taby, self.res[0], tabh)):
            if mx > tabx + self.res[0] - tabh: # close button
                self.close()
            elif self.can_minimize and mx > tabx + self.res[0] - tabh*2: # minimize button
                self.minimize()
            elif self.can_update: # drag
                self.dragging = True
                self.drag_from = (mx-self.pos[0], my-self.pos[1])

    @property
    def mouse(self):
        mx, my = self.vos.input.mouse
        x, y = self.pos
        return mx - x, my - y

    def minimize(self):
        self.visible = False
        self.vos.log(f"minimizing {self.name}")
        self.on_minimize(self)

    def on_minimize(self, app):
        self.vos.log(f"no minimization handler for {self.name}")

    @property
    def tab_pos(self):
        return (self.pos[0], self.pos[1] - self.tab_height)
    
    def update(self):
        if not self.visible:
            return
        if self.dragging:
            mx, my = self.vos.input.mouse
            dx, dy = self.drag_from
            self.pos = (mx - dx, my - dy)
            if not self.vos.input.click:
                self.dragging = False
    
    def render(self):
        if self.visible:
            self.vos.screen.blit(self.srf, self.pos)
            if self.res != self.vos.res:
                self.vos.screen.blit(self.tab_srf, self.tab_pos)

class NodeApp(WindowApp):
    def __init__(self, name, vos, resolution=None):
        super().__init__(name, vos, resolution)
        self.children = []
        self.global_pos = (0,0)
    def update(self):
        super().update()
        for node in self.children:
            node.update()
    def render(self):
        self.srf.fill(self.bg)
        for node in self.children:
            node.render()
        super().render()
    def add(self, node):
        self.children.append(node)
        node.parent = self
        node.orphan = False
    def remove(self, node):
        self.children.remove(node)
        node.orphan = True

class Node:
    def __init__(self, app, pos=(0,0)):
        self.app = app
        self.vos = app.vos
        self.children = []
        self.parent = None
        self.x, self.y = pos
        self.orphan = True
    @property
    def global_pos(self):
        x, y = self.parent.global_pos
        return self.x, self.y
    def update(self):
        for node in self.children:
            node.update()
    def render(self):
        for node in self.children:
            node.render()
    def add(self, node):
        self.children.append(node)
        node.parent = self
        node.orphan = False
    def remove(self, node):
        self.children.remove(node)
        node.orphan = True

class SurfaceNode(Node):
    def __init__(self, app, pos=(0,0), size=(100, 100), draw_srf = None):
        super().__init__(app, pos)
        self.size = size
        self.srf = pg.Surface(size)
        self.draw_srf = draw_srf
    def render(self):
        srf = self.draw_srf if self.draw_srf else self.app.srf
        srf.blit(self.srf, self.global_pos)
        super().render()

class RectNode(Node):
    def __init__(self, app, pos=(0,0), size=(100, 100), color=(255,0,255)):
        super().__init__(app, pos)
        self.size = size
        self.srf = pg.Surface(size)
        self.color = color
    def render(self):
        pg.draw.rect(self.app.srf, self.color, list(self.global_pos) + list(self.size))
        super().render()

class TextNode(SurfaceNode):
    def __init__(self, app, pos=(0,0), size=(100, 100), text="This is a TextNode", font = None, color=(255,255,255), background=(0,0,0), center = False, draw_srf = None):
        super().__init__(app, pos, size, draw_srf)
        self.text = text
        self.old_text = None
        self.font = font if font else self.vos.font
        self.color = color
        self.bg = background
        self.center = center
    def render(self):
        if self.text != self.old_text:
            if self.bg:
                self.srf.fill(self.bg)
            self.old_text = self.text
            srf = self.font.render(self.text, True, self.color, self.bg)
            if not self.center:
                self.srf.blit(srf, (0,0))
            else:
                w, h = srf.get_size()
                W, H = self.size
                self.srf.blit(srf, (W//2-w//2,H//2-h//2))
        super().render()

class ScrollTextNode(SurfaceNode):
    def __init__(self, app, pos=(0,0), size=(100, 100), text="This is a TextNode", font = None, color=(255,255,255), background=(0,0,0), center = False, line_height = None, draw_srf = None):
        super().__init__(app, pos, size, draw_srf)
        self.text = text
        self.old_text = None
        self.font = font if font else self.vos.font
        self.color = color
        self.bg = background
        self.center = center
        self.line_height = line_height if line_height else self.font.render("lyg", True, [0]*3).get_height()
        self.scroll = 0
        self.old_scroll = None
        self.nlines = 0
        self.speed = 1
    def update(self):
        if not self.app.visible:
            return
        self.scroll -= self.vos.input.scroll * self.speed * self.line_height
        self.scroll = max(min(self.scroll, (self.line_height * self.nlines - self.size[1])), 0)
        super().update()
    def render(self):
        if self.text != self.old_text:
            lines = self.text.split('\n')
            self.nlines = len(lines)
            self.text_srf = pg.Surface((self.size[0], self.line_height * self.nlines))
            if self.bg:
                self.text_srf.fill(self.bg)
            y = 0
            for line in lines:
                text = TextNode(self.app, (0,y), (self.size[0], self.line_height),
                                line, self.font, self.color, self.bg, self.center,
                                draw_srf = self.text_srf)
                text.parent = self
                text.render()
                y += self.line_height

        if self.scroll != self.old_scroll or self.text != self.old_text:
            self.old_text = self.text
            self.old_scroll = self.scroll
            self.srf.fill(self.bg)
            self.srf.blit(self.text_srf, (0, -self.scroll))
        super().render()

class ButtonNode(TextNode):
    def __init__(self, app, pos=(0,0), size=(100, 100), text="This is a TextNode",
                 font = None, color=(255,255,255), background=(0,0,0), on_press=None,
                 center = False):
        super().__init__(app, pos, size, text, font, color, background, center)
        self.on_press = on_press
        self.pressed = False
    def update(self):
        super().update()
        if not self.app.visible:
            return
        inp = self.vos.input
        self.pressed = True
        if inp.click_inst and point_within_rect(self.app.mouse, [self.x, self.y]+list(self.size)) and self.on_press:
            self.on_press()
            self.pressed = True
        

class TextApp(WindowApp):
    def __init__(self, name, vos, resolution=None, font=None):
        super().__init__(name, vos, resolution)
        self.font = font if font else self.vos.font
        self.margin = 10
        self.line_height = 20
        if not self.res:
            self.res = self.vos.res
        self.max_lines = self.res[1]//(self.line_height+self.margin)
        self.bg = (0,0,0)
        self.color = (255,255,255)
        self.old_text = ""
    def update_render(self, text):
        if text == self.old_text:
            return
        self.old_text = text
        self.srf.fill(self.bg)
        x, y = self.margin, self.margin
        lines = text.split('\n')
        lines = lines[:min(self.max_lines, len(lines))]
        for line in lines:
            if line:
                self.srf.blit(
                    self.font.render(line, True, self.color, self.bg), (x,y))
            y += self.line_height

class DictMenuApp(TextApp):
    def __init__(self, name, vos, resolution=None):
        super().__init__(name, vos, resolution)
        self.tree = {"- no options -":None}
        self.location = []
        self.idx = 0
        self.BACK = "<- back"
        self.text = ""

        self.branchflags = []
        
    def back(self):
        if self.location:
            self.location.pop()
            if "double_back" in self.branchflags:
                self.branchflags = []
                self.back()
        
    def get_branch(self, loc):
        loc = list(loc)
        branch = self.tree
        [branch:=branch[loc] for loc in self.location]
        return branch

    def update_options(self):
        branch = self.get_branch(self.location)
        
        options = list(branch.keys())

        self.branchflags = branch.get("flags")
        if self.branchflags != None:
            options.remove('flags')
        else:
            self.branchflags = []

        
        
        if self.location:
            options.insert(0, self.BACK)
        self.idx %= len(options)

        s = self.text + '\n\n' if self.text else ''
        for i in range(len(options)):
            s += ('> ' if self.idx == i else '  ') + options[i] + '\n'

        if pg.K_RETURN in self.vos.input.keys_inst:
            choice = options[self.idx]
            self.idx = 0
            if choice == self.BACK:
                self.back()
            elif isinstance(branch[choice], dict):
                self.location.append(choice)
            elif branch[choice]:branch[choice]()

        self.update_render(s)

    def on_run(self):
        super().on_run()
        self.update_render(str(self.tree))

    def update(self):
        if not self.visible:
            return
        super().update()
        inp = self.vos.input
        if pg.K_UP in inp.keys_inst:
            self.idx -= 1
        if pg.K_DOWN in inp.keys_inst:
            self.idx += 1

        self.update_options()

class PromptApp(TextApp):
    def __init__(self, name, vos, prompt="Enter text:", callback=None, resolution=(400, 75)):
        super().__init__(name, vos, resolution)
        self.vos.input.text = ""
        self.prompt, self.callback = prompt, callback
        self.vos.input.keys_inst = []
        self.bg = (255,255,255)
        self.color = (0,0,0)
    def update(self):
        inp = self.vos.input
        if not self.visible:
            return
        super().update()
        if pg.K_RETURN in inp.keys_inst:
            self.callback(inp.text)
            self.close()
        self.update_render(self.prompt+'\n'+inp.text)
        

if __name__ == '__main__':
    vos = VirtualOS(resolution = (1200, 900))
    vos.start()
