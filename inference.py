#run me under py3.8
import subprocess
import os
import requests
import urllib
import argparse
from tempfile import NamedTemporaryFile
import scipy
import torch
import torchaudio
from transformers import AutoProcessor, MusicgenForConditionalGeneration
#import ssl
#ssl._create_default_https_context = ssl._create_unverified_context
## huggingface.co now has a bad SSL certificate, your lib internally tries to verify it and fails. By adding the env variable, you basically disabled the SSL verification. But, this is actually not a good thing. Probably a work around only. All communications will be unverified in your app because of this. – Kris Apr 1, 2022 at 4:32
os.environ['CURL_CA_BUNDLE'] = ''
CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))

parser = argparse.ArgumentParser(description='text 2 audio or audio 2 audio ')
parser.add_argument('--model_mode', dest='model_mode', type=str, default="1", help="Model name, text-to-music, text-and-melody-to-music, music-to-music, music-continuation")
parser.add_argument('--audio_path', dest='audio_path', type=str, default="test.wav", help="Input audio URL, OPTIONAL")
parser.add_argument('--prompt', dest='prompt', type=str, default='', help="Text to audio prompt") #modern jazz pop with a spanish gipsy vibe
parser.add_argument('--audio_length', dest='length', type=int, default=1503, help="Generated Music Length") #modern jazz pop with a spanish gipsy vibe
parser.add_argument('--guidance_scale', dest='guidance_scale', type=int, default=3, help="Guidance scale") #modern jazz pop with a spanish gipsy vibe
parser.add_argument('--output_name', dest='output_name', type=str, default='', help="outname") #modern jazz pop with a spanish gipsy vibe
parser.add_argument('--output_path', dest='output_path', type=str, default='', help="outpath") #modern jazz pop with a spanish gipsy vibe


args = parser.parse_args()

if int(args.model_mode) == 1: #'text-to-music':
    mode = 1
if int(args.model_mode) == 2: #'text-and-melody-to-music':
    mode = 2
if int(args.model_mode) == 3: #'music-continuation':
    mode = 2
if int(args.model_mode) == 4: #'music-to-music':
    mode = 4
print(mode)   



dir_path = os.path.dirname(os.path.realpath(__file__))
folder_name = os.path.join(dir_path, "temp")
os.makedirs(folder_name, exist_ok=True)

opath = os.path.join(folder_name, f"{args.model_mode}_output.wav")
print(opath)
print(args.prompt)
def trim_sound_file(soundfile, trim_file, tmax):
    # Trim the input sound file to a maximum length of 30 seconds
    trimmed_file = trim_file # f"trimmed_{soundfile}"
    subprocess.check_call(f'ffmpeg -i {soundfile} -t {tmax} -y {trimmed_file}', shell=True)
    print(f"Trimmed sound file saved as: {trimmed_file}")
    return soundfile

def extract_sound_length(soundfile):
    # Extract the length of the sound file in seconds
    result = subprocess.check_output(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {soundfile}', shell=True)
    length = int(float(result))
    print(f"Sound file length: {length} seconds")
    return length


#mode = 2 #mode 1 = text to music ~~ mode 2 = text + music to music ~~ mode 3 = music continue

# Using small model, better results would be obtained with `medium` or `large`.



processor = AutoProcessor.from_pretrained(os.path.join(dir_path, "model"),local_files_only=True)

model = MusicgenForConditionalGeneration.from_pretrained(os.path.join(dir_path, "model"),local_files_only=True)
device = "cuda:0" if torch.cuda.is_available() else "cpu"
model.to(device)

#segment_duration = args.segment_duration
#total_duration = args.duration
#overlap = args.overlap
desc = [args.prompt]

if mode == 4:
    desc = [""]
    mode = 2

if mode == 1:
#    model.set_generation_params(
#        use_sampling=True,
#        top_k=250,
#        duration=segment_duration
#    )

    inputs = processor(
        text=desc,
        padding=True,
        return_tensors="pt",
    ).to("cuda")

    segment = model.generate(**inputs, do_sample=True, guidance_scale=args.guidance_scale, max_new_tokens=args.length)

    #segment = model.generate(descriptions=desc, progress=True)
    #total_duration -= segment_duration
if mode == 2:

    textension = os.path.splitext(args.audio_path)[1]
    tpath = os.path.join(folder_name, args.audio_path)
    
    
    temp_path = os.path.join(folder_name, f"trim{textension}")
    trim_sound_file(args.audio_path, temp_path, 30) #trim to max 30 sec
    
    tlength = extract_sound_length(temp_path)

#    model.set_generation_params(
#        use_sampling=True,
#        top_k=250,
#        duration= tlength ## TODO = DURATION OF file already put
#    )

    melody_waveform, sr = torchaudio.load(temp_path)
    melody_waveform = melody_waveform.unsqueeze(0).repeat(1, 1, 1)


    
    inputs = processor(
        audio=melody_waveform,
        sampling_rate=sr,
        text=desc,
        padding=True,
        return_tensors="pt",
    ).to("cuda")

    segment = model.generate(**inputs, do_sample=True, guidance_scale=args.guidance_scale, max_new_tokens=args.length)
    #total_duration -= tlength ## TODO = DURATION OF file already put

if mode == 3:

    textension = os.path.splitext(args.audio_url)[1]
    tpath = os.path.join(folder_name, f"temp{textension}")
    response = requests.get(args.audio_url)
    if response.status_code == 200:
        with open(tpath, 'wb') as file:
            file.write(response.content)
            print(f"out saved to {tpath}")
    
    temp_path = os.path.join(folder_name, f"trim{textension}")
    trim_sound_file(tpath, temp_path, 15) #trim to max 30 sec
    
    tlength = extract_sound_length(temp_path)

    model.set_generation_params(
        use_sampling=True,
        top_k=250,
        duration= 30 ## TODO = DURATION OF file already put
    )

    melody_waveform, sr = torchaudio.load(temp_path)
    #sr = sr[..., :int(tlength * sr)]
    #melody_waveform = melody_waveform.unsqueeze(0).repeat(1, 1, 1)

    segment = model.generate_continuation(melody_waveform,prompt_sample_rate=sr, progress=True)
    ##total_duration -= 30 ## TODO = DURATION OF file already put

sampling_rate = model.config.audio_encoder.sampling_rate



 

scipy.io.wavfile.write(os.path.join(CURRENT_PATH, args.output_path, args.output_name), rate=sampling_rate, data=segment[0, 0].cpu().numpy())


print("Quitting")
exit()

