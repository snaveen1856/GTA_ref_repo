"""Setup script for SUTAS."""
import shutil
import tempfile
import sys
import platform
import os
import datetime
import re
import site
from subprocess import Popen, PIPE
from distutils import sysconfig
from setuptools import setup, find_packages

packages = find_packages()
directory = os.getcwd()

class MyWriter(object):
    """
        Class for logging stdout to a file
    """
    def __init__(self, stdout, filename):
        """
            Initializer
        """
        self.stdout = stdout
        self.logfile = open(filename, 'a')

    def write(self, text):
        """
            write stdout to a file
        """
        self.stdout.write(text)
        self.logfile.write(text)

    def flush(self):
        """
            flush stdout method
        """
        pass

    def close(self):
        """
            close stdout method
        """
        self.stdout.close()
        self.logfile.close()

os_type = platform.uname()[0]

with open("sutas_install.log", "a") as log:
    hash1 = "###########################################"
    time_stamp = 2 * hash1 + "\n****Installation Started at " + \
        str(datetime.datetime.now()) + "****\n" + 2 * hash1 + "\n"
    print(time_stamp)
    log.write(time_stamp)

if "develop" in sys.argv:
    def install_cmd(pack,pypi_files, sym):
        """install package using pip."""
        for k in pypi_files:
            if pack.split(sym)[0] in k:
                pypi_path = pypi + '\\' + k
                cmd = ["pip3.7", "install", pypi_path]
                result = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE)
                output = result.stdout.read()
                print(output)
                with open("sutas_install.log", "a") as fp:
                    fp.write(output)

    def install_requirements(pypi_files):
        """Install the requirements."""
        with open(os.path.join(directory, 'requirements.txt'), 'r') as req_file:
            packs = req_file.readlines()

            for pack in packs:
                if '>' in pack:
                    install_cmd(pack, pypi_files, sym='>')
                elif '=' in pack:
                    install_cmd(pack, pypi_files, sym='=')
    package_dir = None
    for i in sys.argv[1:]:
        if '--find-links' in i:
            package_dir = i
    if package_dir is None:
        sys.exit()
    else:
        pypi = package_dir.split("=")[-1]
        pypi_files = os.listdir(pypi)
        install_requirements(pypi_files)

def get_sutaspkgs_win(site_packages_path,sutas_pattern):
    pkgslist = os.listdir(site_packages_path)
    pkgs = list(filter(sutas_pattern.match, pkgslist))
    sutas_pkgs = [os.path.join(site_packages_path, pkg) for pkg in pkgs]
    return sutas_pkgs
def get_sutaspkgs_lin(site_packages_path,sutas_pattern):
    pkgslist = []
    sutas_pkgs = []
    if len(site_packages_path) > 1:
        for sitepkg in site_packages_path:
            if 'site-python' in sitepkg:
                continue
            pkgslist = os.listdir(sitepkg)
            pkgs = list(filter(sutas_pattern.match, pkgslist))
            if pkgs:
                site_packages_path = sitepkg
                break
        sutas_pkgs = [os.path.join(site_packages_path, pkg) for pkg in pkgs]
    return sutas_pkgs
user_temp_dir = tempfile.gettempdir()
sutas_pattern = re.compile("SUTAS.*")

if os_type == "Windows":
    site_packages_path = sysconfig.get_python_lib()
    scripts_path = os.path.join(sys.prefix, 'Scripts')
    sutas_pkgs = get_sutaspkgs_win(site_packages_path,sutas_pattern)
    print("Found {} SUTAS packages".format(len(sutas_pkgs)))
    if len(sutas_pkgs) != 0:
        latest_sutasdir = max(sutas_pkgs, key=os.path.getmtime)
        for sutasver in sutas_pkgs:
            if sutasver != latest_sutasdir:
                shutil.rmtree(sutasver)         
        sutas_dirname = os.path.basename(latest_sutasdir)
        sutas_temp = os.path.join(user_temp_dir, sutas_dirname)
        temp_sutas_bat = os.path.join(user_temp_dir, 'sutas.bat')
        temp_sutas_py = os.path.join(user_temp_dir, 'sutas.py')
        scripts_sutas_bat = os.path.join(scripts_path, 'sutas.bat')
        scripts_sutas_py = os.path.join(scripts_path, 'sutas.py')
        
        if os.path.exists(sutas_temp):
            shutil.rmtree(sutas_temp)        
        #Backup latest Sutas in site-packages to temp directory.
        shutil.copytree(latest_sutasdir, sutas_temp)
        #Backup sutas.py and sutas.bat from Scripts folder to temp folder.
        shutil.copyfile(scripts_sutas_bat,temp_sutas_bat)
        shutil.copyfile(scripts_sutas_py,temp_sutas_py)
        shutil.copyfile(os.path.join(os.getcwd(),'testData','testenvdata.yaml'),os.path.join(os.path.expanduser('~'),'testenvdata.yaml'))
        first = False
        if os.path.exists(latest_sutasdir):
            shutil.rmtree(latest_sutasdir)        
    else:
        first = True
        print('Installing this SUTAS version for the first time')
