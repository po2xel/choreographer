import shutil
import platform
import os

chrome = ["chrome", "Chrome", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]
chromium = ["chromium", "chromium-browser"]
# firefox = // this needs to be tested
# brave = // this needs to be tested
# edge = // this needs to be tested

system = platform.system()

default_path_chrome = None
if system == "Windows":
    default_path_chrome = [
            r"c:\Program Files\Google\Chrome\Application\chrome.exe"
            ]
elif system == "Linux":
    default_path_chrome = [
            "/usr/bin/google-chrome-stable"
            ]
else: # assume mac, or system == "Darwin"
    default_path_chrome = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            ]

def which_windows_chrome():
    try:
        import winreg
        import re

        command = winreg.QueryValueEx(
            winreg.OpenKey(
                winreg.HKEY_CLASSES_ROOT,
                "ChromeHTML\\shell\\open\\command",
                0,
                winreg.KEY_READ,
            ),
            "",
        )[0]
        exe = re.search('"(.*?)"', command).group(1)
        return exe
    except BaseException:
        return None

def _is_exe(path):
    res = False
    try:
        res = os.access(path, os.X_OK)
    finally:
        return res

def which_browser(executable_name=chrome):
    path = None
    if isinstance(executable_name, str):
        executable_name = [executable_name]
    if platform.system() == "Windows":
        os.environ["NoDefaultCurrentDirectoryInExePath"] = "0"
    for exe in executable_name:
        if platform.system() == "Windows" and exe == "chrome":
            path = which_windows_chrome()
            if path and _is_exe(path):
                return path
        path = shutil.which(exe)
        if path and _is_exe(path):
            return path
    if not path:
        default_path = []
        if executable_name == chrome:
            default_path = default_path_chrome
        for candidate in default_path:
            if _is_exe(candidate):
                return default_path
    return None
