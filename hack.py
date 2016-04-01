import sublime, sublime_plugin
import subprocess, os, re, threading

def insertText(view, message):
    view.set_read_only(False)
    view.run_command('insert_text', {"txt": message})
    view.set_read_only(True)

class HackClient(threading.Thread):
    def __init__(self, window):
        super(HackClient, self).__init__()

        self.window = window
        self.output_view = self.window.get_output_panel("textarea")
        self.settings = self.window.active_view().settings()
        self.ssh_enable = self.settings.get("hack_ssh_enable")
        self.ssh_address = self.settings.get("hack_ssh_address")
        self.ssh_folder = self.settings.get("hack_ssh_folder")
        self.client = None

        self.window.run_command("show_panel", {"panel": "output.textarea"})

    def run(self):
        self.client = self.startClient()

        t = threading.Timer(1.0, insertText, (self.output_view, "Waiting for hh_client to initialise...\n"))
        t.start()

        self.client.wait()
        t.cancel()
        self.updateOutput()

    def useSSH(self):
        return self.ssh_enable and self.ssh_folder != None and self.ssh_address != None

    def startClient(self):
        if self.useSSH():
            return self.startSSHClient()
        else:
            return self.startLocalClient()

    def startSSHClient(self):
        return subprocess.Popen(
            [
                "ssh", self.ssh_address, "cd " + self.ssh_folder, "; hh_client --from sublime"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    def startLocalClient(self):
        directory = os.path.dirname(self.window.active_view().file_name())
        return subprocess.Popen(
            [
                which('hh_client'), '--from', 'sublime'
            ],
            cwd=directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    def updateOutput(self):
        output = self.client.stdout.read().decode('utf-8')
        insertText(self.output_view, output)

        self.unmarkAll()
        if len(output) != 0:
            self.markErrorLines(output)

    def markErrorLines(self, output):
        views = {}
        regions = {}
        output_lines = output.split("\n")
        for oline in output_lines:
            if not re.search('^File', oline):
                continue # Skip error messages
            split = oline.split(',')
            filename = split[0][6:-1]
            line_number = split[1][6:]
            if self.useSSH():
                view = self.findViewForFile(filename)
            else:
                view = self.window.find_open_file(filename)
            if view == None:
                # TODO: Sublime doesn't like symlinks
                continue # file not open, don't highlight it
            # sublime uses characters rather than linenumbers
            offset = view.text_point(int(line_number)-1, 0)
            region = split[2][12:-1].split('-')
            region = sublime.Region(offset-1+int(region[0]), offset+int(region[1]))
            views[view.id()] = view
            if not regions.get(view.id()):
                regions[view.id()] = []
            regions[view.id()].append(region)

        for view in views:
            # for some reason view gets converted to its id in the for
            self.markError(views[view], regions[view])

    def findViewForFile(self, file):
        settings = self.window.active_view().settings()
        ssh_folder = settings.get("hack_ssh_folder")
        relative_file = file

        if file.startswith(ssh_folder):
            relative_file = file[len(ssh_folder):]

        for view in self.window.views():
            if view.file_name() and view.file_name().endswith(relative_file):
                return view

        return None

    def markError(self, view, regions):
        view.add_regions(
                'error', regions, 'invalid', 'circle'
            )

    def unmarkAll(self):
        for view in self.window.views():
            view.erase_regions('error')

class InsertTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, txt):
        self.view.insert(edit, self.view.size(), txt);

class ShowTypecheckerCommand(sublime_plugin.WindowCommand):
    def run(self):
        if not checkFileType(self.window.active_view()):
            return

        hack_client = HackClient(self.window)
        hack_client.start()

class onSaveListener(sublime_plugin.EventListener):
	def on_post_save(self, view):
		view.window().run_command("show_typechecker")

class CompletionsListener(sublime_plugin.EventListener):

    def on_query_completions(self, view, prefix, locations):
        settings = view.settings()
        ssh = settings.get("hack_ssh_enable")
        if ssh or not checkFileType(view):
            return [()] # default
        directory = os.path.dirname(view.file_name())
        startregion = sublime.Region(0, locations[0])
        endregion = sublime.Region(locations[0], view.size());
        contents = view.substr(startregion)+"AUTO332"+view.substr(endregion)
        proc = subprocess.Popen(
                    [
                        which('hh_client'), "--auto-complete"
                    ],
                    cwd=directory,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
        stdout = proc.communicate(contents.encode('utf-8'))
        if proc.returncode == 0:
            results = self.format(stdout)
            return results

    # hh_client returns a tuple
    # = ("newline seperated list", None) for what I see
    def format(self, input):
        entries = results = []
        for entry in input[0].decode('utf-8').split("\n"):
            if not entry:
                continue
            space = entry.find(' ')
            if entry[0] == '$': # Variable
                name_end = len(entry) if (space == -1) else space
                word = entry[1:name_end]
                results.append((entry, word));
            elif space < 0: # Class or function
                results.append((entry, entry))
            else: # Method, property or constant
                word = entry[:space]
                results.append((entry, word))
        return results



def checkFileType(view):
    tag = view.substr(sublime.Region(0, 2))
    return tag == '<?'

def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        pathenv = os.getenv("PATH") + os.pathsep + "/usr/local/bin/"
        for path in pathenv.split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    raise Exception("hh_client executable not found")
