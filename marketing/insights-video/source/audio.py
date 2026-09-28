"""Soundtrack for the insights video: synthesized music + SFX + voiceover, ducked and mixed to mix.wav.
usage: python audio.py <work> [duration]   (voice wavs in <work>/vo/, cue offsets in <work>/vo/cues.json)"""
import json, sys
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, resample_poly

S = sys.argv[1]
SR = 44100
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 65.0
N = int(DUR * SR)
rng = np.random.default_rng(11)
t_all = np.arange(N) / SR

def buf(): return np.zeros((N, 2))
def lp(x, f, order=2): return sosfilt(butter(order, f, 'low', fs=SR, output='sos'), x, axis=0)
def hp(x, f, order=2): return sosfilt(butter(order, f, 'high', fs=SR, output='sos'), x, axis=0)
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], 'band', fs=SR, output='sos'), x, axis=0)
def midi(n): return 440.0 * 2 ** ((n - 69) / 12)
def put(dst, sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= N: return
    if sig.ndim == 1: sig = np.stack([sig * (1 - max(0, pan)), sig * (1 + min(0, pan))], 1)
    j = min(N, i + len(sig)); dst[i:j] += sig[:j - i] * gain
def env_adsr(n, a=.01, d=.1, s=.7, r=.2, hold=None):
    L = n / SR; hold = L - a - d - r if hold is None else hold
    pts = [(0, 0), (a, 1), (a + d, s), (a + d + max(0, hold), s), (a + d + max(0, hold) + r, 0)]
    xs, ys = zip(*pts); return np.interp(np.arange(n) / SR, xs, ys)
def saw(f, n, detune=0.0):
    tt = np.arange(n) / SR; out = 0
    for d in (-detune, 0, detune):
        ph = (tt * f * (1 + d)) % 1.0; out = out + (2 * ph - 1)
    return out / 3

def tick(g=1.0):
    k = int(.03 * SR); x = hp(rng.standard_normal(k), 7000) * np.exp(-np.arange(k) / (SR * .008)); return x * g
def sub(f=55, L=.35, g=1.0):
    k = int(L * SR); tt2 = np.arange(k) / SR; fr = f * (1 + 1.5 * np.exp(-tt2 * 30))
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-tt2 * 7) * g
def riser(L, g=1.0):
    k = int(L * SR); tt2 = np.arange(k) / SR; x = rng.standard_normal(k)
    y = np.zeros(k); ch = SR // 20
    for i in range(0, k, ch):
        f = 400 + 7000 * (i / k) ** 2; y[i:i + ch] = bp(x[i:i + ch], f, f * 1.6)
    tone = np.sin(2 * np.pi * np.cumsum(200 + 900 * (tt2 / L) ** 2) / SR) * .25
    e = (tt2 / L) ** 2.2
    return (y * .8 + tone) * e * g
def pad_chord(notes, L, g):
    k = int(L * SR); x = sum(saw(midi(m), k, .006) for m in notes) / len(notes)
    x = lp(x, 1800) * env_adsr(k, .25, .3, .8, .6)
    return np.stack([x, np.roll(x, 441)], 1) * g
def pluck(f, L=.35, g=1.0):
    k = int(L * SR); tt2 = np.arange(k) / SR
    x = (np.sin(2 * np.pi * f * tt2) + .5 * np.sin(4 * np.pi * f * tt2) + .25 * np.sin(6 * np.pi * f * tt2)) * np.exp(-tt2 * 11)
    return x * g
def kick(g=1.0):
    k = int(.4 * SR); tt2 = np.arange(k) / SR; fr = 48 + 110 * np.exp(-tt2 * 35)
    return (np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-tt2 * 9) + hp(rng.standard_normal(k), 3000) * np.exp(-tt2 * 200) * .2) * g
def clap(g=1.0):
    k = int(.25 * SR); tt2 = np.arange(k) / SR; x = bp(rng.standard_normal(k), 900, 4000)
    e = np.exp(-tt2 * 22) + .6 * np.exp(-np.maximum(0, tt2 - .012) * 30) * (tt2 > .012)
    return x * e * g
def hat(g=1.0, L=.06):
    k = int(L * SR); return hp(rng.standard_normal(k), 8000) * np.exp(-np.arange(k) / (SR * L / 5)) * g

def whoosh(L=.6, g=1.0, up=True):
    k = int(L * SR); tt2 = np.arange(k) / SR; x = rng.standard_normal(k); y = np.zeros(k); ch = SR // 40
    for i in range(0, k, ch):
        p = i / k; f = (500 + 4000 * p) if up else (4500 - 4000 * p); y[i:i + ch] = bp(x[i:i + ch], f, f * 1.8)
    e = np.sin(np.pi * np.clip(tt2 / L, 0, 1)) ** 2
    return y * e * g
