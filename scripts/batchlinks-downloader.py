#github.com/etherealxx
import os
import time
import gradio as gr
import urllib.request, subprocess, contextlib #these handle mega.nz
import http.client
import requests #this handle civit
import re
# from tqdm import tqdm
#from IPython.display import display, clear_output
import pathlib
import inspect
import platform
import shlex
import signal
import sys
sdless = False
try:
    from modules import script_callbacks #,scripts
    from modules.paths import script_path
    from modules.shared import cmd_opts #check for gradio queue
except ImportError: #sdless
    if platform.system() == "Windows":
        userprofile = os.environ['USERPROFILE']
        downloadpath = os.path.join(userprofile, "Downloads")
        script_path = os.path.join(downloadpath, "stable-diffusion-webui")
    elif platform.system() == "Darwin":
        userhome = os.environ['HOME']
        downloadpath = os.path.join(userhome, "Downloads")
        script_path = os.path.join(downloadpath, "stable-diffusion-webui")
    else:
        script_path = '/content/stable-diffusion-webui'
    gradio_queue = True
    import sys
    import types
    module = types.ModuleType('cmd_opts')
    module.gradio_queue = gradio_queue
    sys.modules['cmd_opts'] = module
    import cmd_opts
    sdless = True

script_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
extension_dir = os.path.abspath(os.path.join(script_dir, "../"))
#Version checking{
version_dir = os.path.join(extension_dir, "version.txt")
with open(version_dir, 'r', encoding='utf-8') as file:
    curverall = file.readlines()
currentversion = curverall[0].strip()

try:
    versionurl = "https://raw.githubusercontent.com/etherealxx/batchlinks-webui/main/version.txt"
    versionresp = requests.get(versionurl)
    version_lines = versionresp.text.splitlines()
    latestversion = version_lines[0].strip()
except requests.exceptions.RequestException:
    latestversion = '??'

if latestversion != '??':
    if currentversion == latestversion:
        latestversiontext = ""
    else:
        latestversiontext = f"[Latest version: {latestversion}]"
else:
    latestversiontext = ""

currentverforlink = latestversion.replace('.', '')
#}

try:
    global gradiostate
    if cmd_opts.gradio_queue:
        gradiostate = True
    else:
        gradiostate = False
except AttributeError:
    gradiostate = False #at this point just use onedotsix
    pass

typechecker = [
    "embedding", "embeddings", "embed", "embeds", "textualinversion", "ti",
    "model", "models", "checkpoint", "checkpoints",
    "vae", "vaes",
    "lora", "loras",
    "hypernetwork", "hypernetworks", "hypernet", "hypernets", "hynet", "hynets",
    "addnetlora", "loraaddnet", "additionalnetworks", "addnet",
    "aestheticembedding", "aestheticembed",
    "controlnet", "cnet",
    "extension", "extensions", "ext", #obsolete
    "upscaler", "upscale"
    ]

typemain = [
    "model", "vae", "embed",
    "hynet", "lora", "addnetlora",
    "aestheticembed", "cnet", "ext",
    "upscaler"
]

supportedlinks = [
    "https://mega.nz",
    "https://huggingface.co",
    "https://civitai.com/api/download/models",
    "https://civitai.com/models/",
    "https://cdn.discordapp.com/attachments",
    "https://github.com",
    "https://raw.githubusercontent.com",
    "https://files.catbox.moe",
    "https://drive.google.com",
    "https://pixeldrain.com",
    "https://www.mediafire.com/file",
    "https://anonfiles.com",
    "https://www.dropbox.com/s"
]

modelpath = os.path.join(script_path, "models/Stable-diffusion")
embedpath = os.path.join(script_path, "embeddings")
vaepath = os.path.join(script_path, "models/VAE")
lorapath = os.path.join(script_path, "models/Lora")
addnetlorapath = os.path.join(script_path, "extensions/sd-webui-additional-networks/models/lora")
hynetpath = os.path.join(script_path, "models/hypernetworks")
aestheticembedpath = os.path.join(script_path, "extensions/stable-diffusion-webui-aesthetic-gradients/aesthetic_embeddings")
cnetpath = os.path.join(script_path, "extensions/sd-webui-controlnet/models")
extpath = os.path.join(script_path, "extensions") #obsolete
upscalerpath = os.path.join(script_path, "models/ESRGAN")

if platform.system() == "Windows":
    for x in typemain: 
        # exec(f"{x}path = os.path.normpath({x}path)")
        exec(f"{x}path = {x}path.replace('/', '\\\\')")
        #exec(f"print({x}path)")

newlines = ['\n', '\r\n', '\r']
currentlink = ''
currentfolder = modelpath
finalwrite = []
currentcondition = ''
currentsuboutput = ''
processid = ''
logging = False
#currentiterfolder = ''
prockilled = False
currentfoldertrack = []
everyprocessid = []
remaininglinks = []
gdownupgraded = False
mediafireinstalled = False
# addedcustompath = []
# ariamode = False

globaldebug = True #set this to true to activate every debug features
if len(sys.argv) > 1:
    if sys.argv[1] == '--debug':
        globaldebug = True


