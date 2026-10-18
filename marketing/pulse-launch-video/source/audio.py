"""Builds the soundtrack: synthesized music + SFX + voiceover, ducked and mixed to mix.wav."""
import json, sys
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, resample_poly

S = sys.argv[1]
SR = 44100
DUR = 90.0
N = int(DUR * SR)
rng = np.random.default_rng(7)
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

BPM = 110; BEAT = 60 / BPM; BAR = 4 * BEAT
HIT = 19.72                     # logo reveal downbeat
grid0 = HIT - 36 * BEAT
def beat_t(k): return grid0 + k * BEAT

music = buf()

# ---------- Section A: tension (0 → HIT) ----------
n = int(HIT * SR) + SR
tt = np.arange(n) / SR
drone = 0
for m, g in ((45, .5), (52, .35), (57, .3), (60, .18)):          # A2 E3 A3 C4
    drone = drone + saw(midi(m), n, .004) * g
cut = 300 + 1400 * np.clip(tt / HIT, 0, 1) ** 2
# time-varying lowpass: process in chunks
out = np.zeros(n); ch = SR // 10
for i in range(0, n, ch):
    out[i:i + ch] = lp(drone[i:i + ch], float(cut[min(n - 1, i)]))
out *= np.clip(tt / 2.5, 0, 1) * (1 - np.clip((tt - HIT + .05) / .1, 0, 1)) * .44
put(music, np.stack([out, np.roll(out, 300)], 1), 0)

# soft ticking from the problem section, sub pulse building towards the reveal
def tick(g=1.0):
    k = int(.03 * SR); x = hp(rng.standard_normal(k), 7000) * np.exp(-np.arange(k) / (SR * .008)); return x * g
def sub(f=55, L=.35, g=1.0):
    k = int(L * SR); tt2 = np.arange(k) / SR; fr = f * (1 + 1.5 * np.exp(-tt2 * 30))
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-tt2 * 7) * g
for k in range(0, 72):
    tb = grid0 + k * BEAT / 2
    if 6.4 <= tb < HIT - .05: put(music, tick(.1 + .1 * (tb - 6.4) / 13), tb, pan=.3 if k % 2 else -.3)
for k in range(0, 36):
    tb = beat_t(k)
    if 13.3 <= tb < HIT - .05: put(music, sub(55, .4, .7 + .5 * (tb - 13.3) / 6), tb)

# riser into the hit
def riser(L, g=1.0):
    k = int(L * SR); tt2 = np.arange(k) / SR; x = rng.standard_normal(k)
    y = np.zeros(k); ch = SR // 20
    for i in range(0, k, ch):
        f = 400 + 7000 * (i / k) ** 2; y[i:i + ch] = bp(x[i:i + ch], f, f * 1.6)
    tone = np.sin(2 * np.pi * np.cumsum(200 + 900 * (tt2 / L) ** 2) / SR) * .25
    e = (tt2 / L) ** 2.2
    return (y * .8 + tone) * e * g
put(music, riser(2.0, .35), HIT - 2.0)

# ---------- Section B: uplifting groove ----------
PROG = [(48, [60, 64, 67, 72]), (43, [59, 62, 67, 71]), (45, [57, 60, 64, 69]), (41, [57, 60, 65, 69])]   # C G Am F
END = 86.26
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

BREAK0, BREAK1 = HIT + 26 * BAR + 2 * BEAT, HIT + 28 * BAR   # drums drop out under "Stop guessing. Start knowing."
bars = int((END - HIT) / BAR) + 1
arp = buf()
for b in range(bars):
    t0 = HIT + b * BAR
    if t0 >= END: break
    root, notes = PROG[b % 4]
    put(music, pad_chord(notes, BAR + .5, .16), t0)
    for q in range(8):                                # bass: 8ths on the root
        tq = t0 + q * BEAT / 2
        k = int(BEAT / 2 * SR); tt2 = np.arange(k) / SR
        bs = lp(saw(midi(root - 12 + (12 if q in (3, 7) else 0)), k), 500) * np.exp(-tt2 * 5) * .5
        put(music, bs, tq, .5)
    for q in range(8):                                # pluck arpeggio, 8ths
        tq = t0 + q * BEAT / 2; m = notes[[0, 1, 2, 3, 2, 1, 2, 3][q]] + 12
        put(arp, pluck(midi(m), .4, .12), tq, pan=(-.35 if q % 2 else .35))
    drums = not (BREAK0 <= t0 < BREAK1)
    for q in range(4):
        tq = t0 + q * BEAT
        if not drums or tq >= END: continue
        if b >= 1 or q >= 0: put(music, kick(.55), tq)
        if q in (1, 3) and b >= 2: put(music, clap(.16), tq)
        put(music, hat(.05), tq + BEAT / 2, pan=.25)
        put(music, hat(.025), tq, pan=-.25)
