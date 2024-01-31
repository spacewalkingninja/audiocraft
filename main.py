import os
import sys
import shutil
import time
import json
import argparse
import random
import subprocess
# Define the output path for the synthesized video

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
# DeSOTA Funcs [START]
#   > Import DeSOTA Scripts
from desota import detools
#   > Grab DeSOTA Paths
USER_SYS = detools.get_platform()
APP_PATH = os.path.dirname(os.path.realpath(__file__))
TMP_PATH = os.path.join(CURRENT_PATH, f"tmp")
#IN_PATH = os.path.join(CURRENT_PATH, f"in")
#   > USER_PATH
if USER_SYS == "win":
    path_split = str(APP_PATH).split("\\")
    desota_idx = [ps.lower() for ps in path_split].index("desota")
    USER=path_split[desota_idx-1]
    USER_PATH = "\\".join(path_split[:desota_idx])
elif USER_SYS == "lin":
    path_split = str(APP_PATH).split("/")
    desota_idx = [ps.lower() for ps in path_split].index("desota")
    USER=path_split[desota_idx-1]
    USER_PATH = "/".join(path_split[:desota_idx])
DESOTA_ROOT_PATH = os.path.join(USER_PATH, "Desota")
CONFIG_PATH = os.path.join(DESOTA_ROOT_PATH, "Configs")
SERV_CONF_PATH = os.path.join(CONFIG_PATH, "services.config.yaml")

ENV_PATH = os.path.join(DESOTA_ROOT_PATH,"Portables","Transformers")


TMP_PATH = os.path.join(CURRENT_PATH, f"tmp")
OUT_PATH = os.path.join(TMP_PATH, f"out.mp4")
OUT_NAME = "out"
DEF_DATA = os.path.join(CURRENT_PATH, f"data")
DEF_MOON = os.path.join(DEF_DATA, f"test.wav")
INF_PATH = os.path.join(CURRENT_PATH, f"inference.py")

preseed = int(random.randint(1, 1000000))  # Generate a random seed

#parser = argparse.ArgumentParser()

DEFAULT_OUT_PATH = os.path.join(f"music.wav")
# Create an argument parser
parser = argparse.ArgumentParser(description="AI Audio With Text Control Synthesis CLI")
parser.add_argument("-p", "--prompt", default="enter_cli_mode", help="Text description of target audio", type=str)
parser.add_argument("-ap", "--audio_path", default=DEF_MOON, help="Path to the source audio file", type=str)
parser.add_argument("-al", "--audio_length", help="Length of synthesized audio", default=1503, type=int)
parser.add_argument("-gs", "--guidance_scale", help="Guidance scale", default=3, type=int)
parser.add_argument("-m", "--mode", help="This is the mode, def = 1 = Text to Music ignore additional audio_path, 2 = Audio + Text to Music , 3 = Audio Continuation only, 4 = music to music", default=1, type=int)





parser.add_argument("-rp", "--respath", 
                    help=f'Output filename`',
                    default=str(DEFAULT_OUT_PATH),
                    type=str)
parser.add_argument('-nc', '--noclear',
                    help='Service Status Request',
                    action='store_true')

args = parser.parse_args()



args.prompt = args.prompt

DEBUG = True
    
# UTILS
def pcol(obj, template, nostart=False, noend=False):
    '''
    # Description
        print with colors
    # Arguments
    {
        obj: {
            desc: object to print, parsed into string
        },
        template: {
            desc: template name,
            options: [
                header1,
                header2,
                section,
                title,
                body,
                sucess,
                fail
            ]
        }
    }
    '''
    _configs = {
        "header1": "\033[1;105m",
        "header2": "\033[1;95m",
        "search": "\033[104m",
        "section": "\033[94m",
        "title": "\033[7m",
        "body": "\033[97m",
        "sucess": "\033[92m",
        "fail": "\033[91m",
        "end": "\033[0m"
    }
    _morfed_obj = ""
    # PARSE OBJ INTO STR
    if isinstance(obj, list) or isinstance(obj, dict):
        _morfed_obj = json.dumps(obj, indent=2)
    elif not isinstance(obj, str):
        try:
            _morfed_obj = str(obj)
        except:
            # Last ressource
            pass
    else:
        _morfed_obj = obj

    if template in _configs and (_morfed_obj or _morfed_obj==""):
        return f"{_configs[template] if not nostart else ''}{_morfed_obj}{_configs['end'] if not noend else ''}"
    else:
        return obj

