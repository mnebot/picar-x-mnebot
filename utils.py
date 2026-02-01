import os
import sys

GRAY = '1;30'
RED = '0;31'
GREEN = '0;32'
YELLOW = '0;33'
BLUE = '0;34'
PURPLE = '0;35'
DARK_GREEN = '0;36'
WHITE = '0;37'

def print_color(msg, end='\n', file=sys.stdout, flush=False, color=''):
    print('\033[%sm%s\033[0m'%(color, msg), end=end, file=file, flush=flush)

def gray_print(msg, end='\n', file=sys.stdout, flush=False):
    print_color(msg, end=end, file=file, flush=flush, color=GRAY)

def warn(msg, end='\n', file=sys.stdout, flush=False):
    print_color(msg, end=end, file=file, flush=flush, color=YELLOW)

def error(msg, end='\n', file=sys.stdout, flush=False):
    print_color(msg, end=end, file=file, flush=flush, color=RED)

def redirect_error_2_null():
    # https://github.com/spatialaudio/python-sounddevice/issues/11

    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(2)
    sys.stderr.flush()
    os.dup2(devnull, 2)
    os.close(devnull)
    return old_stderr

def cancel_redirect_error(old_stderr):
    os.dup2(old_stderr, 2)
    os.close(old_stderr)

def run_command(cmd):
    """
    Run command and return status and output

    :param cmd: command to run
    :type cmd: str
    :return: status, output
    :rtype: tuple
    """
    import subprocess
    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = p.stdout.read().decode('utf-8')
    status = p.poll()
    return status, result

def sox_volume(input_file, output_file, volume):
    import sox

    try:
        transform = sox.Transformer()
        transform.vol(volume)

        transform.build(input_file, output_file)

        return True
    except Exception as e:
        print(f"sox_volume err: {e}")
        return False


speak_first = False

def speak_block(music, name, volume=100):
    """
    speak, play audio with block

    :param name: the file name int the folder(SOUND_DIR)
    :type name: str
    :param volume: volume, 0-100
    :type volume: int
    """
    global speak_first
    is_run_with_root = (os.geteuid() == 0)
    if not is_run_with_root and not speak_first:
        speak_first = True
        # Running as normal user is fine with PulseAudio/PipeWire (e.g. systemd service).
        gray_print("Playing audio as non-root (PulseAudio/PipeWire).")
    # No fer killall pulseaudio quan s'usa PipeWire o com a servei systemd: pot tallar
    # el servidor de so i fer que la reproducció es quedi penjada. Només útil en entorn VNC.
    # _status, _ = run_command('sudo killall pulseaudio')

    if os.path.isfile(name):
        gray_print(f"[debug] speak_block: sound_play start {name}")
        try:
            music.sound_play(name, volume)
            gray_print("[debug] speak_block: sound_play done")
        except Exception as e:
            warn(f"[debug] speak_block: sound_play error: {e}")
    else:
        warn(f'No sound found for {name}')
        return False
