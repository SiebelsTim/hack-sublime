Installation
============

Download the zip-archive and move it into Sublime Text's config folder.

```bash
wget https://github.com/SiebelsTim/hack-sublime/raw/master/Hack.sublime-package
mv Hack.sublime-package ~/.config/sublime-text-3/Installed\ Packages/Hack.sublime-package
```
Change the folder to `sublime-text-2` if you use Sublime Text 2


How to use
==========

The typechecker is triggered on saving files. The files need to begin with `<?`. So both `<?php` and `<?hh` will work. The filetype is ignored. 

Autocompletion is triggered on your keyboard shortcut. Look it up under `Preferences -> Key Bindings` and search for `auto_complete`.

![Example](http://i.imgur.com/DaDBlgE.png)