def AudioThread(query, args=args):
    prompt = query
    args = args
    res = None
    # Check that required arguments are provided
    if not args.prompt :
        exit(1)

    # Convert source video path to Path object
    audio_path = args.audio_path
    output_path = args.respath
    if int(args.mode)>1:
        if not os.path.isfile(audio_path):
            exit(1)
    try:
        shutil.rmtree(TMP_PATH)
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))

    os.makedirs(TMP_PATH, exist_ok=True)

    if USER_SYS == "win":
        _model_runner_py = os.path.join(ENV_PATH, "env", "python.exe")
    elif USER_SYS == "lin":
        _model_runner_py = os.path.join(ENV_PATH, "env", "bin", "python3")

    # Build the command for subprocess
    command = [
        _model_runner_py,
        INF_PATH,
        "--prompt", str(args.prompt),
        "--audio_path", str(audio_path),
        "--model_mode", str(args.mode),
        "--output_path", str(TMP_PATH),  # You may need to adjust this
        "--output_name", str(args.respath),  # You may need to adjust this
        "--audio_length", str(args.audio_length),
#            "--smoother_steps", str(f'"{args.smoother_steps}"'),
        "--guidance_scale", str(args.guidance_scale),
    ]

    # Execute the subprocess
    subprocess.check_output(" ".join(command))
    return OUT_PATH

