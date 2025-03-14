import os
import sys
import ctypes
from configparser import ConfigParser
import zipfile
import requests
import subprocess
import shutil
from bs4 import BeautifulSoup

# Global variables
first = True
command = "req"
install_mode = "Auto"

def is_admin():
    """Checks if the script is being run as administrator"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def elevate_privileges():
    """Attempts to elevate script privileges"""
    if not is_admin():
        print("This program needs to be run as administrator!")
        print("Attempting to restart with elevated privileges...")
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit()
        except:
            print("Error elevating privileges. Please run the program as administrator manually.")
            sys.exit(1)

def load_config():
    """Loads and returns configurations from the config.ini file"""
    if not os.path.exists("config.ini"):
        print("Error: config.ini file not found!")
        create_default_config()
    config = ConfigParser()
    try:
        config.read("config.ini")
        return {
            'vs_url': str(config["Settings"]["vs_link"]),
            'update': config["Settings"]["update"],
            'skia_url': config["Settings"]["skia_link"],
            'ninja_url': config["Settings"]["ninja_link"],
            'n_p': config["Settings"]["ninja_path"],
            'p_path': config["Settings"]["p_path"],
            'aseprite_path': config["Settings"]["aseprite_path"],
            'aseprite_link': config["Settings"]["aseprite_link"]
        }
    except Exception as e:
        print(f"Error: Configuration file corrupted or does not exist! {str(e)}")
        sys.exit(1)

def create_default_config():
    """Creates default configuration file"""
    config = ConfigParser()
    config['Settings'] = {
        'vs_link': 'https://aka.ms/vs/17/release/vs_community.exe',
        'skia_link': 'https://github.com/aseprite/skia/releases/latest/download/Skia-Windows-Release-x64.zip',
        'ninja_link': 'https://github.com/ninja-build/ninja/releases/latest/download/ninja-win.zip',
        'aseprite_link': 'https://github.com/aseprite/aseprite.git',
        'ninja_path': 'C:/Program Files/CMake/bin',
        'p_path': 'C:/Program Files/',
        'aseprite_path': 'C:/',
        'update': 'True'
    }

    with open('config.ini', 'w') as f:
        config.write(f)
    print("config.ini file created with default settings")

config = load_config()

if config['update'] == "True":
    if os.path.isdir("Git"):
        shutil.rmtree("Git")

    # Replacing requests_html with BeautifulSoup
    git_r = requests.get("https://github.com/git-for-windows/git/releases/")
    soup = BeautifulSoup(git_r.content, 'lxml')
    links = [a.get('href') for a in soup.find_all('a', href=True)]
    git_url = None
    for link in links:
        if isinstance(link, str) and "MinGit" in link and "64" in link and "busybox" not in link:
            git_url = "https://github.com" + link
            break

    cmake_r = requests.get("https://cmake.org/download/")
    soup = BeautifulSoup(cmake_r.content, 'lxml')
    links = [a.get('href') for a in soup.find_all('a', href=True)]
    cmake_url = None
    for link in links:
        if isinstance(link, str) and "windows" in link and "msi" in link and "64" in link:
            cmake_url = link
            break

    r_vs = requests.get(config['vs_url'])
    r_git = requests.get(git_url)
    r_cmake = requests.get(cmake_url)
    r_skia = requests.get(config['skia_url'])
    r_ninja = requests.get(config['ninja_url'])

    os.mkdir("Git")

    open("Git.zip", "wb").write(r_git.content)
    open("vs.exe", "wb").write(r_vs.content)
    open("cmake.msi", "wb").write(r_cmake.content)
    open("skia.zip", "wb").write(r_skia.content)
    open("ninja.zip", "wb").write(r_ninja.content)

    with zipfile.ZipFile("Git.zip", "r") as zf:
        zf.extractall("Git")

    os.remove("Git.zip")

    os.system("cmake.msi")

    os.remove("cmake.msi")

    os.system("vs.exe")

    os.remove("vs.exe")

    config.set("Settings", "update", "False")

    with open("config.ini", "w") as configfile:
        config.write(configfile)

def change_install_mode(mode):
    """Changes the installation mode"""
    global install_mode
    install_mode = mode
    print(f"Success! Installation mode changed to: {install_mode}")

def Install():
    with open("Install.bat", "w") as f:
        f.write("SET PATH=%PATH%;" + os.getcwd() + "/Git/cmd" + "\n")
        f.write("cd " + config['aseprite_path'] + "\n")
        f.write("git clone --recursive " + config['aseprite_link'])

    subprocess.call(["Install.bat"])

    os.remove("Install.bat")

    skia_path = "skia.zip"
    ninja_path = "ninja.zip"

    try:
        with zipfile.ZipFile(skia_path, "r") as zf:
            zf.extractall(config['aseprite_path'] + "deps/skia")

        with zipfile.ZipFile(ninja_path, "r") as zf:
            zf.extractall(config['n_p'])

    except Exception as e:
        print(e)

    if os.path.isdir(config['p_path'] + "Microsoft Visual Studio/2022/Community/Common7/Tools"):
        build_aseprite(
            config['p_path'] + 'Microsoft Visual Studio/2022/Community/Common7/Tools/VsDevCmd.bat'
        )

    elif os.path.isdir(config['p_path'][:-1] + " (x86)" + "/Microsoft Visual Studio/2019/Community/Common7/Tools"):
        build_aseprite(
            config['p_path'][:-1] + " (x86)" + '/Microsoft Visual Studio/2019/Community/Common7/Tools/VsDevCmd.bat'
        )

    else:
        print("No Visual Studio installation found. Please refer to https://github.com/TheLiteCrafter/AsepriteTool")

    os.system('shortcut /a:c /f:"C:/ProgramData/Microsoft/Windows/Start Menu/Programs/Aseprite.lnk" /t:"' + config['aseprite_path'] + 'aseprite/build/bin/aseprite.exe"')

    print("Done! Finished Compiling Aseprite! It can be found by searching for aseprite in the start menu")
    os.remove("cmd.bat")

def build_aseprite(vs_cmd_path):
    """Aseprite compilation function"""
    try:
        print("Starting compilation...")
        with open("cmd.bat", "w", encoding='utf-8') as f:
            f.write("@echo off\n")
            f.write(f'call "{vs_cmd_path}" -arch=x64\n')
            f.write(f"cd {config['aseprite_path']}aseprite\n")
            f.write("if not exist build mkdir build\n")
            f.write(f"cd {config['aseprite_path']}aseprite/build\n")
            f.write(f"cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo -DLAF_BACKEND=skia "
                            f"-DSKIA_DIR={config['aseprite_path']}deps/skia "
                            f"-DSKIA_LIBRARY_DIR={config['aseprite_path']}deps/skia/out/Release-x64 "
                            f"-DSKIA_LIBRARY={config['aseprite_path']}deps/skia/out/Release-x64/skia.lib "
                            "-G Ninja ..\n")
            f.write("ninja aseprite")

        result = subprocess.run(["cmd.bat"], capture_output=True, text=True, shell=True)
        if result.returncode != 0:
            print(f"Compilation error: {result.stderr}")
            return False
        return True

    except Exception as e:
        print(f"Error executing build: {str(e)}")
        return False
    finally:
        if os.path.exists("cmd.bat"):
            try:
                os.remove("cmd.bat")
            except:
                pass

def Update():
    """Update function"""
    try:
        # Check if Git is installed and available
        if not os.path.exists(os.path.join(os.getcwd(), "Git", "cmd", "git.exe")):
            print("Git not found. Reinstalling dependencies...")
            if config['update'] == "False":
                config['update'] = "True"
                return False

        # Check if the aseprite directory exists
        aseprite_dir = os.path.join(config['aseprite_path'], "aseprite")
        if not os.path.isdir(aseprite_dir):
            print(f"Aseprite directory not found in {aseprite_dir}")
            print("Changing to install mode...")
            return Install()

        print("Updating Aseprite...")
        with open("cmd.bat", "w", encoding='utf-8') as f:
            f.write("@echo off\n")
            f.write("SET PATH=%PATH%;" + os.path.join(os.getcwd(), "Git", "cmd") + "\n")
            f.write(f"cd {aseprite_dir}\n")
            f.write("git pull\n")
            f.write("git submodule update --init --recursive\n")

        result = subprocess.run(["cmd.bat"], capture_output=True, text=True, shell=True)
        if result.returncode != 0:
            print(f"Error executing git pull: {result.stderr}")
            return False

        print("Compiling Aseprite...")
        vs_paths = [
            os.path.join(config['p_path'], "Microsoft Visual Studio/2022/Community/Common7/Tools/VsDevCmd.bat"),
            os.path.join(config['p_path'][:-1] + " (x86)", "Microsoft Visual Studio/2019/Community/Common7/Tools/VsDevCmd.bat")
        ]

        vs_path = next((path for path in vs_paths if os.path.isfile(path)), None)

        if vs_path:
            if build_aseprite(vs_path):
                try:
                    shortcut_cmd = f'shortcut /a:c /f:"C:/ProgramData/Microsoft/Windows/Start Menu/Programs/Aseprite.lnk" /t:"{os.path.join(config["aseprite_path"], "aseprite/build/bin/aseprite.exe")}"'
                    subprocess.run(shortcut_cmd, shell=True, check=True)
                    print("Update completed successfully!")
                    return True
                except subprocess.CalledProcessError:
                    print("Error creating shortcut, but compilation was completed.")
                    return True
        else:
            print("Visual Studio not found. Please install Visual Studio Community.")
            return False

    except Exception as e:
        print(f"Error during update: {str(e)}")
        return False
    finally:
        if os.path.exists("cmd.bat"):
            try:
                os.remove("cmd.bat")
            except:
                pass

def main():
    """Main function of the program"""
    elevate_privileges()  # Checks privileges at the beginning
    global first, command
    config = load_config()

    while True:
        if not first:
            command = input("Please enter a command: ").lower()

        try:
            if command == "help":
                print("""Available command list:
