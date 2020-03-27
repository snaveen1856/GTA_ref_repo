import os, logging
import sys, platform
from subprocess import Popen, PIPE

def doc_gen():
    
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    """checking sphinx installed or not."""
    try:
        import sphinx
    except Exception as err:
        logging.error(err)
        logging.info("Please install sphinx before running this script.")
        sys.exit(1)

    while True:
        question = input("Do you want to clone repository[y/n]:")
        s = ["y","yes","n","no"]
        if question.lower() in s:
            break
        else:
            print("Please enter either 'y/yes','n/no'")

    if question.lower() == 'y' or question.lower() == 'yes':
        for i in range(3):
            giturl = input("Enter your GIT url: ")
            if not "@bitbucket.org/mountdiablo" in giturl:
                logging.info("please provide correct url.")
                continue
            else:
                i = None
                break
        
        if i:
            raise Exception("Provided incorrect git url for 3 times.")
        
        """giturl validation check."""
        if giturl.startswith('https://') and giturl.endswith('.git'):
            """getting project name from the git url."""
            project = giturl.split('/')[-1]
            projectdir = project.split('.')[0]

            """check for git install or not."""
            try:
                git = os.system("git --version")
                if git != 0:
                    raise Exception("Git is not installed yet.")
            except Exception as err:
                logging.error(err)
                logging.info("please install git.")
                sys.exit(1)

            """Taking Giturl and clone the repository into ur local machine."""
            try:
                print("cloning started...please wait")
                result = os.system("git clone -q " + giturl)
                if result != 0:
                    raise Exception("Clonning unsuccessful.")
                print("cloning completed successfully...!")
            except Exception as err:
                logging.error(err)
                logging.info("cloning failed..please check ur git url.")
                sys.exit(1)

            try:
                os.chdir(projectdir)
            except Exception as err:
                logging.error(err)
                sys.exit(1)

            """Fetching and displaying all branchs in ur repository."""
            p = os.system("git branch -a")
            p = Popen(["git", "branch", "-a"], stdout=PIPE, stderr=PIPE,
                      stdin=PIPE, shell=True)
            out = p.communicate()
            if out[1]:
                raise Exception(out[1])
            else:
                output = out[0].split()
            branch = input("Please enter your branch name: ")
            if branch in output or ('remotes/origin/'+branch) in output:
                logger.info("branch name is valid.")
            else:
                raise Exception("Provided branch is not in list")

            """switching to your branch."""
            try:
                result = os.system("git checkout " + branch)
                if result != 0:
                    raise Exception("can't find your branch.")
            except Exception as err:
                logging.error(err)
                logging.info("please check your above branch list and try again.")
                sys.exit(1)
        else:
            logging.error("Invalid giturl,please enter a valid giturl.")
            sys.exit(1)
    else:
        projectpath = input("please enter your project directory full path:")
        if ":" in projectpath or projectpath.startswith("/"):
            if platform.uname()[0].lower() == "windows":
                projectpath = projectpath.strip("\\")
                projectdir = projectpath.split('\\')[-1]
            else:
                projectpath = projectpath.strip("/")
                projectdir = projectpath.split('/')[-1]
        try:
            if os.path.isdir(projectpath):
                os.chdir(projectpath)
            else:
                raise Exception("Provided project path doesn't exist.")
        except Exception as err:
            logging.error(err)
            sys.exit(1)

    sutas_path = os.path.join(os.getcwd(), "SUTAS")
    os.chdir(os.path.expanduser("~"))
    while True:
        outputdir = input("enter a name for your output directory: ")
        if os.path.isdir(outputdir):
            logging.info("directory with same name already exists in users "
                         "home directory. Please enter a different name")
        else:
            break

    """creating output directory inside users home directory."""
    result = os.system("sphinx-apidoc -F -o " + outputdir + " " + sutas_path)
    if result != 0:
        raise Exception("Pleae make sure Sphinx is installed.")

    conf = os.path.join(os.getcwd(), outputdir,"conf.py")
    with open(conf, "r+") as fp:
        data = fp.readlines()
        data.insert(1, "import sys\n")
        line = "sys.path.insert(0, '%s')\n" %os.getcwd()
        data.insert(2, line)
        fp.writelines(data)
    os.system(os.path.join(outputdir, "make.bat html"))

if __name__ == '__main__':
    doc_gen()
