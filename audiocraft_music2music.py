import os, sys
import time, re, json, shutil
import requests, subprocess, random
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-mr", "--model_req", 
                    help="DeSOTA Request as yaml file path",
                    type=str)
parser.add_argument("-mru", "--model_res_url",
                    help="DeSOTA API Result URL. Recognize path instead of url for desota tests", # check how is atribuited the dev_mode variable in main function
                    type=str)

DEBUG = False
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
# DeSOTA Funcs [END]
#SET FOR TRANSFORMERS ENV::
ENV_PATH = os.path.join(DESOTA_ROOT_PATH,"assets","transformers")


def main(args):
    '''
    return codes:
    0 = SUCESS
    1 = INPUT ERROR
    2 = OUTPUT ERROR
    3 = API RESPONSE ERROR
    9 = REINSTALL MODEL (critical fail)
    '''
   # Time when grabed
    _report_start_time = time.time()
    start_time = int(_report_start_time)

    #---INPUT---# TODO (PRO ARGS)
    _resnum = 5
    #---INPUT---#

    # DeSOTA Model Request
    model_request_dict = detools.get_model_req(args.model_req)
    
    # API Response URL
    send_task_url = args.model_res_url
    
    # TARGET File Path
    out_filename = f"result-{start_time}.wav"
    out_filepath = os.path.join(TMP_PATH, out_filename)
    
    out_urls = detools.get_url_from_str(send_task_url)
    if len(out_urls)==0:
        dev_mode = True
        report_path = send_task_url
    else:
        dev_mode = False
        report_path = out_urls[0]

    # Get text from request
    _req_text = detools.get_request_text(model_request_dict)
    if isinstance(_req_text, list):
        _req_text = " OR ".join(_req_text)
    if DEBUG:
        with open(os.path.join(APP_PATH, "debug.txt"), "w") as fw:
            fw.writelines([
                f"INPUT: '{_req_text}'\n",
                f"IsINPUT?: {True if _req_text else False}\n"
            ])
    
    
    # TODO Get VIDEO from request TODO
    ##TODO##
    _req_audio = detools.get_request_audio(model_request_dict) ##TODO##
    #print(model_request_dict)
    if isinstance(_req_audio, list):
        _req_audio = str(_req_audio[0])
    #REMOVE OLD INPUTS
    #try:
    #    shutil.rmtree(IN_PATH)
    #except OSError as e:
    #    print("Error: %s - %s." % (e.filename, e.strerror))
    #os.makedirs(args.IN_PATH, exist_ok=True)

    filename = os.path.basename(_req_audio)
    file_ext = os.path.splitext(filename)[1]

    # INPUT File Path    
    #in_filename = f'video-input.{file_ext}'
    #in_filepath = os.path.join(IN_PATH, in_filename)

    ##TODO##
    #with requests.get(_req_audio, stream=True) as r:
    #        with open(in_filepath, 'wb') as f:
    #            shutil.copyfileobj(r.raw, f)
    

    # Run Model
    if _req_text:
        _model_run = os.path.join(APP_PATH, "main.py")
        if USER_SYS == "win":
            _model_runner_py = os.path.join(ENV_PATH, "env", "python.exe")
        elif USER_SYS == "lin":
            _model_runner_py = os.path.join(ENV_PATH, "env", "bin", "python3")


        targs = {}
        if 'prompt' in targs:
            if targs['prompt'] == '-=#{([$argument$])}#=-':
                targs['prompt'] = _req_text
        else:
            targs['prompt'] = _req_text

        if 'audio_length' not in targs:
            targs['audio_length'] = 1503
        else:
            if int(targs['audio_length']) > 1503:
                targs['audio_length'] = 1503
            if int(targs['audio_length']) < 200:
                targs['audio_length'] = 200

        if 'guidance_scale' not in targs:
            targs['guidance_scale'] = 3
        else:
            if int(targs['guidance_scale']) > 4:
                targs['guidance_scale'] = 4
            if int(targs['guidance_scale']) < 0:
                targs['guidance_scale'] = 0

        

        targs['version'] = "v11"
        print(targs)
        le_cmd = [
            _model_runner_py, _model_run, 
            "--prompt", f'"{targs["prompt"]}"', 
            "--audio_length", str(int(tags['audio_length'])),
            "--respath", str(out_filename),
            "--audio_path", str(_req_audio),
            "--guidance_scale", str(int(targs["guidance_scale"])),
            "--mode", str(1) ,
            #"--is_long_video" if targs.is_long_video else "",
        ]

        print(" ".join(le_cmd))
        _sproc = subprocess.Popen(
            le_cmd
        )
        while True:
            # TODO: implement model timeout
            _ret_code = _sproc.poll()
            if _ret_code != None:
                break
    else:
        print(f"[ ERROR ] -> DeSotaControlAudio Request Failed: No Input found")
        exit(1)

    if not os.path.isfile(out_filepath):
        print(f"[ ERROR ] -> DeSotaControlAudio Request Failed: No Output found")
        exit(2)
    
    if dev_mode:
        if not report_path.endswith(".json"):
            report_path += ".json"
        with open(report_path, "w") as rw:
            json.dump(
                {
                    "Model Result Path": out_filepath,
                    "Processing Time": time.time() - _report_start_time
                },
                rw,
                indent=2
            )
        detools.user_chown(report_path)
        detools.user_chown(out_filepath)
        print(f"Path to report:\n\t{report_path}")
    else:
        with open(out_filepath, "r") as fr:
            deurlcruncher_res = json.loads(fr.read())
        if DEBUG:
            with open(os.path.join(APP_PATH, "debug.txt"), "a") as fw:
                fw.write(f"RESULT: {json.dumps(deurlcruncher_res)}")

        print(f"[ INFO ] -> DeSotaControlAudio Response:{json.dumps(deurlcruncher_res, indent=2)}")

        # DeSOTA API Response Preparation
        files = []
        with open(out_filepath, 'rb') as fr:
            files.append(('upload[]', fr))
            # DeSOTA API Response Post
            send_task = requests.post(url = send_task_url, files=files)
            print(f"[ INFO ] -> DeSOTA API Upload:{json.dumps(send_task.json(), indent=2)}")
        # Delete temporary file
        os.remove(out_filepath)

        if send_task.status_code != 200:
            print(f"[ ERROR ] -> DeSotaControlAudio Post Failed (Info):\nfiles: {files}\nResponse Code: {send_task.status_code}")
            exit(3)
    
    print("TASK OK!")
    exit(0)


if __name__ == "__main__":
    args = parser.parse_args()
    if not args.model_req or not args.model_res_url:
        raise EnvironmentError()
    main(args)