else:
    temp_sutas_py = os.path.join(user_temp_dir, 'sutas.py')
    bin_sutas_py = "/usr/local/bin/sutas.py"
    lib_sutas_py = os.path.join(os.getcwd(), "lib/sutas.py")
    shutil.copyfile(lib_sutas_py,bin_sutas_py)
    os.system("ln -s  " + "/usr/local/bin/sutas.py /usr/local/bin/sutas")
    os.system("chmod 777 /usr/local/bin/sutas.py")
    site_packages_path = site.getsitepackages()
    sutas_pkgs = get_sutaspkgs_lin(site_packages_path,sutas_pattern)
    print("Found {} SUTAS packages".format(len(sutas_pkgs)))
    if len(sutas_pkgs) != 0:
        latest_sutasdir = max(sutas_pkgs, key=os.path.getmtime)
        for sutasver in sutas_pkgs:
            if sutasver != latest_sutasdir:
                shutil.rmtree(sutasver)         
        sutas_dirname = os.path.basename(latest_sutasdir)
        sutas_temp = os.path.join(user_temp_dir, sutas_dirname)
        if os.path.exists(sutas_temp):
            shutil.rmtree(sutas_temp)
        shutil.copytree(latest_sutasdir, sutas_temp)
        shutil.copyfile(bin_sutas_py, temp_sutas_py)
        shutil.copyfile(os.path.join(os.getcwd(),'testData','testenvdata.yaml'),os.path.join(os.path.expanduser('~'),'testenvdata.yaml'))
        first = False
        if os.path.exists(latest_sutasdir):
            shutil.rmtree(latest_sutasdir)        
    else:
        first = True
        print('Installing this SUTAS version for the first time')
    
with open("requirements.txt", "r") as req:
    requirements = req.readlines()
requirements = [i.strip() for i in requirements]
#import pdb; pdb.set_trace()

def pkg_install():
    """
        install pip packages
    """
    for pkg in requirements:
        cmd = ["pip3.7", "install", pkg]
        result = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE)
        out = result.stdout.read()
        err = result.stderr.read()
        output = str(out) + "\n" + str(err)
        print(output)
        with open("sutas_install.log", "a") as fp:
            fp.write(output)
def update_easy_install_path(site_packages_path,latest_sutasdir):
    with open(os.path.join(site_packages_path,'easy-install.pth'),'r') as pthdata:
        data = pthdata.readlines()
    for val in data:
        if 'sutas' in val:
            data[data.index(val)] = './' + os.path.basename(latest_sutasdir).lower()
    with open(os.path.join(site_packages_path,'easy-install.pth'),'w') as pthdata:
        pthdata.writelines(data)
        
if '--no-packages' in sys.argv:
    sys.argv.remove('--no-packages')
else:
    pkg_install()

writer = MyWriter(sys.stdout, 'sutas_install.log')
sys.stdout = writer
try:
    setup(name='SUTAS',
          version='1.7',
          description='Sungard Unified Test Automation System',
          author='Sungard',
          author_email='ramarao.kedarasetti@sungardas.com',
          zip_safe=False,
          packages=packages,
          include_package_data=True,)
    if os_type.lower() == 'windows':
        shutil.copyfile(os.path.join(directory, 'lib', 'sutas.bat'),
                        os.path.join(scripts_path, 'sutas.bat'))
        shutil.copyfile(os.path.join(directory, 'lib', 'sutas.py'),
                        os.path.join(scripts_path, 'sutas.py'))
    time_stamp = "\n\n****Installation Completed at " + \
        str(datetime.datetime.now()) + "****\n\n"
    print(time_stamp)

    print("Checking Installation status of SUTAS.........")
    status = os.system('sutas -h')
    if status != 0:
        raise Exception("SUTAS is not installed properly So restoring sutas if backup found")
