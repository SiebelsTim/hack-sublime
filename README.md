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

Windows
=======

If you use Windows you can install a virtual machine running linux. This plugin will then log into ssh and run `hh_client` remotely. You'll have to have your ssh credentials setup so you don't have to enter your password.

This plugin then defines three new settings.
 - hack_ssh_enable - enables ssh support
 - hack_ssh_folder - the remote folder to run `hh_client` on
 - hack_ssh_address - user@ipaddress

The plugin will fall back to locally executing `hh_client` if one of these settings is missing.

Example Preferences.sublime-settings
------------------------------------
To edit your settings go to
Preferences -> Settings - User

```
{
  "hack_ssh_folder": "/home/tim/project/",
  "hack_ssh_adress": "tim@10.0.0.1",
  "hack_ssh_enable": true
}
```