def stopwatch(func):
    """
    A function that acts as a stopwatch for another function.

    Args:
    func (function): The function to be timed.

    Returns:
    The return value of the timed function.
    """
    def wrapper(*args, **kwargs):
        if not globaldebug:
            return func(*args, **kwargs)
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        minutes = int(elapsed_time // 60)
        seconds = elapsed_time % 60
        print(f"Time taken by {func.__name__}: {minutes:.0f}m {seconds:.2f}s")
        return result
    return wrapper

#debuggingpurpose{
    #Hello debuggers! This will track every files when the extension is launched, and
    #you can remove every downloaded files after with hashtag '#debugresetdownloads', for debugging purposes on colab
    #(Note: You need to fill the textbox with only a single line of #debugresetdownloads and nothing more)
    #There's also another feature, '#debugeverymethod', which will download a single link with all four possible methods available.
import shutil
snapshot = []
paths_to_scan = []

# take a snapshot of the directories
def take_snapshot():
    snapshotdir = os.path.join(script_path, 'snapshot.txt')
    global snapshot
    global paths_to_scan
    paths_to_scan = []
    for x in typemain:
        exec(f"paths_to_scan.append({x}path)")
    if os.path.exists(snapshotdir):
        with open(snapshotdir, 'r') as f:
            snapshot = [line.strip() for line in f.readlines()]
        print("Batchlinks extension: snapshot already exist.")
        return
    else:
        snapshot = []
        for path in paths_to_scan:
            if os.path.exists(path):
                pathtemp = os.listdir(path)
                for file in pathtemp:
                    pathoffile = os.path.join(path, file)
                    snapshot.append(pathoffile)
        with open(snapshotdir, 'w') as f:
            for item in snapshot:
                f.write(f"{item}\n")
        print("Batchlinks extension: snapshot taken.")

# rewind everything to a fresh state
def global_rewind():
    global paths_to_scan
    global path
    global currentsuboutput
    removedall, removed_files, removed_dirs, new_snapshot = [], [], [], []
    print('[1;32mDebug rewind initiated...')
    print('[0m')
    for path in paths_to_scan:
        if os.path.exists(path):
            pathtemp = os.listdir(path)
            for file in pathtemp:
                pathoffile = os.path.join(path, file)
                new_snapshot.append(pathoffile)
    toremoves = [x for x in new_snapshot if x not in snapshot]
    for fileordir in toremoves:
        if os.path.exists(fileordir):
            if os.path.isdir(fileordir):
                try:
                    shutil.rmtree(fileordir)
                    removed_dirs.append(fileordir)
                except PermissionError as e:
                    print(e)
            else:
                os.remove(fileordir)
                removed_files.append(fileordir)
    if removed_files or removed_dirs:
        print("Removed files:")
        removedall.append("Removed files:")
        for file in removed_files:
            print(file)
            removedall.append(file)
        print("Removed directories:")
        removedall.append("Removed directories:")
        for dir in removed_dirs:
            print(dir)
            removedall.append(dir)
    print('[1;32mrewind completed')
    print('[0m')
    return removedall

# Take a snapshot of the directories
if globaldebug == True:
    take_snapshot()
# }

def printdebug(toprint):
    if globaldebug == True:
        print(toprint)

def runwithsubprocess(rawcommand, folder=None, justrun=False, additionalcontext=''): #@note runwithsubprocess
    
    commandtorun = shlex.split(rawcommand) #construct_command(rawcommand)
    printdebug(f"raw command: {rawcommand}")
    printdebug(f"merged command: {commandtorun}")
    global prockilled
    global everyprocessid
    # if gradiostate == False and not rawcommand.startswith("aria"):
    #     subprocess.run(commandtorun, stderr=subprocess.STDOUT, universal_newlines=True)
    # else:
    if folder != None:
        printdebug("debug folderforsavestate: " + str(folder))
        savestate_folder(folder)
        printdebug("debug currentfoldertrack: " + str(currentfoldertrack))
    if justrun:
        process = subprocess.Popen(rawcommand, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
    else:
        process = subprocess.Popen(commandtorun, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    global processid
    processid = process.pid
    everyprocessid.append(processid)
    printdebug("debug processid: " + str(processid))

    ariacomplete = False
    global currentsuboutput
    while True:
        # Read the output from the process
        nextline = process.stdout.readline()
        if nextline == '' and process.poll() is not None:
            break
        # Check if the line contains progress information
        elif additionalcontext == 'aria2':
            if 'Download Results' in nextline:
                ariacomplete = True
                print('\n')
                print(nextline, end='')
                currentsuboutput = nextline
            else:
                if not ariacomplete:
                    match = re.search(r'\[[^\]]+\]', nextline)
                    if match:
                        stripnext = match.group().strip()
                        print("\r", end="")
                        print(f"\r{stripnext}", end='')
                        currentsuboutput = stripnext
                else:
                    print(nextline, end='')
                    currentsuboutput = nextline
        elif additionalcontext == '7z':
            sevenzmessage = [
                "Extracting", "Everything", "ERROR"
            ]
            if nextline.strip().startswith(tuple(sevenzmessage)):
                print(nextline, end=' ')
                currentsuboutput = nextline
            else:
                stripnext = nextline.strip()
                print("\r", end="")
                print(f"\r{stripnext}", end='')
                currentsuboutput = stripnext
        else:
            if justrun:
                print(nextline, end='')
            else:
                if "%" in nextline.strip() or rawcommand.startswith("curl"):
                    stripnext = nextline.strip()
                    print("\r", end="")
                    print(f"\r{stripnext}", end='')
                else:
                    print(nextline, end='')
                    if additionalcontext == 'mega':
                        process.kill()
                if additionalcontext == 'mega':
                    if nextline.strip().startswith("Download finished:"):
                        _ = subprocess.getoutput("taskkill /f /t /im MEGAcmdServer.exe")
                        printdebug("MEGA server killed")
            currentsuboutput = nextline
            

    process.wait()
    currentsuboutput = ''
    processid = ''
    if prockilled == True:
        rewind_folder(folder)
        print('[1;31mOperation Cancelled')
        print('[0m')
        global currentcondition
        currentcondition = 'Operation Cancelled'
        return

#these code below handle mega.nz
def unbuffered(proc, stream='stdout'):
    stream = getattr(proc, stream)
    with contextlib.closing(stream):
        while prockilled == False:
            out = []
            last = stream.read(1)
            # Don't loop forever
            if last == '' and proc.poll() is not None:
                break
            while last not in newlines:
                # Don't loop forever
                if last == '' and proc.poll() is not None:
                    break
                out.append(last)
                last = stream.read(1)
            out = ''.join(out)
            yield out

def transfare(todownload, folder, torename=''):
    #import codecs
    #decoder = codecs.getincrementaldecoder("UTF-8")()
    todownload_s = shlex.quote(todownload)
    folder_s = shlex.quote(folder)
    if platform.system() == "Windows":
        savestate_folder(folder)
        localappdata = os.environ['LOCALAPPDATA']
        megagetloc = os.path.join(localappdata, "MEGAcmd", "mega-get.bat")
        runwithsubprocess(f"{shlex.quote(megagetloc)} {todownload_s} {folder_s}", folder, False, 'mega')
    else:
        savestate_folder(folder_s)
        cmd = ["mega-get", todownload_s, folder_s]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
        global processid
        global everyprocessid
        processid = proc.pid
        everyprocessid.append(processid)

        global currentsuboutput
        for line in unbuffered(proc):
            if prockilled == False:
                if not line.startswith("Download"):
                    currentsuboutput = line
                    print(f"\r{line}", end="")
                else:
                    print(f"\n{line}")
            else:
                currentsuboutput = ''
                print('[1;31mOperation Cancelled')
                print('[0m')
                global currentcondition
                currentcondition = 'Operation Cancelled'
                return
        currentsuboutput = ''
    if torename:
        listfilenew = os.listdir(folder)
        newerfoldertrack = []
        for file in listfilenew:
            pathoffile = os.path.join(folder, file)
            newerfoldertrack.append(pathoffile)
        checkrename = [x for x in newerfoldertrack if x not in currentfoldertrack]
        if checkrename:
            # renamedfile = os.path.basename(checkrename[0])
            # pathtorename = os.path.join(folder, renamedfile)
            os.rename(checkrename[0], os.path.join(folder, torename))
    

def installmega():
    HOME = os.path.expanduser("~")
    ocr_file = pathlib.Path(f"{HOME}/.ipython/ocr.py")
    if not ocr_file.exists():
        hCode = "https://raw.githubusercontent.com/biplobsd/" \
                    "OneClickRun/master/res/ocr.py"
        urllib.request.urlretrieve(hCode, str(ocr_file))

    from importlib.util import module_from_spec, spec_from_file_location
    ocr_spec = spec_from_file_location("ocr", str(ocr_file))
    ocr = module_from_spec(ocr_spec)
    ocr_spec.loader.exec_module(ocr)

    if not os.path.exists("/usr/bin/mega-cmd"):
        #ocr.loadingAn()
        print('[1;32mInstalling MEGA ...')
        print('[0m')
        ocr.runSh('sudo apt-get -y update')
        ocr.runSh('sudo apt-get -y install libmms0 libc-ares2 libc6 libcrypto++6 libgcc1 libmediainfo0v5 libpcre3 libpcrecpp0v5 libssl1.1 libstdc++6 libzen0v5 zlib1g apt-transport-https')
        ocr.runSh('sudo curl -sL -o /var/cache/apt/archives/MEGAcmd.deb https://mega.nz/linux/MEGAsync/Debian_9.0/amd64/megacmd-Debian_9.0_amd64.deb', output=True)
        ocr.runSh('sudo dpkg -i /var/cache/apt/archives/MEGAcmd.deb', output=True)
        print('[1;32mMEGA is installed.')
        print('[0m')

def installmegawin():
    userprofile = os.environ['USERPROFILE']
    localappdata = os.environ['LOCALAPPDATA']
    megagetloc = os.path.join(localappdata, "MEGAcmd", "mega-get.bat")
    megacmdloc = os.path.join(userprofile, "Downloads", "MEGAcmdSetup64.exe")
    if not os.path.exists(megagetloc):
        print('[1;32mInstalling MEGA ...')
        print('[0m')
        runwithsubprocess(f"curl -o {shlex.quote(megacmdloc)} https://mega.nz/MEGAcmdSetup64.exe")
        time.sleep(1)
        runwithsubprocess(f"{shlex.quote(megacmdloc)} /S")
        time.sleep(4)
        print('[1;32mMEGA is installed.')
        print('[0m')
        #clear_output()
#these code above handle mega.nz

def getcivitname(link): #@note getcivitname
    searcher = "findstr" if platform.system() == "Windows" else "grep"
    try:
        contentdis = [line for line in subprocess.getoutput(f"curl -sI {link} | {searcher} -i content-disposition").splitlines() if line.startswith('location')][0]
    except IndexError:
        return ''
    cuttedcontent = contentdis.find('response-content-disposition=attachment%3B%20filename%3D%22') + 59
    filename = str(contentdis[cuttedcontent:]).replace('%22&x-id=GetObject', '')
    
    filename = civitmodeltypename(filename, link)
    return filename

def getcivitname2(link):
    searcher = "findstr" if platform.system() == "Windows" else "grep"
    try:
        contentdis = [line for line in subprocess.getoutput(f"curl -sI {link} | {searcher} -i content-disposition").splitlines() if line.startswith('location')][0]
        cuttedcontent = contentdis.find('response-content-disposition=attachment%3B%20filename%3D%22') + 59
        filename = str(contentdis[cuttedcontent:]).replace('%22&x-id=GetObject', '')
        if filename:
            return [0, link, filename]
    except:
        return []

def civitmodeltypename(name, filelink):
    nameonly, extension = os.path.splitext(name)
    if 'type=Pruned' in filelink:
        nameonly += "_pruned"
    
    if 'format=Safetensor' in filelink:
        extension = '.safetensors'
    elif 'format=PickleTensor' in filelink:
        extension = '.ckpt'
    
    nameoffile = nameonly + extension
    return nameoffile

def checkcivitconfig(link): #check if the current civit link has a config file (v2.0+) @note checkcivitconfig
    def getrequest(link2):
        response = requests.get(link2)
        return response.status_code

    params = ['?type=Config','?type=Config&format=Other']

    for param in params:
        response = getrequest(link + param)
        if response == 200:
            #print('The link exists')
            return link + param
    return ''

def civitmodeltypechooser(modeljson, prunedmodel, torchortensor, linkandnames):

  prunedorfull = ['?type=Model', '?type=Pruned%20Model']
  if prunedmodel == True:
    prunedorfull.reverse()
  pickleorsafe = ['&format=SafeTensor', '&format=PickleTensor']
  if torchortensor=='ckpt':
    pickleorsafe.reverse()

  defaultlinkurl = [link.get('downloadUrl') for link in modeljson['modelVersions'][0]['files'] if not '?type=' in link.get('downloadUrl')][0]

  indexlinkname = list()
  checklater = ''
  for index, (link, name) in enumerate(linkandnames.items()):
    if prunedorfull[0] in link:
        if pickleorsafe[0] in link:
            indexlinkname.extend([index, link, name])
            break
        else:
            checklater = link
            continue
    else: 
        continue

  if checklater and not indexlinkname:
    for index, (link, name) in enumerate(linkandnames.items()):
        if checklater == link:
            indexlinkname.extend([index, link, name])
            checklater = ''
            break
          
  if not indexlinkname:
    indexlinkname = getcivitname2(defaultlinkurl+prunedorfull[0]+pickleorsafe[0])

  if not indexlinkname:
    for index, (link, name) in enumerate(linkandnames.items()):
        if defaultlinkurl == link:
            indexlinkname.extend([index, link, name])
            break

  return indexlinkname

#thank you @rti7743 for this part {
def civitdown2_get_json(url):
  import re
  m = re.search(r'https://civitai.com/models/(\d+)', url)
  model_id = m.group(1)

  api_url = "https://civitai.com/api/v1/models/" + model_id

  import requests
  txt = requests.get(api_url).text

  import json
  try:
    return json.loads(txt)
  except json.decoder.JSONDecodeError:
    return 'error'

def civitdown2_get_save_directory(model_type, default_folder):
  if model_type == "Checkpoint":
    return modelpath
  elif model_type == "Hypernetwork":
    return hynetpath
  elif model_type == "TextualInversion":
    return embedpath
  elif model_type == "AestheticGradient":
    return aestheticembedpath
  elif model_type == "VAE":
    return vaepath
  elif model_type == "LORA":
    return lorapath
  else:
    return default_folder

def civitdown2_convertimage(imagejpg_save_path, imagepng_save_path):
  from PIL import Image
  img = Image.open(imagejpg_save_path)
  img_resized = img.resize((img.width // 2, img.height // 2))
  img_resized.save(imagepng_save_path)
  os.remove(imagejpg_save_path)

def civitdown2(url, folder, downloader, isdebugevery, modeldefaulttype, isprunedmodel, isdownvae): #@note civitdown2
  def civitlinkandnamer(model):
    linkandname = dict()
    for i, link in enumerate(model['modelVersions'][0]['files']):
        name = link.get('name')
        url = link.get('downloadUrl')
        if name and url:
            linkandname[url] = name
            # print(i, url, name)
        else:
          pass
    return linkandname

  model = civitdown2_get_json(url)
  if model == 'error':
    print('[1;31mFailed retrieving the model data.')
    print('[1;31mCivitAI website might going down currently.')
    print('[0m')
    return
  
  if model == {'error': 'Model not found'}:
    print('[1;31mModel ' + url + ' is not available anymore')
    print('[0m')
    return
  
  save_directory = civitdown2_get_save_directory(model['type'], folder)
  try:
    parameter = url.split("?")[-1] + "?"
  except:
    parameter = ''

  civitlinkandnames = linkandnamer(model)

  if model['type'] == "Checkpoint":
    data_index, data_url, data_filename = civitmodeltypechooser(model, False, 'safetensors', civitlinkandnames) #@note
    data_filename = civitmodeltypename(data_filename, parameter)
    image_filename = model['modelVersions'][0]['files'][0]['name']
  else:
    data_url = model['modelVersions'][0]['files'][0]['downloadUrl']
    data_filename = model['modelVersions'][0]['files'][0]['name']
    image_filename = data_filename

  image_url = model['modelVersions'][0]['images'][0]['url']
  printdebug("data_url: " + data_url)
  printdebug("data_filename: " + data_filename)
  printdebug("image_url: " + data_filename)
  if model['type'] == "TextualInversion":
      image_filename_jpg = pathlib.PurePath(image_filename).stem + ".preview.jpg"
      image_filename_png = pathlib.PurePath(image_filename).stem + ".preview.png"
  else:
      image_filename_jpg = pathlib.PurePath(image_filename).stem + ".jpg"
      image_filename_png = pathlib.PurePath(image_filename).stem + ".png"

  data_save_path = os.path.join(save_directory, data_filename)
  imagejpg_save_path = os.path.join(save_directory, image_filename_jpg)
  imagepng_save_path = os.path.join(save_directory, image_filename_png)

  currentmode = 'civit'
  if isdebugevery:
      currentmode = 'civitdebugevery'

  printdebug(f"debug download_url({data_url}, {data_save_path}, {downloader})")
  if prockilled == False:
    hfdown(data_url, data_save_path, downloader, currentmode)
    printdebug("normal download done, now check for the config")
    config_url = checkcivitconfig(data_url)
    vae_url, vae_name = '',''
    for link, name in civitlinkandnames:
        if '?type=VAE' in link:
            vae_url, vae_name = link, name
            break
  if model['type'] == "Checkpoint":
    if prockilled == False and isdownvae and vae_url:
          namefile = os.path.splitext(data_filename)[0]
          vae_name = namefile + '.vae.pt'
          data_save_path = os.path.join(os.path.dirname(data_save_path), vae_name)
          hfdown(vae_url, data_save_path, downloader, currentmode)
    if prockilled == False and config_url:
          namefile = os.path.splitext(data_filename)[0]
          config_name = namefile + '.yaml'
          data_save_path = os.path.join(os.path.dirname(data_save_path), config_name)
          hfdown(config_url, data_save_path, downloader, currentmode)

  hfdown(image_url, imagejpg_save_path, downloader, currentmode)
  civitdown2_convertimage(imagejpg_save_path, imagepng_save_path)
  print(f"{data_save_path} successfully downloaded.")


  if isdebugevery:
    additionalname = '-' + downloader

    if model['type'] == "TextualInversion":
      image_filename_jpg = pathlib.PurePath(data_filename).stem + additionalname + ".preview.jpg"
      image_filename_png = pathlib.PurePath(data_filename).stem + additionalname + ".preview.png"
    else:
      image_filename_jpg = pathlib.PurePath(data_filename).stem + additionalname + ".jpg"
      image_filename_png = pathlib.PurePath(data_filename).stem + additionalname + ".png"
    
    imagejpg_save_path = os.path.join(save_directory, image_filename_jpg)
    imagepng_save_path = os.path.join(save_directory, image_filename_png)
    
#}
def mediadrivedown(todownload, folder, mode, torename=''): #@note mediadrivedown
    todownload_s = shlex.quote(todownload)
    if platform.system() == "Windows":
        folder_s = folder
    else:
        folder_s = shlex.quote(folder)
    prevcurdir = os.getcwd()
    os.chdir(folder)
    savestate_folder(folder_s)

    if mode=='gdrive':
        runwithsubprocess(f"gdown --fuzzy {todownload_s}", folder_s)
    elif mode=='mediafire':
        runwithsubprocess(f"mediafire-dl {todownload_s}", folder_s)

    os.chdir(prevcurdir)
    if torename:
        listfilenew = os.listdir(folder)
        newerfoldertrack = []
        for file in listfilenew:
            pathoffile = os.path.join(folder, file)
            newerfoldertrack.append(pathoffile)
        checkrename = [x for x in newerfoldertrack if x not in currentfoldertrack]
        if checkrename:
            os.rename(checkrename[0], os.path.join(folder, torename))

def hfdown(todownload, folder, downloader, mode='default', torename=''): #@note hfdown
    global currentcondition
    # global ariamode
    if mode=='civit' or mode=='civitdebugevery':
        filename = pathlib.Path(folder).name
        filename_s = shlex.quote(filename)
        filepath = folder
        filepath_s = shlex.quote(folder)
        todownload_s = todownload
        folder_s = pathlib.Path(folder).parent.resolve()
    else:
        if mode=='pixeldrain' or mode=='dropbox':
            filename = torename
        else:
            filename = todownload.rsplit('/', 1)[-1]
        filename_s = shlex.quote(filename)
        filepath = os.path.join(folder, filename)
        filepath_s = shlex.quote(filepath)
        todownload_s = shlex.quote(todownload)
        folder_s = shlex.quote(folder)
    #savestate_folder(folder_s)
    if platform.system() == "Windows": #@note windows downloader
        localappdata = os.environ['LOCALAPPDATA']
        batchlinksinstallpath = os.path.join(localappdata, "batchlinks")
        wgetpath = os.path.join(batchlinksinstallpath, "wget-gnutls-x64.exe")

        ariazippath = os.path.join(batchlinksinstallpath, "aria2-1.36.0-win-64bit-build2.7z")
        ariapath = os.path.join(batchlinksinstallpath, "aria2-1.36.0-win-64bit-build2", "aria2c.exe")
        os.makedirs(batchlinksinstallpath, exist_ok=True)
        if downloader=='gdown':
            global gdownupgraded
            if gdownupgraded == False:
                tempcondition = currentcondition
                currentcondition = "Upgrading gdown..."
                print('[1;32mUpgrading gdown ...')
                print('[0m')
                runwithsubprocess(f"pip install -q --upgrade --no-cache-dir gdown")
                print('[1;32mgdown upgraded!')
                print('[0m')
                currentcondition = tempcondition
                gdownupgraded = True
            try:
                runwithsubprocess(f"gdown {todownload_s} -O {filepath_s}", folder)
            except FileNotFoundError:
                import gdown
                gdown.download(todownload, filepath, quiet=False)
        elif downloader=='wget':
            #os.system("python -m wget -o " + os.path.join(folder, filename) + " " + todownload)
            # import wget
            # wget.download(todownload, filepath)
            checkwget = subprocess.getoutput(wgetpath)
            if "is not recognized" in checkwget:
                tempcondition = currentcondition
                currentcondition = "Installing wget Windows..."
                print('[1;32mInstalling wget Windows...')
                print('[0m')
                wgetwinlink = "https://github.com/webfolderio/wget-windows/releases/download/v1.21.3.june.19.2022/wget-gnutls-x64.exe"
                print(wgetwinlink)
                runwithsubprocess("curl -Lo " + shlex.quote(wgetpath) + " " + wgetwinlink, batchlinksinstallpath)
                print('[1;32mwget Windows installed!')
                print('[0m')
                currentcondition = tempcondition
            runwithsubprocess(f"{shlex.quote(wgetpath)} -O {filepath_s} {todownload_s} --progress=bar:force", folder)
        elif downloader=='curl':
            runwithsubprocess(f"curl -Lo {filepath_s} {todownload_s}", folder)
        elif downloader=='aria2':
            checkaria = subprocess.getoutput(ariapath)
            if "is not recognized" in checkaria or "cannot find the path" in checkaria:
                tempcondition = currentcondition
                currentcondition = "Installing aria2 Windows..."
                print('[1;32mInstalling aria2 Windows...')
                print('[0m')
                ariaziplink = "https://github.com/q3aql/aria2-static-builds/releases/download/v1.36.0/aria2-1.36.0-win-64bit-build2.7z"
                print(ariaziplink)
                runwithsubprocess("curl -Lo " + shlex.quote(ariazippath) + " " + ariaziplink, batchlinksinstallpath)
                sevenzpath = install7zWin()
                runwithsubprocess(f"{shlex.quote(sevenzpath)} x {shlex.quote(ariazippath)} -o{shlex.quote(batchlinksinstallpath)}", batchlinksinstallpath, False, '7z')
                print('[1;32maria2 Windows installed!')
                print('[0m')
                currentcondition = tempcondition
            # ariamode = True
            runwithsubprocess(f"{shlex.quote(ariapath)} --summary-interval=1 --console-log-level=error --check-certificate=false -c -x 16 -s 16 -k 1M {todownload_s} -d {folder_s} -o {filename_s}", folder, False, 'aria2')
    else:
        if downloader=='gdown':
            printdebug(f"debug gdown {todownload_s} -O {filepath_s}")
            runwithsubprocess(f"gdown {todownload_s} -O {filepath_s}", folder_s)
        elif downloader=='wget':
            runwithsubprocess(f"wget -O {filepath_s} {todownload_s} --progress=bar:force", folder_s)
        elif downloader=='curl':
            runwithsubprocess(f"curl -Lo {filepath_s} {todownload_s}", folder_s)
            # curdir = os.getcwd()
            # os.rename(os.path.join(curdir, filename), filepath)
        elif downloader=='aria2':
            ariachecker = "dpkg-query -W -f='${Status}' aria2"
            checkaria = subprocess.getoutput(ariachecker)
            if "no packages found matching aria2" in checkaria:
                tempcondition = currentcondition
                currentcondition = "Installing aria2..."
                print('[1;32mInstalling aria2 ...')
                print('[0m')
                runwithsubprocess(f"apt -y update -qq")
                runwithsubprocess(f"apt -y install -qq aria2")
                print('[1;32maria2 installed!')
                print('[0m')
                currentcondition = tempcondition
            # ariamode = True
            runwithsubprocess(f"aria2c --summary-interval=1 --console-log-level=error -c -x 16 -s 16 -k 1M {todownload_s} -d {folder_s} -o {filename_s}", folder_s, False, 'aria2')
        printdebug("\nmode: " + mode)
        if mode=='debugevery':
            time.sleep(2)
            try:
                os.rename(filepath, os.path.join(folder, f"{os.path.splitext(filename)[0]}-{downloader}{os.path.splitext(filename)[1]}"))
                printdebug("renamed to " + f"{os.path.splitext(filename)[0]}-{downloader}{os.path.splitext(filename)[1]}")
            except FileNotFoundError or FileExistsError:
                printdebug("rename failed somehow")
                pass
        elif mode=='civitdebugevery':
            time.sleep(2)
            printdebug("debug filename: " + str(filename))
            printdebug("debug filename_s: " + str(filename_s))
            printdebug("debug filepath: " + str(filepath_s))
            printdebug("debug todownload_s: " + str(todownload_s))
            printdebug("debug folder_s: " + str(folder_s))
            try:
                os.rename(folder, os.path.join(folder_s, f"{os.path.splitext(filename)[0]}-{downloader}{os.path.splitext(filename)[1]}"))
                printdebug("renamed to " + f"{os.path.splitext(filename)[0]}-{downloader}{os.path.splitext(filename)[1]}")
            except FileNotFoundError or FileExistsError:
                printdebug("rename failed somehow")
                pass
    if torename and prockilled == False and filename != torename:
        def saferename(oldpath, newpath):
            try:
                os.rename(oldpath, newpath)
            except:
                print("Rename failed.")
                pass

        if mode=='civit':
            saferename(folder, os.path.join(folder_s, shlex.quote(torename)))
        else:
            saferename(filepath, os.path.join(folder, shlex.quote(torename)))
    if mode=='dropbox':
        if os.path.getsize(filepath) <= 1024:
            print('[1;31mDropbox filesize below 1kb')
            print("There's a chance that the file got too much traffic and dropbox blocked access to it")
            print('[0m')
    # if prockilled == True:
    #     #rewind_folder(folder_s)
    #     pass

def install7zWin(): #@note install7z
    #usage: sevenzpath = install7zWin()
    localappdata = os.environ['LOCALAPPDATA']
    batchlinksinstallpath = os.path.join(localappdata, "batchlinks")
    sevenzpath = os.path.join(batchlinksinstallpath, "7zr.exe")
    sevenzlink = "https://www.7-zip.org/a/7zr.exe"
    print(sevenzlink)
    if not os.path.exists(sevenzpath):
        runwithsubprocess("curl -Lo " + shlex.quote(sevenzpath) + " " + sevenzlink, batchlinksinstallpath)
    return sevenzpath

def savestate_folder(folder):
    global currentfoldertrack
    currentfoldertrack = []
    listfile = os.listdir(folder)
    for file in listfile:
        pathoffile = os.path.join(folder, file)
        currentfoldertrack.append(pathoffile)

def rewind_folder(folder):
    listfilenew = os.listdir(folder)
    newerfoldertrack = []
    for file in listfilenew:
        pathoffile = os.path.join(folder, file)
        newerfoldertrack.append(pathoffile)
    toremove = [x for x in newerfoldertrack if x not in currentfoldertrack]
    printdebug("\ndebug toremove: " + str(toremove))
    print()
    for fileordir in toremove:
        if os.path.exists(fileordir):
            if os.path.isdir(fileordir):
                shutil.rmtree(fileordir)
                print("Removed incomplete download: " + fileordir)
            else:
                os.remove(fileordir)
            print("Removed incomplete download: " + fileordir)

def writeall(olddict, shellonly, custompaths=''):
    newdict = trackall()
    global finalwrite
    finalwrite = []

    finalwrite.append("All done!")
    if custompaths:
        finalwrite.append("⬇️Custom path added:⬇️")
        for hashtag, thepath in custompaths.items():
            finalwrite.append(f"{hashtag} -> {thepath}")
    finalwrite.append("Downloaded files: ")
    for oldtype, olddir in olddict.items():
        for newtype, newdir in newdict.items():
            if newtype == oldtype:
                s = set(olddir)
                trackcompare = [x for x in newdir if x not in s]
                if len(trackcompare) > 0:
                    exec(f"finalwrite.append('⬇️' + {newtype}path + '⬇️')")
                    for item in trackcompare:
                        finalwrite.append(item)
    if bool(remaininglinks):
        finalwrite.append("(There are still some files that have not been downloaded. Click the 'Resume Download' button to load the links that haven't been downloaded.)")
    finaloutput = list_to_text(finalwrite)
    finalwrite = []
    if shellonly:
        return "Commands executed successfully."
    else:
        return finaloutput

def writepart(box, path):
    global finalwrite
    if len(box) > 0:
        finalwrite.append("⬇️" + path + "⬇️")
        for item in box:
            finalwrite.append(item)

def trackall():
    filesdict = dict()
    for x in typemain:
        exec(f"os.makedirs({x}path, exist_ok=True)")
        exec(f"filesdict['{x}'] = os.listdir({x}path)")
    return filesdict

def currentfoldertohashtag(folder):
    for x in typemain:
        checkpath = str()
        checkpath = eval(x+'path')
        printdebug("checkpath: " + checkpath)
        if str(folder).strip() == checkpath:
            thehashtag = "#" + x
            printdebug("thehashtag: " + thehashtag)
            return thehashtag
    return "#debug"

def splitrename(linkcurrent):
    renamecurrent = ''
    if ">" in linkcurrent:
        file_rename = linkcurrent.split(">")
        file_rename = [file_rename.strip() for file_rename in file_rename]
        linkcurrent = file_rename[0]
        if file_rename[1]:
            renamecurrent = file_rename[1]
    return linkcurrent, renamecurrent

def extractcurdir(currentdir): #@note extractcurdir
    allfileshere = os.listdir(currentdir)
    szfileall = []
    sevenzpath = install7zWin()
    global currentcondition
    for filehere in allfileshere:
        if filehere.endswith('.7z'):
            szpath = os.path.join(currentdir, filehere)
            szfileall.append(szpath)
    for szfile in szfileall:
        if prockilled == False:
            # currentcondition = "Extracting" + os.path.basename(szfile) + "..."
            if platform.system() == "Windows":
                runwithsubprocess(f"{shlex.quote(sevenzpath)} x {shlex.quote(szfile)} -p- -o{shlex.quote(currentdir)} -y -sdel -bb0", currentdir, False, '7z')
            else:
                runwithsubprocess(f"7z x {shlex.quote(szfile)} -p- -o{shlex.quote(currentdir)} -y -sdel -bb0", currentdir, False, '7z')

#@stopwatch #the decorator mess with the progress bar
def run(command, choosedowner, civitdefault, civitpruned, civitvae, progress=gr.Progress()): #@note run
    progress(0.01, desc='')
    global prockilled
    prockilled = False
    global everyprocessid
    everyprocessid = []
    everymethod = False
    global currentcondition
    resumebuttonvisible = False
    if command.strip() == '#debugresetdownloads' and snapshot != {} and globaldebug == True:
        currentcondition = f'Removing downloaded files...'
        removed_files = global_rewind()
        texttowrite = ["⬇️Removed files⬇️"]
        for item in removed_files:
            texttowrite.append(item)
        writefinal = list_to_text(texttowrite)
        currentcondition = f'Removing done.'
        if gradiostate == True:
            return [writefinal, gr.Dataframe.update(value=buildarrayofhashtags('right')), gr.Dataframe.update(value=buildarrayofhashtags('bottom'))]
        else:
            return [writefinal, gr.Dataframe.update(value=buildarrayofhashtags('right')), gr.Dataframe.update(value=buildarrayofhashtags('bottom')), gr.Button.update(visible=resumebuttonvisible)]
    
    oldfilesdict = trackall()
    currentfolder = modelpath
    os.makedirs(currentfolder, exist_ok=True)
    currentcondition = 'Extracting links...'
    links = extract_links(command)
    isshell = True
    for listpart in links:
        if not listpart.startswith('!'):
            isshell = False
            break
    printdebug("links: " + str(links))
    steps = float(0)
    totalsteps = float(1)

    usemega = False
    usegdrive = False
    usemediafire = False
    # global ariamode
    global gdownupgraded
    global mediafireinstalled
    for item in links:
        if not item.startswith('#'):
            totalsteps += 1
        if item.startswith('https://mega.nz'):
            usemega = True
        if item.startswith('https://drive.google.com'):
            usegdrive = True
        if item.startswith('https://www.mediafire.com/file'):
            usemediafire = True

            #break
    printdebug("totalsteps: " + str(totalsteps))
    if usemega == True:
        currentcondition = 'Installing Mega...'
        progress(0.01, desc='Installing Mega...')
        if platform.system() == "Windows":
            installmegawin()
        else:
            installmega()
    if usegdrive == True and gdownupgraded == False:
        tempcondition = currentcondition
        currentcondition = "Upgrading gdown..."
        print('[1;32mUpgrading gdown ...')
        print('[0m')
        runwithsubprocess(f"pip install -q --upgrade --no-cache-dir gdown")
        print('[1;32mgdown upgraded!')
        print('[0m')
        currentcondition = tempcondition
        gdownupgraded = True
    if usemediafire == True and mediafireinstalled == False:
        tempcondition = currentcondition
        currentcondition = "Installing mediafire-dl..."
        print('[1;32mInstalling mediafire-dl...')
        print('[0m')
        runwithsubprocess(f"pip3 install git+https://github.com/Juvenal-Yescas/mediafire-dl")
        print('[1;32mmediafire-dl installed!')
        print('[0m')
        currentcondition = tempcondition
        mediafireinstalled = True

    print('[1;32mBatchLinks Downloads starting...')
    print('[0m')
    printdebug('prockilled: ' + str(prockilled))
    global remaininglinks
    batchtime = time.time()
    addedcustompath = dict()
    downmethod = ['gdown', 'wget', 'curl', 'aria2']
    hfmethods = [
        "https://raw.githubusercontent.com",
        "https://huggingface.co",
        "https://cdn.discordapp.com/attachments"
    ]
    for listpart in links:
        if prockilled == False:
            currenttorename = ''
            printdebug("steps: " + str(steps))
            printdebug("total steps: " + str(totalsteps))
            printdebug("percentage: " + str(round(steps/totalsteps, 1)))
            # ariamode = False
            if gradiostate == False:
                if time.time() - batchtime >= 70:
                    remaininglinks = links[links.index(listpart):]
                    printdebug("remaining links: " + str(remaininglinks))
                    if bool(remaininglinks):
                        printdebug("currentfolder: " + currentfolder)
                        tophashtag = currentfoldertohashtag(currentfolder)
                        printdebug("tophashtag: " + tophashtag)
                        remaininglinks.insert(0, tophashtag)
                        printdebug("remaining links new: " + str(remaininglinks))
                        print()
                        print('[1;33mRuntime was stopped to prevent hangs.')
                        print("[1;33mCheck the UI and press 'Resume Download' to load the remaining links")
                        print("[1;33mThen click 'Download All!' again")
                        print('[0m')
                        print("These are some links that haven't been downloaded yet.👇")
                        printremains = list_to_text(remaininglinks)
                        print(printremains)
                        resumebuttonvisible = True
                    cancelrun()
                    break

            if listpart.startswith("https://mega.nz"):
                currentlink, currenttorename = splitrename(listpart)
                print('\n')
                print(currentlink)
                currentcondition = f'Downloading {currentlink}...'
                progress(round(steps/totalsteps, 3), desc='Downloading from ' + os.path.basename(currentlink).split('#')[0] + '...')
                transfare(currentlink, currentfolder, currenttorename)
                steps += 1

            elif listpart.startswith(tuple(hfmethods)):
            # elif listpart.startswith("https://huggingface.co") or listpart.startswith("https://raw.githubusercontent.com") or listpart.startswith("https://cdn.discordapp.com/attachments"):
                currentlink, currenttorename = splitrename(listpart)
                print('\n')
                print(currentlink)
                currentcondition = f'Downloading {currentlink}...'
                progress(round(steps/totalsteps, 3), desc='Downloading ' + os.path.basename(currentlink) + '...')
                if everymethod == False:
                    hfdown(currentlink, currentfolder, choosedowner, 'default', currenttorename)
                else:
                    for xmethod in downmethod:
                        if prockilled == False:
                            hfdown(currentlink, currentfolder, xmethod, 'debugevery')
                steps += 1

            elif listpart.startswith("https://www.dropbox.com/s"): #@note dropbox
                currentlink, currenttorename = splitrename(listpart)
                if currentlink.endswith("?dl=0"):
                    currentlink = currentlink.split("?dl=")[0] + "?dl=1"
                realname = currentlink.split("/")[-1].split("?dl=")[0]
                if currenttorename == '':
                    currenttorename = realname
                print('\n')
                print(currentlink)
                currentcondition = f'Downloading {currentlink}...'
                progress(round(steps/totalsteps, 3), desc='Downloading ' + currenttorename + '...')
                hfdown(currentlink, currentfolder, choosedowner, 'dropbox', currenttorename)
                steps += 1

            elif listpart.startswith("https://drive.google.com"):
                currentlink, currenttorename = splitrename(listpart)
                print('\n')
                print(currentlink)
                currentcondition = f'Downloading {currentlink}...'
                match = re.search(r'\?id=([^\&]+)\&export|/d/([^\s/]+)/', currentlink)
                if match:
                    if match.group(1):
                        extracted_string = match.group(1)
                    else:
                        extracted_string = match.group(2)
                progress(round(steps/totalsteps, 3), desc='Downloading from ' + extracted_string + '...')
                mediadrivedown(currentlink, currentfolder, 'gdrive', currenttorename)
                steps += 1
                
            elif listpart.startswith("https://pixeldrain.com"): #@note pixeldrain
                currentlink, currenttorename = splitrename(listpart)
                if not currentlink.startswith("https://pixeldrain.com/api/file/"):
                    fileid = currentlink.split("/")[-1]
                    currentlink = f"https://pixeldrain.com/api/file/{fileid}"
                currentcondition = f'Retrieving Pixeldrain link...'
                searcher = "findstr" if platform.system() == "Windows" else "grep"
                try:
                    filename = subprocess.getoutput(f"curl -sI {currentlink} | {searcher} -i Content-Disposition").split('filename="', 1)[1].rsplit('"', 1)[0]
                except IndexError:
                    print("Something wrong while retrieving the Pixeldrain link")
                    continue
                if currenttorename == '':
                    currenttorename = filename
                print('\n')
                print(currentlink)
                currentcondition = f'Downloading {currentlink}...'
                progress(round(steps/totalsteps, 3), desc='Downloading ' + currenttorename + '...')
                # if everymethod == False:
                hfdown(currentlink, currentfolder, choosedowner, 'pixeldrain', currenttorename)
                # else:
                #     for xmethod in downmethod:
                #         if prockilled == False:
                #             hfdown(currentlink, currentfolder, xmethod, 'debugevery')
                steps += 1

            elif listpart.startswith("https://www.mediafire.com/file"): #@note mediafire
                currentlink, currenttorename = splitrename(listpart)
                print('\n')
                print(currentlink)
                currentcondition = f'Downloading {currentlink}...'
                progress(round(steps/totalsteps, 3), desc='Downloading ' + currentlink.split("/")[-2] + '...')
                # if everymethod == False:
                mediadrivedown(currentlink, currentfolder, 'mediafire', currenttorename)
                # else:
                #     for xmethod in downmethod:
                #         if prockilled == False:
                #             hfdown(currentlink, currentfolder, xmethod, 'debugevery')
                steps += 1

            elif listpart.startswith("https://anonfiles.com"): #@note anonfiles
                currentlink, currenttorename = splitrename(listpart)
                print('\n')
                print(currentlink)

                currentcondition = f'Retrieving anonfiles link...'
                # print(filename)
                # Send HTTP request to the website and read the response
                response = urllib.request.urlopen(currentlink)
                html_content = response.read().decode('utf-8')

                # Find all links that contain "anonfiles" in them using regular expressions
                download_links = re.findall(r'href=["\'](https?:\/\/.*?anonfiles.*?)["\']', html_content)
                currentlink = max(download_links, key=len)

                currentcondition = f'Downloading {currentlink}...'
                progress(round(steps/totalsteps, 3), desc='Downloading ' + currentlink.split("/")[-1] + '...')
                if everymethod == False:
                    hfdown(currentlink, currentfolder, choosedowner, 'default', currenttorename)
                else:
                    for xmethod in downmethod:
                        if prockilled == False:
                            hfdown(currentlink, currentfolder, xmethod, 'debugevery')
                steps += 1

            elif listpart.startswith("https://files.catbox.moe"):
                currentlink, currenttorename = splitrename(listpart)
                print('\n')
                print(currentlink)
                try:
                    urllib.request.urlopen(currentlink)
                except http.client.RemoteDisconnected:
                    print('[1;31mConnection to ' + currentlink + ' failed.')
                    print("This colab session's server might doesn't have access to catbox")
                    print('[0m')
                    continue
                except urllib.error.URLError as e:
                    print('[1;31mConnection to ' + currentlink + ' failed.')
                    print("This colab session's server might doesn't have access to catbox")
                    print('[0m')
                    continue
                print(currentlink)
                currentcondition = f'Downloading {currentlink}...'
                progress(round(steps/totalsteps, 3), desc='Downloading ' + os.path.basename(currentlink) + '...')
                if everymethod == False:
                    hfdown(currentlink, currentfolder, choosedowner, 'default', currenttorename)
                else:
                    for xmethod in downmethod:
                        if prockilled == False:
                            hfdown(currentlink, currentfolder, xmethod, 'debugevery')
                steps += 1

            elif listpart.startswith("https://civitai.com/api/download/models/"): #@note civit direct
                currentlink, currenttorename = splitrename(listpart)
                if currenttorename == '':
                    currenttorename = getcivitname(listpart)
                    if currenttorename == '':
                        print("That CivitAI link no longer exist, or the server is currently down.")
                        continue
                progress(round(steps/totalsteps, 3), desc='Downloading ' + currenttorename + '...')
                print('\n')
                print(currentlink)
                currentcondition = f'Downloading {currentlink}...'
                # progress(round(steps/totalsteps, 3), desc='Downloading model number ' + os.path.basename(currentlink) + '...')
                if everymethod == False:
                    hfdown(currentlink, currentfolder, choosedowner, 'default', currenttorename)
                    configlink = checkcivitconfig(currentlink)
                    if not configlink=='':
                        namefile= os.path.splitext(currenttorename.split('?')[0])[0]
                        currenttorename = namefile + '.yaml'
                        hfdown(configlink, currentfolder, choosedowner, 'default', currenttorename)
                else:
                    for xmethod in downmethod:
                        if prockilled == False:
                            hfdown(currentlink, currentfolder, xmethod, 'debugevery')
                # civitdown(currentlink, currentfolder, currenttorename)
                steps += 1

            elif listpart.startswith("https://github.com"):
                currentlink, currenttorename = splitrename(listpart)
                print('\n')
                print(currentlink)
                if '/raw/' in listpart or '/releases/download/' in listpart:
                    currentcondition = f'Downloading {currentlink}...'
                    progress(round(steps/totalsteps, 3), desc='Downloading ' + os.path.basename(currentlink) + '...')
                    if everymethod == False:
                        hfdown(currentlink, currentfolder, choosedowner, 'default', currenttorename)
                    else:
                        for xmethod in downmethod:
                            if prockilled == False:
                                hfdown(currentlink, currentfolder, xmethod, 'debugevery')
                else:
                    splits = listpart.split('#')[0].split("/")
                    currentlink = "/".join(splits[:5])
                    foldername = listpart.split('#')[0].rsplit('/', 1)[-1]
                    folderpath = os.path.join(extpath, foldername)
                    currentcondition = f'Cloning {currentlink}...'
                    progress(round(steps/totalsteps, 3), desc='Cloning from ' + currentlink.split('/', 3)[-1] + '...')
                    if platform.system() == "Windows":
                        runwithsubprocess(f"git clone {currentlink} {shlex.quote(folderpath)}")
                    else:
                        runwithsubprocess(f"git clone {currentlink} {folderpath}")
                steps += 1

            elif listpart.startswith("https://civitai.com/models/"):
                currentlink, currenttorename = splitrename(listpart)
                print('\n')
                print(currentlink)
                currentcondition = f'Downloading {currentlink}...'
                progress(round(steps/totalsteps, 3), desc='Downloading ' + os.path.basename(currentlink) + '...')
                if everymethod == False:
                    civitdown2(currentlink, currentfolder, choosedowner, False, civitdefault, civitpruned, civitvae)
                # else:
                #     for xmethod in downmethod:
                #         if prockilled == False:
                #             civitdown2(currentlink, currentfolder, xmethod, True)
                steps += 1

            elif listpart.startswith("!"):
                commandtorun = listpart[1:]
                currentcondition = f'Running command: {commandtorun}'
                progress(round(steps/totalsteps, 3), desc=currentcondition)
                runwithsubprocess(commandtorun, None, True)
                steps += 1
            
            elif listpart.startswith("#debugeverymethod") and globaldebug == True and gradiostate == True:
                print('\n')
                everymethod = True
                print('[1;32mDebugEveryMethod activated!')
                print('[1;32mOne link will be downloaded with every possible download method.')
                print('[0m')

            elif listpart.startswith("#debugresetdownloads") and snapshot != {} and globaldebug == True:
                print('\n')
                currentcondition = f'Removing downloaded files...'
                removed_files = global_rewind()
                oldfilesdict = trackall()
                texttowrite = ["⬇️Removed files⬇️"]
                for item in removed_files:
                    texttowrite.append(item)
                writefinal = list_to_text(texttowrite)
                printdebug(str(writefinal))

            elif listpart.startswith("#extract"): #@note hashtagextract
                print('\n')
                currentcondition = 'Extracting every 7z file in current directory...'
                print('Extracting every 7z file in current directory...\n')
                extractcurdir(currentfolder)

            elif listpart.startswith("@new"): #WIP #@note hashtagcustom
                newcommand, newhashtag, newpath = shlex.split(listpart)
                if newcommand and newhashtag and newpath:
                    if newhashtag.startswith("#"):
                        newtype = newhashtag[1:]
                        global typemain
                        global typechecker
                        if not newtype in typemain and not newpath in typechecker:
                            try:
                                typemain.append(newtype)
                                print('typemain: ' + str(typemain))
                                typechecker.append(newtype)
                                print('typechecker: ' + str(typechecker))
                                newglobalpath = newtype + "path"
                                print('newglobalpath: ' + newtype + "path")
                                newpath = os.path.abspath(os.path.normpath(newpath).rstrip(os.sep))
                                os.makedirs(newpath, exist_ok=True)
                                globals()[newglobalpath] = newpath
                                print("modelpath = " + eval(newglobalpath))
                                # global addedcustompath
                                addedcustompath[newhashtag] = newpath
                                printdebug("addedcustompath: " + str(addedcustompath))
                                print(f"New custom path added!\n{newhashtag} means {newpath}")
                            except Exception as e:
                                print("Adding custom path failed! Reason: " + e)

            else:
                for prefix in typechecker:
                    if listpart.startswith("#" + prefix):
                        if prefix in ["embedding", "embeddings", "embed", "embeds","textualinversion", "ti"]:
                            currentfolder = embedpath
                        elif prefix in ["model", "models", "checkpoint", "checkpoints"]:
                            currentfolder = modelpath
                        elif prefix in ["vae", "vaes"]:
                            currentfolder = vaepath
                        elif prefix in ["lora", "loras"]:
                            currentfolder = lorapath
                        elif prefix in ["hypernetwork", "hypernetworks", "hypernet", "hypernets", "hynet", "hynets",]:
                            currentfolder = hynetpath
                        elif prefix in ["addnetlora", "loraaddnet", "additionalnetworks", "addnet"]:
                            currentfolder = addnetlorapath
                        elif prefix in ["controlnet", "cnet"]:
                            currentfolder = cnetpath
                        elif prefix in ["aestheticembedding", "aestheticembed"]:
                            currentfolder = aestheticembedpath
                        os.makedirs(currentfolder, exist_ok=True)
                
        else:
            currentcondition = 'Operation cancelled'
            return "Operation cancelled"

    currentcondition = 'Writing output...'
    downloadedfiles = writeall(oldfilesdict, isshell, addedcustompath)
    for tokill in everyprocessid:
        try:
            os.kill(tokill, signal.SIGTERM)
        except ProcessLookupError:
            pass
        except PermissionError:
            pass
        except OSError:
            pass
    print()
    print('[1;32mBatchLinks Downloads finished!')
    print('[0m')
    currentcondition = 'Done!'
    printdebug(f"this should be the output:\n" + str(downloadedfiles))
    if gradiostate == True:
        return [downloadedfiles, gr.Dataframe.update(value=buildarrayofhashtags('right')), gr.Dataframe.update(value=buildarrayofhashtags('bottom'))]  #@note dataframe
    else:
        return [downloadedfiles, gr.Dataframe.update(value=buildarrayofhashtags('right')), gr.Dataframe.update(value=buildarrayofhashtags('bottom')), gr.Button.update(visible=resumebuttonvisible)]

wildcardcommand = [
    "#debugeverymethod", "#debugresetdownloads",
    "#extract"
]

def extract_links(string):
    links = []
    lines = string.split('\n')
    for line in lines:
        line = line.split('##')[0].strip()
        if line.startswith(tuple(supportedlinks)):
            links.append(line)
        elif line.startswith(tuple(wildcardcommand)):
            links.append(line)
        elif line.startswith("!"):
            links.append(line.strip())
        elif line.startswith("@new"):
            links.append(line.strip())
        else:
            for prefix in typechecker:
                if line.startswith("#" + prefix):
                    links.append(line)

    #print(f"links: {links}")
    return links

def list_to_text(lst):
    stripped_list = [item.strip(',').strip('\"') for item in lst]
    return '\n'.join(stripped_list)

def uploaded(textpath):
    if not textpath is None:
        print(textpath)
        file_paths = textpath.name
        print(file_paths)
        links = []

        with open(file_paths, 'r') as file:
            for line in file:
                if line.startswith(tuple(supportedlinks)):
                    links.append(line.strip())
                elif line.startswith("!"):
                    links.append(line.strip())
                elif line.startswith("@new"):
                    links.append(line.strip())
                elif line.startswith(tuple(wildcardcommand)):
                    links.append(line.strip())
                else:
                    for prefix in typechecker:
                        if line.startswith("#" + prefix):
                            links.append(line.strip())

        text = list_to_text(links)
        return text    

count = 0
def keeplog():
    global currentcondition
    global currentsuboutput
    global logging
    if logging == False:
        currentcondition = "Logging activated."
        currentsuboutput = ''
        logging = True
        return [currentcondition, gr.Button.update(visible=True), gr.Button.update(visible=False)]
    if currentsuboutput == '':
        return [currentcondition, gr.Button.update(visible=True), gr.Button.update(visible=False)]
    else:
        return [f"{currentcondition}\n{currentsuboutput}", gr.Button.update(visible=True), gr.Button.update(visible=False)]

def offlog():
    global currentcondition
    global currentsuboutput
    global logging
    if logging == True:
        currentcondition = "Logging deactivated."
        currentsuboutput = ''
        logging = False
    return [f"{currentcondition}", gr.Button.update(visible=False), gr.Button.update(visible=True)]
    
def empty():
  return ''

def cancelrun():
    global processid
    global prockilled
    printdebug("debug processid: " + str(processid))
    if not processid == '':
        try:
            os.kill(processid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        except PermissionError:
            pass
        except OSError:
            pass
        #os.killpg(os.getpgid(processid.pid), signal.SIGTERM)
    prockilled = True
    if prockilled == True and globaldebug == True:
        print()
        print("This should kill")
        print()
    return "Operation Cancelled"

def fillbox():
    global remaininglinks
    if bool(remaininglinks):
        text = list_to_text(remaininglinks)
        remaininglinks = []
        return [text, 'Links updated!\nClick Download All! to download the rest of the links', gr.Button.update(visible=False)]
    return ['', '', gr.Button.update(visible=False)]

def stretchui(stretch):
    if stretch:
        return [gr.Box.update(visible=False), gr.Accordion.update(visible=False), gr.Accordion.update(visible=True)] 
    else:
        return [gr.Box.update(visible=True), gr.Accordion.update(visible=True), gr.Accordion.update(visible=False)] 
    
def hidehelp(hide):
    if hide:
        return [gr.Markdown.update(value=titletext), gr.Markdown.update(visible=False)]
    else:
        return [gr.Markdown.update(value=introductiontext), gr.Markdown.update(visible=True)]

countofdefaulthashtags = len(typemain)
def buildarrayofhashtags(rightorbottom):
    printdebug(f"buildarray {rightorbottom} initiated!")
    defaultpathtime = True
    def writingpath(j, path):
        if defaultpathtime:
            return path + " (default path)"
        else:
            if rightorbottom == 'right' and j < countofdefaulthashtags:
                return path.replace(script_path, "~")
            else:
                return path
    hashtagandpath = []
    for i, x in enumerate(typemain):
        try:
            xpath = eval(x+"path")
            hashtagandpath.append(["#"+x, writingpath(i, xpath)])
            defaultpathtime = False
        except Exception as e:
            print(e)
    return hashtagandpath

titletext = f"""<h3 style="display: inline-block; font-size: 20px;">⬇️ Batchlinks Downloader ({currentversion}) {latestversiontext}</h3>"""
introductiontext = f"""
{titletext}
<h5 style="display: inline-block; font-size: 14px;"><a href="https://github.com/etherealxx/batchlinks-webui#latest-release-{currentverforlink}">(what's new?)</a></h5>
<p style="font-size: 14px;;">This tool will read the textbox and download every links from top to bottom one by one<br/>
Put your links down below. Supported link: Huggingface, CivitAI, MEGA, Discord, Github, Catbox, Google Drive, Pixeldrain, Mediafire, Anonfiles, Dropbox<br/>
Use hashtag to separate downloaded items based on their download location<br/>
Valid hashtags: <code>#embed</code>, <code>#model</code>,  <code>#hypernet</code>, <code>#lora</code>, <code>#vae</code>, <code>#addnetlora</code>, etc.<br/>
(For colab that uses sd-webui-additional-networks extension to load LoRA, use <code>#addnetlora</code> instead)<br/>
Use double hashtag after links for comment</p>
"""
knowmoretext = f"""
<p style="font-size: 14px;">Click these links for more:<br/>
<a href="https://github.com/etherealxx/batchlinks-webui">Readme Page</a><br/>
<a href="https://github.com/etherealxx/batchlinks-webui#example">Example</a><br/>
<a href="https://github.com/etherealxx/batchlinks-webui#syntax">Syntax</a><br/>
<a href="https://github.com/etherealxx/batchlinks-webui#valid-hashtags">Valid Hashtags</a><br/>
<a href="https://github.com/etherealxx/batchlinks-webui/blob/main/howtogetthedirectlinks.md">Here's how you can get the direct links</a><br/>
<a href="https://github.com/etherealxx/batchlinks-webui/issues">Report Bug</a></p>
"""

def on_ui_tabs():     
    with gr.Blocks() as batchlinks:
        with gr.Row():
          with gr.Column(scale=2):
            introduction = gr.Markdown(introductiontext)
          with gr.Column(scale=1):
            with gr.Row():
                uistretcher = gr.Checkbox(value=False, label="Stretch UI", interactive=True)
                helphider = gr.Checkbox(value=False, label="Hide Help", interactive=True)
            knowmore = gr.Markdown(knowmoretext)
        with gr.Group():
          command = gr.Textbox(label="Links", placeholder="type here", lines=5)
          if gradiostate == True:
            logbox = gr.Textbox(label="Log", interactive=False)
          else:
            logbox = gr.Textbox("(use --gradio-queue args on launch.py to enable optional logging)", label="Log", interactive=False)

          with gr.Row():
            with gr.Box():
                if gradiostate == True:
                    with gr.Row():
                    #   gr.Textbox(value=None, interactive=False, show_label=False)
                        btn_onlog = gr.Button("Turn On Logging", variant="primary", visible=True)
                        btn_offlog = gr.Button("Turn Off Logging", visible=False)
                        loggingon = btn_onlog.click(keeplog, outputs=[logbox, btn_offlog, btn_onlog], every=1)
                        btn_offlog.click(offlog, outputs=[logbox, btn_offlog, btn_onlog], cancels=[loggingon])
                        #   gr.Textbox(value=None, interactive=False, show_label=False)
                    #   logging = gr.Radio(["Turn On Logging"], show_label=False)
                    #   logging.change(keeplog, outputs=logbox, every=1)
                    out_text = gr.Textbox(label="Output")
                else:
                    print("Batchlinks webui extension: (Optional) Use --gradio-queue args to enable logging & cancel button on this extension")
                    out_text = gr.Textbox("(If this text disappear, that means a download session is in progress.)", label="Output")

                # if platform.system() == "Windows":
                #     choose_downloader = gr.Radio(["gdown", "wget", "curl"], value="gdown", label="Download method")
                # else:
                with gr.Row():
                    
                    if gradiostate == True:
                        with gr.Column(scale=2):
                            choose_downloader = gr.Radio(["gdown", "wget", "curl", "aria2"], value="gdown", label="Download method")
                    else:
                        with gr.Column(scale=1):
                            choose_downloader = gr.Radio(["aria2"], value="aria2", label="Downloader")
                    with gr.Box():
                        with gr.Column(scale=1):
                            civit_default = gr.Radio(["ckpt", "safetensors"], value="safetensors", label="CivitAI Preferred Model Type", interactive=True)
                            with gr.Row():
                                civit_ispruned = gr.Checkbox(True, label="Pruned", interactive=True)
                                civit_alsodownvae = gr.Checkbox(True, label="Also Download VAE", interactive=True)

                with gr.Row():
                    if gradiostate == True:
                        with gr.Column(scale=2, min_width=100):
                            btn_run = gr.Button("Download All!", variant="primary")
                        # btn_upload = gr.UploadButton("Upload .txt", file_types="text")
                        # btn_upload.upload(uploaded, btn_upload, file_output)
                        with gr.Column(scale=1, min_width=100):
                            btn_cancel = gr.Button("Cancel")
                                        
                    else:
                        btn_run = gr.Button("Download All!", variant="primary")
                        btn_resume = gr.Button("Resume Download", visible=False)
                    with gr.Column(scale=1, min_width=100):
                        file_output = gr.UploadButton(file_types=['.txt'], label='Upload txt')
                if gradiostate == False:
                    with gr.Row():
                        gr.Markdown(
                        f"""
                        <p style="font-size: 14px; text-align: center; line-height: 90%;;"><br/>After clicking the Download All button, it's recommended to inspect the
                        colab console, as every information about the download progress is there.</p>
                        """)

                if gradiostate == False:
                    btn_resume.click(fillbox, None, outputs=[command, out_text, btn_resume])

                # file_output = gr.File(file_types=['.txt'], label="you can upload a .txt file containing links here")
                # file_output.change(uploaded, file_output, command)

                file_output.upload(uploaded, file_output, command)
            with gr.Box(visible=True) as boxtohide:
                # gr.Markdown("""
                # <h5 style="text-align: center; vertical-align: middle; font-size: 14px;">If you feel the UI is too cramped, click the Stretch UI button above.</h5>
                # """)
                with gr.Accordion("List of Every Hashtags and its Path", open=False, visible=True) as rightlist:
                    righttable = gr.DataFrame(
                    buildarrayofhashtags('right'),
                    headers=["hashtag", "path"],
                    datatype=["str", "str"],
                    interactive=False
                    )
                # sidetext = gr.Markdown(knowmoretext, visible=True)
            finish_audio = gr.Audio(interactive=False, value=os.path.join(extension_dir, "notification.mp3"), elem_id="finish_audio", visible=False)
        # gr.Markdown(
        # f"""
        # <center><p style="font-size: 14px;">Current default save directory: {modelpath}</p></center>
        # """)
        with gr.Accordion("List of Every Hashtags and its Path", open=False, visible=False) as bottomlist:
            bottomtable = gr.DataFrame(
                buildarrayofhashtags('bottom'),
                headers=["hashtag", "path"],
                datatype=["str", "str"],
                interactive=False,
            )
        helphider.change(hidehelp, helphider, outputs=[introduction, knowmore])
        uistretcher.change(stretchui, uistretcher, outputs=[boxtohide, rightlist, bottomlist])
        #batchlinks.load(debug, output=debug_txt, every=1)
        if gradiostate == True:
            run_event = btn_run.click(run, inputs=[command, choose_downloader, civit_default, civit_ispruned, civit_alsodownvae], outputs=[out_text, righttable, bottomtable])
            btn_cancel.click(cancelrun, None, outputs=out_text, cancels=[run_event])
        else:
            btn_run.click(run, inputs=[command, choose_downloader, civit_default, civit_ispruned, civit_alsodownvae], outputs=[out_text, righttable, bottomtable, btn_resume])
        
    if sdless:
        if platform.system() == "Windows":
            batchlinks.queue(64).launch(inbrowser=True)
        else:
            batchlinks.queue(64).launch(share=True)
    else:
        return (batchlinks, "Batchlinks Downloader", "batchlinks"),
if not sdless:
    script_callbacks.on_ui_tabs(on_ui_tabs)
else:
    on_ui_tabs()