except Exception as err:
    print("Installation failed hence restoring to previous installed version.")
    if not first and os_type.lower() == 'windows':
        if len(sutas_pkgs) != 0:
            if sutas_temp and latest_sutasdir:
                sutas_pkgs = get_sutaspkgs_win(site_packages_path,sutas_pattern)
                for s_pkg in sutas_pkgs:
                    if os.path.exists(s_pkg):
                        shutil.rmtree(s_pkg)
                        
                #Restores sutas.py and sutas.bat from temp to scripts path
                shutil.copyfile(temp_sutas_py,scripts_sutas_py)
                shutil.copyfile(temp_sutas_bat,scripts_sutas_bat)
                
                #Restores sutas from temp folder to site-packages
                shutil.copytree(sutas_temp, latest_sutasdir)
                print("Restored succesfully")
                #Updating the easy_install.pth file.
                update_easy_install_path(site_packages_path,latest_sutasdir)               
        else:
            print("No sutas backup found")
    else:
        if len(sutas_pkgs) != 0:
            if sutas_temp and latest_sutasdir:
                shutil.copyfile(temp_sutas_py, bin_sutas_py)
                os.system("ln -s  " + "/usr/local/bin/sutas.py /usr/local/bin/sutas")
                sutas_pkgs = get_sutaspkgs_lin(site_packages_path,sutas_pattern)
                for s_pkg in sutas_pkgs:
                    if os.path.exists(s_pkg):
                        shutil.rmtree(s_pkg)
                shutil.copytree(sutas_temp, latest_sutasdir)
                print("Restored succesfully")
                #Updating the easy_install.pth file.
                update_easy_install_path(os.path.dirname(latest_sutasdir),latest_sutasdir)               
        else:
            print("No sutas backup found")
    raise Exception(err)


def check_openssl(os_type=os_type):
    """
    WinXP-32: x86
    Vista-32: x86
    Win7-64: AMD64
    Debian-32: i686
    Debian-64: x86_64
    """
    os_bit = 32
    if platform.machine().endswith('64'):
        os_bit = 64
        if os_type == "Windows":
            sslpath = "OpenSSL-Win%s" % os_bit
            sslpath = os.path.join("C:\\", sslpath)
            if os.path.exists(sslpath):
                print("Openssl is installed Successfully")
                print("Checking if Openssl Path is set or not........")
                if 'INCLUDE' and 'OPENSSL_CONF' and 'LIB' in os.environ:
                    includepath = os.path.join(sslpath, 'include')
                    if includepath not in os.environ['INCLUDE']:
                        sslmsg = "Please set 'INCLUDE' path as {}".format(
                            includepath)
                        raise Exception(sslmsg)
                    confpath = os.path.join(sslpath, 'bin', 'openssl.cfg')
                    if confpath not in os.environ['OPENSSL_CONF']:
                        sslmsg = "Please set 'OPENSSL_CONF' path as {}".format(
                            confpath)
                        raise Exception(sslmsg)
                    libpath = os.path.join(sslpath, 'lib')
                    if libpath not in os.environ['LIB']:
                        sslmsg = "Please set 'lib' path as {}".format(
                            libpath)
                        raise Exception(sslmsg)
                    print("Openssl path is set")
                else:
                    raise Exception(
                        'Openssl is installed.Need to set path.Please follow installation guide')
            else:
                raise Exception('Openssl is not installed succesfully')
        else:
            cmd = 'gcc -v'
            val = os.system(cmd)
            if val != 0:
                raise Exception('gcc is not installed.')


def check_pkgs(imps, os_type='Windows'):
    """ Checks the installation status of installed packages """
    for imp in imps:
        msg = 'python -c "import {}"'.format(imp)
        print("Checking package {} ..............".format(imp))
        val = os.system(msg)
        if val == 1:
            if imp == 'Crypto' and os_type == 'Windows':
                url = 'https://www.microsoft.com/en-in/download/details.aspx?id=44266'
                print("Please check VC for Python2.7 is installed or not.")
                print("Download VC++ from the url {}".format(url))
            raise Exception("Module %s is not installed" % imp)


imps = ["base64", "os", "hashlib", "Crypto", "robot", "winrm", "sys",
        "traceback", "paramiko", "re", "yaml", "requests", "warnings",
        "datetime", "random", "yaml", "jira", "logging", "smtplib", "email",
        "sqlalchemy", "xml", "socket", "six", "platform",
        "multiprocessing", "psutil", "requests", "getpass", "bs4"]
check_openssl(os_type=os_type)
check_pkgs(imps, os_type=os_type)
