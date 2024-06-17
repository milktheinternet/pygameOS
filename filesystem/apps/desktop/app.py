from virtualOS import SurfaceApp, pg, point_within_rect

APP_ORDER = ["Power Off", "Files"]

class MyApp(SurfaceApp):
    def __init__(self, name, vos):
        super().__init__(name, vos)
        self.apps = self.vos.list_folder(self.vos.appdir)
        if name in self.apps:
            self.apps.remove(name)
        for app_name in reversed(APP_ORDER):
            if app_name in self.apps:
                self.apps.remove(app_name)
                self.apps.insert(0, app_name)
        self.app_size = 64
        self.margin = self.app_size // 10
        self.bg = (25, 25, 25)
        self.app_font = pg.font.SysFont("monospace", self.app_size//2, True)
        self.minimized_app_names = []
        self.minimized_apps = []
        
    def default_icon(self, app):
        srf = pg.Surface((self.app_size, self.app_size))
        srf.blit(self.app_font.render(app.title()[:2], True, (255, 255, 255), (0,0,0)), (0,0))
        return srf
    
    def get_icon(self, app):
        img = self.vos.load_image(self.vos.appdir + app + '/' + 'icon.png', transparent=True)
        if img:
            img = pg.transform.scale(img, (self.app_size, self.app_size))
            return img
        else:
            return self.default_icon(app)
        
    def on_run(self):
        self.icons = {app: self.get_icon(app) for app in self.apps}
        self.minimized_overlay = pg.Surface((self.app_size, self.app_size), pg.SRCALPHA)
        self.minimized_overlay.fill((200, 200, 200, 127))
        
    def on_minimize(self, app):
        self.minimized_apps.append(app)
        self.minimized_app_names.append(app.name)

    @property
    def mouse_not_within_app(self):
        for app in self.vos.apps:
            if 'WindowApp' in app.flags and point_within_rect(self.vos.input.mouse, app.full_rect):
                return False
        return True

    def update(self):
        super().update()
        for app in self.vos.apps:
            if "WindowApp" in app.flags:
                app.on_minimize = self.on_minimize
        x, y = self.margin, self.margin
        for app_name, icon in self.icons.items():
            if self.vos.input.click_inst and self.mouse_not_within_app:
                if point_within_rect(self.vos.input.mouse, (x, y, self.app_size, self.app_size)):
                    if app_name in self.minimized_app_names:
                        app = self.minimized_apps[self.minimized_app_names.index(app_name)]
                        app.visible = True
                        self.minimized_app_names.remove(app_name)
                        self.minimized_apps.remove(app)
                    else:
                        result = self.vos.run(app_name)
                        if result == 2:
                            self.vos.get_app(app_name).minimize()
            
            x += self.app_size + self.margin
            if x + self.app_size > self.res[0]:
                x = self.margin
                y += self.app_size + self.margin
        
    def render(self):
        if not self.visible:
            return
        
        self.srf.fill(self.bg)
        x, y = self.margin, self.margin
        for app_name, icon in self.icons.items():
            self.srf.blit(icon, (x, y))
            if app_name in self.minimized_app_names:
                self.srf.blit(self.minimized_overlay, (x,y))
            x += self.app_size + self.margin
            if x + self.app_size > self.res[0]:
                x = self.margin
                y += self.app_size + self.margin
                
        super().render()