help - Shows available command list
start - Starts the installation/update process
exit - Exits the program
req - Shows all requirements
installmode Auto/Update/Install - Changes the installation mode""")

            elif command == "installmode auto":
                change_install_mode("Auto")

            elif command == "installmode install":
                change_install_mode("Install")

            elif command == "installmode update":
                change_install_mode("Update")

            elif command == "exit":
                sys.exit()

            elif command == "start":

                if install_mode == "Auto":

                    if os.path.isdir(config['aseprite_path'] + "aseprite") and os.path.isdir(config['aseprite_path'] + "deps"):
                        print("Update Mode detected.")
                        if not Update():
                            print("Update failed. Check the logs above.")

                    else:
                        print("Install mode detected.")
                        if not Install():
                            print("Installation failed. Check the logs above.")

                elif install_mode == "Install":
                    if not Install():
                        print("Installation failed. Check the logs above.")

                elif install_mode == "Update":
                    if not Update():
                        print("Update failed. Check the logs above.")

            elif command == "req":
                try:
                    r = requests.get("https://github.com/aseprite/aseprite/blob/main/INSTALL.md")
                    soup = BeautifulSoup(r.content, 'lxml')
                    content = soup.get_text()
                    if 'Desktop development with C++' in content:
                        sdk = "Windows 10 SDK (10.0.19041.0)"
                    else:
                        sdk = "Windows SDK required"

                    print("Requirements: ")
                    print("")
                    print("Visual Studio and Cmake will be downloaded automatically. In Cmake, don't forget to select add to Path for all users, and in Visual Studio, Desktop development with C++ and, in Individual Components, " + sdk)
                except Exception as e:
                    print("Error getting requirements. Please check your internet connection.")
                    print(f"Error: {str(e)}")

            first = False

        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            print("Please try again or run the program as administrator.")

if __name__ == "__main__":
    main()