def click(g=1.0):
    k = int(.05 * SR); tt2 = np.arange(k) / SR
    return (np.sin(2 * np.pi * 1800 * tt2) * np.exp(-tt2 * 180) + bp(rng.standard_normal(k), 2000, 6000) * np.exp(-tt2 * 400) * .5) * g
def pop(f=880, g=1.0):
    k = int(.18 * SR); tt2 = np.arange(k) / SR; fr = f * (1 + .6 * np.exp(-tt2 * 40))
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-tt2 * 25) * g
def bell(freqs, L=2.5, g=1.0):
    k = int(L * SR); tt2 = np.arange(k) / SR
    return sum(np.sin(2 * np.pi * f * tt2) * np.exp(-tt2 * (1.5 + i * .6)) + .3 * np.sin(2 * np.pi * f * 2.76 * tt2) * np.exp(-tt2 * 5) for i, f in enumerate(freqs)) / len(freqs) * g
def boom(g=1.0):
    k = int(1.6 * SR); tt2 = np.arange(k) / SR; fr = 38 + 90 * np.exp(-tt2 * 12)
    return (np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-tt2 * 2.2) + lp(rng.standard_normal(k), 6000) * np.exp(-tt2 * 5) * .35) * g


OFF = {'hook': .5, 'stat1': 8.6, 'need': 15.4, 'without': 24.3, 'with': 33.7, 'stat2': 38.8, 'judge': 48.4, 'end': 58.1}
CUES = json.load(open(f'{S}/vo/cues.json'))
def T(k, i): return OFF[k] + CUES[k]['at'][i]
HIT77, HIT75, FAIL, BOOKED, TAP = T('stat1', 1) + .15, 41.95, T('without', 3), T('with', 2), T('with', 1) + .15

BPM = 96; BEAT = 60 / BPM; BAR = 4 * BEAT
music = buf()
AM = [(45, [57, 60, 64, 69]), (41, [57, 60, 65, 69]), (48, [55, 60, 64, 67]), (43, [55, 59, 62, 67])]    # Am F C G
LIFT = [(48, [60, 64, 67, 72]), (41, [60, 65, 69, 72]), (43, [59, 62, 67, 71]), (48, [60, 64, 67, 72])]  # C F G C

# --- intro drone (0 → 15.4), filter opening towards the 77% hit
n = int(15.6 * SR); tt = np.arange(n) / SR
drone = sum(saw(midi(m), n, .004) * g for m, g in ((45, .5), (52, .3), (57, .25), (60, .15)))
cut = 250 + 1500 * np.clip(tt / 10.3, 0, 1) ** 2
o = np.zeros(n); ch = SR // 10
for i in range(0, n, ch): o[i:i + ch] = lp(drone[i:i + ch], float(cut[min(n - 1, i)]))
o *= np.clip(tt / 2, 0, 1) * np.clip((15.6 - tt) / .8, 0, 1) * .42
put(music, np.stack([o, np.roll(o, 300)], 1), 0)
for k in range(int(15.4 / (BEAT / 2))):
    tb = k * BEAT / 2
    if 2.0 <= tb < 15.2: put(music, tick(.06 + .08 * tb / 15), tb, pan=.3 if k % 2 else -.3)
for k in range(int(15.4 / BEAT)):
    tb = k * BEAT
    if 4.5 <= tb < 15.2: put(music, sub(55, .4, .45 + .4 * tb / 15), tb)
put(music, riser(1.6, .3), HIT77 - 1.6)

def groove(t0, t1, prog, drums=True, pad=.15, arp=0.0, clap_on=True):
    b = 0
    while t0 + b * BAR < t1:
        tb0 = t0 + b * BAR; root, notes = prog[b % 4]
        put(music, pad_chord(notes, min(BAR + .5, t1 - tb0 + .6), pad), tb0)
        for q in range(8):
            tq = tb0 + q * BEAT / 2
            if tq >= t1: break
            k = int(BEAT / 2 * SR); tt2 = np.arange(k) / SR
            put(music, lp(saw(midi(root - 12 + (12 if q in (3, 7) else 0)), k), 480) * np.exp(-tt2 * 5) * .5, tq, .45)
            if arp:
                m = notes[[0, 1, 2, 3, 2, 1, 2, 3][q]] + 12
                put(music, pluck(midi(m), .4, arp), tq, pan=(-.35 if q % 2 else .35))
        if drums:
            for q in range(4):
                tq = tb0 + q * BEAT
                if tq >= t1: break
                put(music, kick(.5), tq)
                if clap_on and q in (1, 3): put(music, clap(.13), tq)
                put(music, hat(.045), tq + BEAT / 2, pan=.25)
        b += 1