def main(args):
    if args.prompt == "enter_cli_mode":
        if not args.noclear:
            os.system("cls" if sys.platform == "win32" else "clear" )
        print(pcol("Welcome to Desota AI Audiocraft Music Text Control CLI ", "header1"), pcol("by © DeSOTA, 2024", "header2"))
        print(pcol("Edit and make music with text!\n", "body"))

        while True:
            print(pcol("*"*80, "body"))

            # Get User Query
            _user_query = ""
            _exit = False
            try:
                _input_query_msg = "".join([pcol("What is your text prompt? ('exit' to exit)\n-------------------------------------------\n|", "search"), pcol("", "title", noend=True)])
                _user_query = input(_input_query_msg)
            except KeyboardInterrupt:
                _exit = True
                pass
            if _user_query in ["exit", "Exit", "EXIT"] or _exit:
                print(pcol("", "title", nostart=True))
                return
            print(f'{pcol("", "title", nostart=True)}{pcol("-------------------------------------------", "search")}')
            #now we have to make this kind of question for every item of args.
            #and at the end display them all
            # and ask you sure you wanna go with these settings? Y/N

            args.prompt = _user_query
            args.prompt = _user_query



            # Get User Input for -vp/--audio_path Argument
            try:
                _user_query = input(f"Enter the MODE (1=Text2Music;2=Text+Music2Music;3=MusicContinuation;4=Music2Music): ")
            except KeyboardInterrupt:
                print()
                return
            if _user_query.lower() in ["exit"] or _exit:
                print(pcol("", "title", nostart=True))
                return
            print(f'{pcol("", "title", nostart=True)}{pcol("-------------------------------------------", "search")}')
            args.mode = int(_user_query) if _user_query else 1
            
            # Get User Input for -vp/--audio_path Argument
            try:
                _user_query = input(f"Enter the path to the source audio file (default is {DEF_MOON}): ")
            except KeyboardInterrupt:
                print()
                return
            if _user_query.lower() in ["exit"] or _exit:
                print(pcol("", "title", nostart=True))
                return
            print(f'{pcol("", "title", nostart=True)}{pcol("-------------------------------------------", "search")}')
            args.audio_path = _user_query if _user_query else DEF_MOON

            # Get User Input for -c/--condition Argument
            try:
                _user_query = input("Enter the guidance scale default is 3 from 0 to 4: ")
            except KeyboardInterrupt:
                print()
                return
            if _user_query.lower() in ["exit"] or _exit:
                print(pcol("", "title", nostart=True))
                return
            print(f'{pcol("", "title", nostart=True)}{pcol("-------------------------------------------", "search")}')
            args.guidance_scale = str(_user_query)

            # Get User Input for -vl/--video_length Argument
            try:
                _user_query = input("Enter the length of synthesized audio (default is 1503 which equals to 30 sec): ")
            except KeyboardInterrupt:
                print()
                return
            if _user_query.lower() in ["exit"] or _exit:
                print(pcol("", "title", nostart=True))
                return
            print(f'{pcol("", "title", nostart=True)}{pcol("-------------------------------------------", "search")}')
            args.audio_length = int(_user_query) if _user_query else 1503


            os.system("cls" if sys.platform == "win32" else "clear" )
            print(pcol("Desota AI Audiocraft Music Text Control CLI ", "header1"), pcol("by © DeSOTA, 2024", "header2"))
            print(pcol("Confirm Settings!\n", "body"))

            # Display the chosen settings
            print(f'{pcol("", "title", nostart=True)}{pcol("-------------------------------------------", "search")}')
            print("\nChosen Settings:")
            print(f'{pcol("", "title", nostart=True)}{pcol("-------------------------------------------", "search")}')
            print(f"Prompt: {args.prompt}")
            print(f"Mode: {args.mode}")
            print(f"Audio Path: {args.audio_path}")
            print(f"Audio Length: {args.audio_length}")
            print(f"Guidance Scale: {args.guidance_scale}")
            print(f'{pcol("", "title", nostart=True)}{pcol("-------------------------------------------", "search")}')
            # Ask user for confirmation
            confirm = input("Are you sure you want to go with these settings? (Y/N): ")
            if confirm.lower() != "y":
                print("Settings not confirmed. Exiting.")
                exit()

            os.system("cls" if sys.platform == "win32" else "clear" )
            print(pcol("Desota AI Audiocraft Music Text Control CLI ", "header1"), pcol("by © DeSOTA, 2024", "header2"))
            print(f'{pcol("", "title", nostart=True)}{pcol("-------------------------------------------", "search")}')
            print("\nChosen Settings:")
            print(f'{pcol("", "title", nostart=True)}{pcol("-------------------------------------------", "search")}')
            print(f"Prompt: {args.prompt}")
            print(f"Mode: {args.mode}")
            print(f"Audio Path: {args.audio_path}")
            print(f"Audio Length: {args.audio_length}")
            print(f"Guidance Scale: {args.guidance_scale}")
            print(f'{pcol("", "title", nostart=True)}{pcol("-------------------------------------------", "search")}')
            print(pcol("AI RENDER INIT!\n", "body"))
            print(f'{pcol("", "title", nostart=True)}{pcol("-------------------------------------------", "search")}')
            # Get Results

            _start_time = time.time() if DEBUG else 0
            _url_res = False
            _mode = 1
            tsearch = AudioThread(args.prompt, args)
            #tsearch.start()
            #tsearch.join(timeout=15)
            #_url_res = tsearch.res
            
            if DEBUG:
                #print(f" [ DEBUG ] - TimeOut: {tsearch.is_alive()}")
                print(f" [ DEBUG ] - elapsed time (secs): {time.time()-_start_time}")

            # Print Results
            if tsearch:
                print('done... :)')
            #    while not os.path.isfile(_url_res):
            #        print("Output video not found")
            #        time.sleep(0.1)
            #    os.rename(_url_res, args.respath)
            #    os.system("cls" if sys.platform == "win32" else "clear" )
            #    print(pcol("Desota AI Text Video Control CLI ", "header1"), pcol("by © DeSOTA, 2024", "header2"))
            #    print(f'{pcol("", "title", nostart=True)}{pcol("-------------------------------------------", "search")}')
            #    print(f"\nSaved at: {args.respath}")
                

    else:
        _url_res = False
        _mode = 1
        tsearch = AudioThread(args.prompt, args)
        #tsearch.start()
        #tsearch.join(timeout=15)
        #_url_res = tsearch.res
        
        if tsearch:
            print('done... :)')
            #while not os.path.isfile(_url_res):
            #    print("Output video not found")
            #    time.sleep(0.1)
            #os.rename(tsearch, args.respath)
            
        exit(0)
        
if __name__ == "__main__":
    args = parser.parse_args()
    main(args)