import sublime, sublime_plugin
import subprocess, os.path

class InsertTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, txt):
        self.view.insert(edit, self.view.size(), txt);

class ShowTypecheckerCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.output_view = self.window.get_output_panel("textarea")
        self.window.run_command("hide_panel", {"panel": "output.textarea"})
        if not self.checkFileType():
            return
        self.output_view.set_read_only(False)
        typechecker_output = self.getOutput().decode('utf-8')
        self.output_view.run_command('insert_text', {"txt": typechecker_output})
        self.output_view.set_read_only(True)
        if typechecker_output != "":
            self.window.run_command("show_panel", {"panel": "output.textarea"})

    def getOutput(self):
        if not self.checkConfig():
            return ".hhconfig not found"
        directory = os.path.dirname(self.window.active_view().file_name())
        if directory == None:
            return "File not Found"

        ret = subprocess.Popen(
            ['hh_client', directory],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
            )
        output = ret.communicate()[0]
        if ret.returncode == 0: # No Errors
            return ""
        return output

    def checkConfig(self):
        directory = os.path.dirname(self.window.active_view().file_name())
        return os.path.isfile("%s/.hhconfig" % directory)

    def checkFileType(self):
        tag = self.window.active_view().substr(sublime.Region(0, 2))
        return tag == '<?'



class onSaveListener(sublime_plugin.EventListener):
	def on_post_save(self, view):
		view.window().run_command("show_typechecker")