import common
import plugin

import os
import time

import traceback

log = common.get_logger(__name__)

icon = "lib/icon.ico"
hover_text = "NMControl"

def open_conf_folder(app):
    """Systray entry function."""
    # http://stackoverflow.com/questions/41969/standard-way-to-open-a-folder-window-in-linux
    path = app['path']['conf']
    if os.name == "nt":  # windows
        os.startfile(path)
        #  workaround for pylint in case it should be necessary
        #import subprocess
        #subprocess.call(["cmd", "/c", "start", path])
    elif os.name == "posix":  # linux
        os.system('xdg-open "%s"' % path)
    else:  # osx
        os.system('open "%s"' % path)

class pluginSystray(plugin.PluginThread):
    name = 'systray'
    options = {
        'start':    ['Launch at startup', 1],
    }
    systrayEntry = ('Open conf folder', None, open_conf_folder)
    sti = None

    def gather_entries(self):
        entries = []
        for plugin in self.app["plugins"]:
            try:
                entries.append(self.app["plugins"][plugin].systrayEntry)
            except AttributeError:
                pass
        return tuple(entries)

    def pStart(self):
        if self.sti:
            return
        log.debug("Systray.py: Plugin %s parent start" %(self.name))
        self.menu_options = self.gather_entries()
        try:
            if os.name == "nt":
                import winsystray as ossystray
                self.sti = ossystray.SysTrayIcon(icon, hover_text, self.menu_options, on_quit=self.do_quit, default_menu_index=None)
            else:
                log.info("pluginSystray: Sorry, the systray icon is only available on Windows so far.")
                return
        except:
            # bail without systray for GUI people
            import __main__
            if "win.py" in __main__.__file__:  # nmcontrol.py, nmcontrolwin.pyw, nmcontrolwin.py (pyinstaller)
                self.criticalStartException = ("Systray start failed.\n" +
                                                        "Note: Windows systray needs Python Win32 Extensions.\n\n" +
                                                        traceback.format_exc())
                return
            raise
        self.sti.app = self.app
        self.halted = 0
        self.running = 1
        while self.running:
            self.sti.pump()
            time.sleep(0.01)
        self.sti.do_quit()
        self.halted = 1

    def pStop(self, arg = []):
        log.debug("Plugin %s parent stop" %(self.name))
        if not self.running:
            return True
        while not self.halted:
            self.running = False
            time.sleep(0.001)
        return True

    def do_quit(self, sti):
        log.debug("Systray.py: do_quit")
        common.app['plugins']['main'].stop()  # will bail if already shutting down