# ping-pong delay on the arp
d = int(BEAT * .75 * SR); echo = np.zeros_like(arp)
echo[d:, 0] = arp[:-d, 1] * .35; echo[2 * d:, 1] = arp[:-2 * d, 0] * .25
music += lp(arp + echo, 5000)
put(music, riser(BREAK1 - BREAK0, .25), BREAK0)

# final chord ring-out
k = int((DUR - END) * SR)
fin = sum(saw(midi(m), k, .006) for m in (48, 55, 60, 64, 67, 72)) / 6
fin = lp(fin, 1600) * np.exp(-np.arange(k) / (SR * 1.8))
put(music, np.stack([fin, np.roll(fin, 441)], 1), END, .3)
put(music, kick(.6), END)

# master fade in/out
fade = np.clip(t_all / .8, 0, 1) * np.clip((DUR - t_all) / 1.5, 0, 1)
music *= fade[:, None]

# ---------- SFX ----------
sfx = buf()
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

for tw in (6.25, 13.3, 34.3, 47.2, 57.15, 65.25, 70.75):
    put(sfx, whoosh(.6, .22), tw - .15)
put(sfx, whoosh(.9, .25), 23.6)                      # phone rises in
put(sfx, whoosh(.7, .22, False), 18.75)              # everything collapses
put(sfx, whoosh(.7, .2), 80.0)
put(sfx, boom(.7), HIT)
put(sfx, bell([midi(72), midi(76), midi(79), midi(84)], 3.0, .22), HIT + .05)
put(sfx, bell([midi(84), midi(88)], 1.5, .12), 81.3)   # end card
for tc in (10.3, 11.2, 11.9): put(sfx, pop(520, .3), tc)
for tc in (36.05, 37.5, 39.3, 40.95, 42.3): put(sfx, pop(1040, .22), tc)
for tc in (51.9, 52.6, 53.3): put(sfx, pop(880, .22), tc)
for tc in (70.95, 72.3, 75.6): put(sfx, pop(660, .25), tc)
for i in range(4): put(sfx, pop(990, .12), 81.6 + i * .12)
for i in range(9): put(sfx, click(.18), 73.0 + (i + 1) * 1.3 / 9 - .02, pan=.2)   # pairing code typing
put(sfx, bell([midi(79), midi(83)], 1.2, .12), 68.5)   # goal ring fills
for clip, t0 in (('log', 25.0), ('metrics', 34.6), ('overview', 47.6), ('goals', 65.3)):
    for tp in json.load(open(f'{S}/clips/{clip}/meta.json'))['taps']:
        put(sfx, click(.32), t0 + tp['t'], pan=-.1)

# ---------- voice ----------
voice = np.zeros(N)
OFF = {'hook': .6, 'problem': 6.7, 'reveal': 20.0, 'log': 25.0, 'metrics': 34.6, 'overview': 47.6,
       'honest': 57.4, 'goals': 65.5, 'sync': 70.9, 'cta': 77.9}
for key, at in OFF.items():
    a, sr = sf.read(f'{S}/vo/{key}.wav')
    a = resample_poly(a, 147, 80)                     # 24 kHz → 44.1 kHz
    i = int(at * SR); voice[i:i + len(a)] += a[:N - i]
voice = hp(voice, 80)
voice = voice / np.abs(voice).max() * .89
# gentle presence lift
voice = voice + bp(voice, 2500, 6000) * .25

# duck music under the voice
e = np.abs(voice); win = int(.02 * SR)
e = np.convolve(e, np.ones(win) / win, mode='same')
env = np.zeros(N); a_c, r_c = np.exp(-1 / (.03 * SR)), np.exp(-1 / (.35 * SR)); v = 0.0
for i in range(0, N, 64):                             # coarse follower (fast enough, smooth enough)
    x = e[i]; c = a_c ** 64 if x > v else r_c ** 64; v = c * v + (1 - c) * x; env[i:i + 64] = v
env = np.clip(env / .08, 0, 1)
duck = 1 - .55 * env

mix = music * duck[:, None] * .2 + sfx * .45 + np.stack([voice, voice], 1) * 1.0
peak = np.abs(mix).max(); mix = mix / peak * .95
sf.write(f'{S}/mix.wav', mix.astype(np.float32), SR, subtype='FLOAT')
sf.write(f'{S}/music_only.wav', (music / np.abs(music).max() * .9).astype(np.float32), SR, subtype='FLOAT')
print('peak', peak, 'written', DUR)
bed = music * duck[:, None] * .2 + sfx * .45
def db(a): return 20 * np.log10(np.sqrt(np.mean(a ** 2)) + 1e-9)
for key, at in OFF.items():
    a, b = int((at + .3) * SR), int((at + 3) * SR)
    print(f'{key:9s} voice {db(voice[a:b]):6.1f}  bed {db(bed[a:b]):6.1f}  diff {db(voice[a:b]) - db(bed[a:b]):5.1f}')