groove(15.4, FAIL, AM, drums=True, pad=.13)
# clock ticks building under "without"
for k in range(int((FAIL - 24.3) / (BEAT / 2))):
    tb = 24.3 + k * BEAT / 2; put(music, tick(.12 + .12 * k / 28), tb, pan=.4 if k % 2 else -.4)
put(music, riser(2.2, .3), FAIL - 2.2)
# the fail: music drops to a low drone until the light scene
k = int((33.35 - FAIL) * SR); tt2 = np.arange(k) / SR
dd = lp(saw(midi(33), k, .01) + saw(midi(40), k, .01) * .5, 300) * np.exp(-tt2 * .6) * .5
put(music, np.stack([dd, dd], 1), FAIL)
# lift: bright major with arps
groove(33.5, 38.3, LIFT, drums=False, pad=.17, arp=.13)
put(music, riser(3.4, .28), HIT75 - 3.4)
groove(HIT75, 57.6, AM, drums=True, pad=.14, arp=.07)
# ending: resolve chord, no drums
k = int((DUR - 57.8) * SR)
fin = sum(saw(midi(m), k, .006) for m in (45, 52, 57, 60, 64, 69)) / 6
fin = lp(fin, 1500) * np.clip(np.arange(k) / (SR * .4), 0, 1) * np.exp(-np.arange(k) / (SR * 3.5))
put(music, np.stack([fin, np.roll(fin, 441)], 1), 57.8, .32)
fade = np.clip(t_all / .6, 0, 1) * np.clip((DUR - t_all) / 1.2, 0, 1)
music *= fade[:, None]

# --- SFX
sfx = buf()
for tw in (8.3, 15.1, 23.95, 38.3, 48.2, 57.75):
    put(sfx, whoosh(.6, .22), tw - .2)
put(sfx, whoosh(.9, .28), 33.2)
for i in range(5): put(sfx, pop(700 + i * 90, .22), T('hook', 0) + .35 + i * .11)
for i in range(10): put(sfx, click(.09), T('hook', 1) + .15 + i * .12, pan=.2)
put(sfx, boom(.8), HIT77)
put(sfx, bell([midi(69), midi(72), midi(76)], 2.2, .14), HIT77 + .05)
for i in range(4): put(sfx, pop(620 + i * 110, .28), T('need', i + 2) - .05)
put(sfx, pop(520, .22), T('without', 0) + .15)
for i in range(4): put(sfx, click(.2), T('without', 0) + .9 + i * .45, pan=-.1)
put(sfx, pop(520, .22), T('without', 1)); put(sfx, pop(520, .22), T('without', 2))
for i in range(6): put(sfx, pop(1250, .06), T('without', 2) + .45 + i * .22)
put(sfx, boom(.75), FAIL); put(sfx, clap(.25), FAIL)
put(sfx, click(.4), TAP)
put(sfx, bell([midi(84), midi(88), midi(91)], 2.0, .24), BOOKED)
put(sfx, boom(.8), HIT75)
put(sfx, bell([midi(81), midi(84), midi(88)], 2.2, .16), HIT75 + .05)
put(sfx, pop(560, .25), T('judge', 1)); put(sfx, pop(880, .25), T('judge', 2))
put(sfx, bell([midi(81), midi(88)], 2.5, .14), T('end', 1))
if DUR > 66: put(sfx, bell([midi(76), midi(81), midi(88)], 3.0, .16), 64.95)

# --- voice
voice = np.zeros(N)
for key, at in OFF.items():
    a, sr = sf.read(f'{S}/vo/{key}.wav')
    a = resample_poly(a, 147, 80)
    i = int(at * SR); voice[i:i + len(a)] += a[:N - i]
voice = hp(voice, 80); voice = voice / np.abs(voice).max() * .89
voice = voice + bp(voice, 2500, 6000) * .25
e = np.abs(voice); win = int(.02 * SR); e = np.convolve(e, np.ones(win) / win, mode='same')
env = np.zeros(N); a_c, r_c = np.exp(-1 / (.03 * SR)), np.exp(-1 / (.35 * SR)); v = 0.0
for i in range(0, N, 64):
    x = e[i]; c = a_c ** 64 if x > v else r_c ** 64; v = c * v + (1 - c) * x; env[i:i + 64] = v
duck = 1 - .55 * np.clip(env / .08, 0, 1)
mix = music * duck[:, None] * .22 + sfx * .45 + np.stack([voice, voice], 1)
peak = np.abs(mix).max(); mix = mix / peak * .95
sf.write(f'{S}/mix.wav', mix.astype(np.float32), SR, subtype='FLOAT')
print('peak', round(peak, 3), 'dur', DUR)
