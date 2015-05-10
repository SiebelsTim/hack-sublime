import sublime, sublime_plugin
import subprocess, os, re

class InsertTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, txt):
        self.view.insert(edit, self.view.size(), txt);

class ShowTypecheckerCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.unmarkAll()
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
            self.markErrorLines(typechecker_output)

    def getOutput(self):
        settings = self.window.active_view().settings()
        directory = os.path.dirname(self.window.active_view().file_name())
        ssh = settings.get("hack_ssh_enable")
        address = settings.get("hack_ssh_address")
        folder = settings.get("hack_ssh_folder")
        if (ssh and folder != None and address != None):
            ret = subprocess.Popen(
                [
                    "ssh", address, "cd " + folder + "; hh_client"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        else:
            ret = subprocess.Popen(
                      [
                          which('hh_client'),
                          '--from', 'sublime'
                          # ^ doesn't do anything for hh_client yet
                      ],
                      cwd=directory,
                      stdout=subprocess.PIPE,
                      stderr=subprocess.PIPE
                  )
        output = ret.communicate()[0]
        if ret.returncode == 0: # No Errors
            return ""
        return output

    def markErrorLines(self, output):
        views = {}
        regions = {}
        errors = output.split("\n")
        status = ""

        for err in errors:
            result = re.search('^(.*):(\d*):(\d*),(\d*): (.*)$', err)
            if result is None:
                continue
            filename, line_number, char_start, char_end, err_msg = result.groups()
            status += line_number + ": " + err_msg + " "

            filename = os.path.basename(filename)
            view = self.window.find_open_file(filename)
            if view is None:
                continue

            offset = view.text_point(int(line_number) - 1, 0)
            region = sublime.Region(
                offset - 1 + int(char_start),
                offset + int(char_end)
            )
            views[view.id()] = view

            if not regions.get(view.id()):
                regions[view.id()] = []
            regions[view.id()].append(region)

        for view in views:
            self.markError(views[view], regions[view])
        self.window.active_view().set_status('hacklang', status)

    def markError(self, view, regions):
        view.add_regions(
                'error', regions, 'invalid', 'circle'
            )

    def unmarkAll(self):
        for view in self.window.views():
            view.erase_regions('error')



class onSaveListener(sublime_plugin.EventListener):
	def on_post_save(self, view):
		view.window().run_command("show_typechecker")

class CompletionsListener(sublime_plugin.EventListener):

    def on_query_completions(self, view, prefix, locations):
        view.settings()
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
