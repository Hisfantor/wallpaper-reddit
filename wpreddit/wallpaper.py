import ctypes
import os
import random
import re
import shutil
import sys
from subprocess import check_call, check_output, CalledProcessError

from wpreddit import config


def set_wallpaper():
    if config.opsys == "Windows":
        ctypes.windll.user32.SystemParametersInfoW(0x14, 0, config.walldir + "\\wallpaper.bmp", 0x3)
    elif config.opsys == "Darwin":
        path = os.path.expanduser(config.walldir + "/wallpaper.jpg")
        try:
            check_call(["sqlite3", "~/Library/Application Support/Dock/desktoppicture.db", "\"update",
                                   "data", "set", "value", "=", "'%s'\"" % path])
            check_call(["killall", "dock"])
        except CalledProcessError or FileNotFoundError:
            print("Setting wallpaper failed.  Ensure all dependencies listen in the README are installed.")
            sys.exit(1)
    else:
        linux_wallpaper()
    print("wallpaper set command was run")


def linux_wallpaper():
    de = os.environ.get('DESKTOP_SESSION')
    path = os.path.expanduser(config.walldir + "/wallpaper.jpg")
    try:
        if config.setcmd != '':
            check_call(config.setcmd, shell=True)
        elif de in ["gnome", "gnome-xorg", "gnome-wayland", "unity", "ubuntu", "budgie-desktop"]:
            check_call(["gsettings", "set", "org.gnome.desktop.background", "picture-uri",
                                   "file://%s" % path])
        elif de in ["cinnamon"]:
            check_call(["gsettings", "set", "org.cinnamon.desktop.background", "picture-uri",
                                   "file://%s" % path])
        elif de in ["pantheon"]:
            # Some disgusting hacks so that Pantheon will update the wallpaper
            # If the filename isn't changed, the wallpaper doesn't either
            files = os.listdir(config.walldir)
            for file in files:
                if re.search('wallpaper[0-9]+\.jpg', file) is not None:
                    os.remove(config.walldir + "/" + file)
            randint = random.randint(0, 65535)
            randpath = os.path.expanduser(config.walldir + "/wallpaper%s.jpg" % randint)
            shutil.copyfile(path, randpath)
            check_call(["gsettings", "set", "org.gnome.desktop.background", "picture-uri",
                                   "file://%s" % randpath])
        elif de in ["mate"]:
            check_call(["gsettings", "set", "org.mate.background", "picture-filename",
                                   "'%s'" % path])
        elif de in ["xfce", "xubuntu"]:
            # Light workaround here, just need to toggle the wallpaper from null to the original filename
            # xfconf props aren't 100% consistent so light workaround for that too
            props = check_output(['xfconf-query', '-c', 'xfce4-desktop', '-p', '/backdrop', '-l'])\
                    .decode("utf-8").split('\n')
            for prop in props:
                if "last-image" in prop or "image-path" in prop:
                    check_call(["xfconf-query", "-c", "xfce4-desktop", "-p", prop, "-s", "''"])
                    check_call(["xfconf-query", "-c", "xfce4-desktop", "-p", prop, "-s" "'%s'" % path])
                if "image-show" in prop:
                    check_call(["xfconf-query", "-c", "xfce4-desktop", "-p", prop, "-s", "'true'"])
        elif de in ["lubuntu", "Lubuntu"]:
            check_call(["pcmanfm", "-w", "%s" % path])
        elif config.setcmd == '':
            print("Your DE could not be detected to set the wallpaper. "
                  "You need to set the 'setcommand' paramter at ~/.config/wallpaper-reddit. "
                  "When you get it working, please file an issue.")
            sys.exit(1)
    except CalledProcessError or FileNotFoundError:
        print("Command to set wallpaper returned non-zero exit code.  Please file an issue or check your custom "
              "command if you have set one in the configuration file.")
        sys.exit(1)


# saves the wallpaper in the save directory from the config
# naming scheme is wallpaperN
def save_wallpaper():
    if not os.path.exists(config.savedir):
        os.makedirs(config.savedir)
        config.log(config.savedir + " created")
    if not os.path.isfile(config.savedir + '/titles.txt'):
        with open(config.savedir + '/titles.txt', 'w') as f:
            f.write('Titles of the saved wallpapers:')
        config.log(config.savedir + "/titles.txt created")

    wpcount = 0
    origpath = config.walldir
    newpath = config.savedir

    if config.opsys == "Windows":
        origpath = origpath + ('\\wallpaper.bmp')
        while os.path.isfile(config.savedir + '\\wallpaper' + str(wpcount) + '.bmp'):
            wpcount += 1
        newpath = newpath + ('\\wallpaper' + str(wpcount) + '.bmp')
    else:
        origpath = origpath + ('/wallpaper.jpg')
        while os.path.isfile(config.savedir + '/wallpaper' + str(wpcount) + '.jpg'):
            wpcount += 1
        newpath = newpath + ('/wallpaper'  + str(wpcount) + '.jpg')
    shutil.copyfile(origpath, newpath)

    with open(config.walldir + '/title.txt', 'r') as f:
        title = f.read()
    with open(config.savedir + '/titles.txt', 'a') as f:
        f.write('\n' + 'wallpaper' + str(wpcount) + ': ' + title)

    print("Current wallpaper saved to " + newpath)
