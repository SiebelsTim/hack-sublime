import sublime, sublime_plugin
import subprocess, os.environ, os.pathsep, os.access, os.X_OK, os.path, re

class InsertTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, txt):
        self.view.insert(edit, self.view.size(), txt);

class ShowTypecheckerCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.output_view = self.window.get_output_panel("textarea")
        self.window.run_command("hide_panel", {"panel": "output.textarea"})
        if not checkFileType(self.window.active_view()):
            return 
        self.output_view.set_read_only(False)
        typechecker_output = self.getOutput().decode('utf-8')
        self.output_view.run_command('insert_text', {"txt": typechecker_output})
        self.output_view.set_read_only(True)
        if typechecker_output != "":
            self.window.run_command("show_panel", {"panel": "output.textarea"})

    def getOutput(self):
        if not checkConfig(self.window.active_view()):
            return ".hhconfig not found"
        directory = os.path.dirname(self.window.active_view().file_name())
        if directory == None:
            return "File not Found"

        ret = subprocess.Popen(
            [
                which('hh_client'), directory, 
                '--from', 'sublime' # doesn't do anything for hh_client yet
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
            )
        output = ret.communicate()[0]
        if ret.returncode == 0: # No Errors
            return ""
        return output



class onSaveListener(sublime_plugin.EventListener):
	def on_post_save(self, view):
		view.window().run_command("show_typechecker")

class CompletionsListener(sublime_plugin.EventListener):

    def on_query_completions(self, view, prefix, locations):
        if not checkFileType(view):
            return [()] # default
        if not checkConfig(view):
            return [('.hhconfig not found', '.hhconfig not found')]
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
                    stderr=subprocess.STDOUT
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
                menu = entry[space:]
                if not not re.search("\(function\(", menu): 
                    results.append((entry, word))
                else:
                    results.append((entry, word))
        return results   



def checkConfig(view):
    for x in view.window().folders():
        if os.path.isfile("%s/.hhconfig " % x):
            return True

    path = os.path.dirname(view.file_name())
    return os.path.isfile("%s/.hhconfig" % path);

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
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None