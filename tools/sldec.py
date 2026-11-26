"""sldec.py <in.SL?|dir> <outdir> : Quarantine II DOS CINEMA slideshows (11-25). File = u16 n_slides, then chunks of
(u32 len, data): data starting 'IMAGEX' (imgdec.py format) or 'GIF87a' = a slide, anything else = 8-bit unsigned mono PCM.
ATTRACT.SL? has one extra u16 after n (11025 = sample rate) and mixes audio chunks between slides; CINEMAn have slides only.
.SLA / .SLF / .SLG = English / French / German (text baked into the pictures). Writes <stem>_<ext>_NN.png and _NN.wav."""
import sys, os, glob, struct, io, wave
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from imgdec import load
from PIL import Image
def chunks(d, attract):
    o = 4 if attract else 2
    while o + 4 <= len(d):
        l = struct.unpack_from('<I', d, o)[0]; yield d[o + 4:o + 4 + l]; o += 4 + l
    assert o == len(d), 'chunk overrun'
def one(p, outdir):
    d = open(p, 'rb').read(); base = os.path.basename(p).replace('.', '_'); ni = na = 0
    att = os.path.basename(p).upper().startswith('ATTRACT')
    tmp = os.path.join(outdir, '_slide.tmp')
    for c in chunks(d, att):
        if c[:6] == b'IMAGEX':
            open(tmp, 'wb').write(c); load(tmp).convert('RGB').save(os.path.join(outdir, '%s_%02d.png' % (base, ni))); ni += 1
        elif c[:3] == b'GIF':
            Image.open(io.BytesIO(c)).convert('RGB').save(os.path.join(outdir, '%s_%02d.png' % (base, ni))); ni += 1
        else:
            w = wave.open(os.path.join(outdir, '%s_%02d.wav' % (base, na)), 'wb'); w.setnchannels(1); w.setsampwidth(1)
            w.setframerate(11025); w.writeframes(c); w.close(); na += 1
    if os.path.exists(tmp): os.remove(tmp)
    assert ni == struct.unpack_from('<H', d, 0)[0], 'slide count'
    return ni, na
def main(a):
    src, outdir = a; os.makedirs(outdir, exist_ok=True)
    files = sorted(glob.glob(os.path.join(src, '*.SL?'))) if os.path.isdir(src) else [src]
    t = [one(f, outdir) for f in files]; print('files', len(files), 'slides', sum(x for x, _ in t), 'audio', sum(y for _, y in t))
if __name__ == '__main__': main(sys.argv[1:])
