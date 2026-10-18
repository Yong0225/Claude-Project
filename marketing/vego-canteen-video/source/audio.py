"""Synthesized score + sound design for the VEGO CANTEEN website comparison video.
Reads out/sfx.json (event times exported by comp/index.html) and writes out/mix.wav (48 kHz stereo)."""
import json, sys
import numpy as np
from scipy import signal
import soundfile as sf

SR = 48000
DUR = 64.8
N = int(SR * DUR)
rng = np.random.default_rng(3)
music = np.zeros((N, 2))
fx = np.zeros((N, 2))

# ---------- time map (mirrors T in comp/index.html) ----------
T = dict(splitIn=3.0, splitOut=5.6, A0=5.9, ffA=24.3, ffB=25.7, giveUp=26.5, rew=29.4, iris=30.9,
         B0=31.6, phoneB=33.3, bOut=49.6, cmp=51.4, cmpOut=57.0, endIn=61.3)
BEAT = 0.5  # 120 bpm


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def env_adsr(n, a, d, s, r, sus_len=None):
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    if sus_len is None:
        sus_len = max(0, n - a - d - r)
    else:
        sus_len = int(sus_len * SR)
    e = np.concatenate([np.linspace(0, 1, a, endpoint=False), np.linspace(1, s, d, endpoint=False),
                        np.full(sus_len, s), np.linspace(s, 0, r)])
    if len(e) < n:
        e = np.pad(e, (0, n - len(e)))
    return e[:n]


def add(buf, t, x, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N or i + len(x) <= 0:
        return
    if i < 0:
        x = x[-i:]; i = 0
    x = x[: N - i]
    l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
    buf[i:i + len(x), 0] += x * gain * l * 1.414
    buf[i:i + len(x), 1] += x * gain * r * 1.414


def lp(x, fc, order=2):
    b, a = signal.butter(order, min(fc, SR / 2 - 100) / (SR / 2), 'low')
    return signal.lfilter(b, a, x)


def hp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), 'high')
    return signal.lfilter(b, a, x)


def bp(x, f1, f2, order=2):
    b, a = signal.butter(order, [f1 / (SR / 2), min(f2, SR / 2 - 100) / (SR / 2)], 'band')
    return signal.lfilter(b, a, x)


def tt(d):
    return np.arange(int(d * SR)) / SR


def noise(d):
    return rng.standard_normal(int(d * SR))


def sweep_sine(f0, f1, d, curve='exp'):
    t = tt(d)
    if curve == 'exp':
        f = f0 * (f1 / f0) ** (t / d)
    else:
        f = f0 + (f1 - f0) * t / d
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


# ---------- instruments ----------
def pad(notes, d, bright=1800, detune=0.12, a=1.2, r=1.5):
    t = tt(d); x = np.zeros_like(t)
    for n in notes:
        f = midi(n)
        for k, dt in enumerate((-detune, 0, detune)):
            ff = f * 2 ** (dt / 12)
            ph = rng.random()
            x += signal.sawtooth(2 * np.pi * ff * t + ph * 6.28) * (0.8 if k != 1 else 1)
    x = lp(x, bright) / (len(notes) * 3)
    return x * env_adsr(len(t), a, 0.3, 0.9, r)


def marimba(n, d=0.9):
    t = tt(d); f = midi(n)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t * 7) + 0.35 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 22) \
        + 0.12 * np.sin(2 * np.pi * f * 10 * t) * np.exp(-t * 40)
    return x * env_adsr(len(t), 0.002, 0.05, 1, 0.05)


def pluck(n, d=0.6, cut=2200):
    t = tt(d); f = midi(n)
    x = signal.sawtooth(2 * np.pi * f * t) * 0.6 + signal.square(2 * np.pi * f * t) * 0.3
    x = lp(x, cut) * np.exp(-t * 6)
    return x * env_adsr(len(t), 0.003, 0.05, 1, 0.05)


def bass(n, d, cut=500):
    t = tt(d); f = midi(n)
    x = np.sin(2 * np.pi * f * t) + 0.35 * lp(signal.sawtooth(2 * np.pi * f * t), cut)
    return x * env_adsr(len(t), 0.005, 0.1, 0.8, 0.08)


def kick(g=1.0, d=0.35):
    t = tt(d)
    f = 45 + 110 * np.exp(-t * 28)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)
    x[:200] += noise(200 / SR) * np.linspace(.4, 0, 200)
    return x * g


def clap():
    d = 0.22; t = tt(d); x = bp(noise(d), 900, 4000)
    e = np.exp(-t * 28)
    for o in (0.0, 0.011, 0.022):
        i = int(o * SR); e[i:i + 150] += 0.8
    return x * e * 0.5


def hat(d=0.05, open_=False):
    d = 0.3 if open_ else d
    t = tt(d); x = hp(noise(d), 7000)
    return x * np.exp(-t * (12 if open_ else 70)) * 0.35


def shaker():
    d = 0.08; t = tt(d); x = bp(noise(d), 5000, 11000)
    return x * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2 * 0.25


def tick(f=2600, d=0.03):
    t = tt(d)
    return (np.sin(2 * np.pi * f * t) + 0.5 * bp(noise(d), 2000, 6000)) * np.exp(-t * 180)


def bell(n, d=2.0):
    t = tt(d); f = midi(n)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t * 2.2) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 5) \
        + 0.2 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 9)
    return x * env_adsr(len(t), 0.002, 0.1, 1, 0.1)


# ---------- SCORE ----------
# Intro: dark drone + clock ticks
add(music, 0.2, pad([45, 52, 57], 5.9, bright=900, a=2.0, r=1.2), .30)
for i in range(int(5.8 / BEAT)):
    t0 = 0.4 + i * BEAT
    add(music, t0, tick(2200 if i % 2 == 0 else 1700), .10, pan=.3 if i % 2 else -.3)
add(music, T['splitIn'] - 1.2, lp(noise(1.2), 3000) * np.linspace(0, 1, int(1.2 * SR)) ** 3, .08)

# A section: minor tension groove, 5.9 -> 26.5
A_CH = [[45, 52, 57, 60], [41, 48, 53, 57], [43, 50, 55, 59], [40, 47, 52, 56]]  # Am F G E
A_BASS = [33, 29, 31, 28]
bar = 4 * BEAT
t = T['A0']; k = 0
while t < T['giveUp'] - 0.01:
    ch = A_CH[k % 4]
    dur = min(bar, T['giveUp'] - t)
    add(music, t, pad(ch, dur + 0.6, bright=1300, a=0.4, r=0.6), .20)
    for s in range(8):
        tb = t + s * BEAT / 2
        if tb >= T['giveUp']:
            break
        add(music, tb, bass(A_BASS[k % 4], BEAT / 2 * 0.9, cut=300), .28 * (1.0 if s % 2 == 0 else .6))
    for s in range(4):
        tb = t + s * BEAT
        if tb >= T['giveUp']:
            break
        if s in (0, 2):
            add(music, tb, kick(.8), .45)
        add(music, tb + BEAT / 2, tick(3000, .02), .08)
    for s in range(16):
        tb = t + s * BEAT / 4
        if tb < T['giveUp']:
            add(music, tb, hat(), .10 if s % 4 else .16, pan=.25)
    # sparse minor pluck motif
    motif = [ch[3] + 12, ch[2] + 12, ch[1] + 12]
    for j, n in enumerate(motif):
        tb = t + (1.5 + j * .5) * BEAT
        if tb < T['giveUp'] - .2:
            add(music, tb, pluck(n, .5, 1600), .09, pan=-.3 + j * .3)
    t += bar; k += 1

# fast-forward riser (music side)
ffd = T['ffB'] - T['ffA'] + .3
add(music, T['ffA'], hp(noise(ffd), 1500) * np.linspace(0, 1, int(ffd * SR)) ** 2, .10)
for i in range(int((T['ffB'] - T['ffA']) / .08)):
    add(music, T['ffA'] + i * .08, tick(3400, .015), .08)

# give-up: cut to dark low drone + sub boom
add(music, T['giveUp'] + .2, pad([33, 40, 45], 3.4, bright=500, a=.05, r=1.5), .35)
add(music, T['giveUp'] + .2, bell(45, 3.0), .18)

# rewind -> iris : reverse swell
d = T['iris'] - T['rew'] + .2
rev = pad([48, 55, 60, 64], d, bright=2500, a=.02, r=.02)[::-1] * np.linspace(0, 1, int(d * SR)) ** 2
add(music, T['rew'], rev, .45)

# B title: warm major chord + shimmer
add(music, T['iris'], pad([48, 55, 59, 64, 67], T['phoneB'] - T['iris'] + 1.0, bright=3500, a=.3, r=1.0), .28)
for j, n in enumerate([72, 76, 79, 83, 84]):
    add(music, T['iris'] + .15 + j * .12, bell(n, 1.8), .07, pan=-.4 + j * .2)

# B groove: C Am F G, 120bpm
B_CH = [[48, 52, 55, 59], [45, 52, 57, 60], [41, 48, 53, 57], [43, 50, 55, 59]]
B_BASS = [36, 33, 29, 31]
ARP = [[72, 76, 79, 76, 74, 76, 79, 83], [72, 76, 81, 76, 72, 76, 81, 84], [69, 72, 77, 72, 69, 72, 77, 81], [71, 74, 79, 74, 71, 74, 79, 83]]
t = T['phoneB']; k = 0
B_END = T['cmpOut']
while t < B_END - 0.01:
    ch = B_CH[k % 4]
    full = t >= T['phoneB'] + 2 * bar  # drums enter after two bars
    big = t >= T['cmp'] - .1
    add(music, t, pad(ch, bar + .6, bright=2600, a=.25, r=.6), .16)
    for s in range(4):
        tb = t + s * BEAT
        if tb >= B_END:
            break
        add(music, tb, kick(.9), .50 if full else .30)
        if full and s in (1, 3):
            add(music, tb, clap(), .35)
        if big:
            add(music, tb + BEAT / 2, hat(open_=True), .10, pan=.2)
    for s in range(16):
        tb = t + s * BEAT / 4
        if tb < B_END and full:
            add(music, tb, shaker(), .22 if s % 2 else .12, pan=-.3)
    for s in range(8):
        tb = t + s * BEAT / 2
        if tb >= B_END:
            break
        n = B_BASS[k % 4] + (12 if s in (3, 7) else 0)
        add(music, tb, bass(n, BEAT / 2 * .85, cut=700), .30)
        add(music, tb, marimba(ARP[k % 4][s]), .16, pan=(-.35 if s % 2 else .35))
    t += bar; k += 1

# closing: breakdown pad + marimba, then logo chord
add(music, T['cmpOut'], pad([41, 48, 53, 57, 64], 4.6, bright=2200, a=.4, r=1.2), .26)
for j, n in enumerate([77, 76, 72, 69, 72, 76, 77, 79]):
    add(music, T['cmpOut'] + .3 + j * .5, marimba(n, 1.2), .10, pan=-.3 + (j % 2) * .6)
add(music, T['endIn'], pad([36, 48, 55, 59, 64, 67], 3.5, bright=3000, a=.05, r=2.0), .32)
add(music, T['endIn'], kick(1.0, .6), .45)
for j, n in enumerate([60, 67, 72, 76, 79]):
    add(music, T['endIn'] + j * .07, bell(n, 3.0), .09, pan=-.4 + j * .2)
add(music, T['endIn'], bass(24, 3.0, 200) * np.exp(-tt(3.0) * 1.2), .35)

# ---------- SFX ----------
def s_whoosh(low=False):
    d = .7; x = noise(d); t = tt(d)
    fc = (400 if low else 900) * (6 if not low else 4) ** np.sin(np.pi * t / d)
    y = np.zeros_like(x); z1 = z2 = 0
    # time-varying bandpass via short blocks
    blk = 512
    for i in range(0, len(x), blk):
        f = fc[i]; seg = x[i:i + blk]
        y[i:i + blk] = bp(seg, f * .6, f * 1.6, 1)
    return y * np.sin(np.pi * t / d) ** 2 * 1.2


FX = {
    'key': lambda: bp(noise(.012), 2500, 9000) * np.exp(-tt(.012) * 300) * (0.8 + .4 * rng.random()),
    'tap': lambda: np.pad(bp(noise(.008), 2000, 8000) * np.exp(-tt(.008) * 400), (0, int(.05 * SR))) + np.sin(2 * np.pi * 190 * tt(.058)) * np.exp(-tt(.058) * 60) * .5,
    'whoosh': lambda: s_whoosh(),
    'whooshLow': lambda: s_whoosh(True),
    'rise': lambda: s_whoosh()[: int(.5 * SR)],
    'pop': lambda: sweep_sine(900, 450, .09) * np.exp(-tt(.09) * 30),
    'bubble': lambda: sweep_sine(500, 1300, .09) * np.exp(-tt(.09) * 25) * .8,
    'drop': lambda: sweep_sine(1400, 380, .18) * np.exp(-tt(.18) * 18),
    'swish': lambda: hp(noise(.28), 1500) * np.sin(np.pi * tt(.28) / .28) ** 3 * .5,
    'swipe': lambda: bp(noise(.16), 1200, 6000) * np.sin(np.pi * tt(.16) / .16) ** 2 * .5,
    'thud': lambda: (np.sin(2 * np.pi * 85 * tt(.3)) * np.exp(-tt(.3) * 14) + lp(noise(.3), 600) * np.exp(-tt(.3) * 30) * .3),
    'error': lambda: np.concatenate([lp(signal.square(2 * np.pi * 220 * tt(.12)), 1500) * env_adsr(int(.12 * SR), .005, .02, .8, .03),
                                     np.zeros(int(.04 * SR)),
                                     lp(signal.square(2 * np.pi * 185 * tt(.2)), 1500) * env_adsr(int(.2 * SR), .005, .02, .8, .08)]) * .35,
    'send': lambda: sweep_sine(480, 1150, .14) * np.sin(np.pi * tt(.14) / .14) * .7,
    'ff': lambda: np.zeros(10),
    'buzz': lambda: lp(signal.square(2 * np.pi * 110 * tt(.16)), 900) * env_adsr(int(.16 * SR), .005, .03, .7, .06) * .35,
    'fall': lambda: sweep_sine(260, 42, 1.4) * np.exp(-tt(1.4) * 2.2) * .9 + lp(noise(1.4), 300) * np.exp(-tt(1.4) * 3) * .3,
    'rewind': lambda: None,
    'iris': lambda: hp(noise(1.0), 3000) * np.linspace(0, 1, int(SR)) ** 2 * .35,
    'panel': lambda: hp(noise(.35), 2000) * np.sin(np.pi * tt(.35) / .35) ** 2 * .45,
    'shimmer': lambda: arp([84, 88, 91], .07, 1.2, 1.5) * .35,
    'ding': lambda: (np.pad(bell(88, 1.0), (0, int(.1 * SR))) + np.pad(bell(95, 1.0), (int(.1 * SR), 0))) * .45,
    'scroll': lambda: bp(noise(.4), 800, 3000) * np.sin(np.pi * tt(.4) / .4) ** 2 * .25,
    'success': lambda: arp([72, 76, 79, 84], .09, 1.4, 1.8) * .45,
    'slam': lambda: kick(1.2, .7) + lp(noise(.7), 2500) * np.exp(-tt(.7) * 10) * .4,
    'tickRun': lambda: None,
    'logo': lambda: np.zeros(10),
}


def arp(notes, gap, d, total):
    out = np.zeros(int(total * SR))
    for j, n in enumerate(notes):
        x = bell(n, d); i = int(j * gap * SR); out[i:i + len(x)] += x[: len(out) - i]
    return out


def rewind_sfx():
    d = 1.5; t = tt(d)
    lfo = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * (6 + 14 * t / d) * t))
    x = bp(noise(d), 600, 5000) * lfo * .5
    x += sweep_sine(900, 200, d) * .15 * lfo
    return x * env_adsr(len(t), .05, .1, 1, .3)


def tickrun():
    out = np.zeros(int(1.7 * SR))
    for i in range(19):
        tm = 1.6 * (1 - (1 - i / 19) ** 2)
        x = tick(2400 + i * 40, .02)
        j = int(tm * SR); out[j:j + len(x)] += x[: len(out) - j]
    return out * .8


events = json.load(open(sys.argv[1] if len(sys.argv) > 1 else 'out/sfx.json'))
for ev in events:
    k, t0, g = ev['k'], ev['t'], ev.get('g', 1)
    if k == 'rewind':
        x = rewind_sfx()
    elif k == 'tickRun':
        x = tickrun()
    else:
        x = FX[k]()
    x = np.asarray(x, dtype=float)
    pan = {'swipe': .3, 'bubble': (rng.random() - .5) * .8, 'key': (rng.random() - .5) * .2}.get(k, 0)
    add(fx, t0, x, .5 * g, pan)

# ---------- reverb ----------
def reverb(x, dur=2.2, wet=.22, damp=4000):
    ir_l = lp(noise(dur), damp) * np.exp(-tt(dur) * 3.2)
    ir_r = lp(noise(dur), damp) * np.exp(-tt(dur) * 3.2)
    ir_l /= np.sqrt(np.sum(ir_l ** 2)); ir_r /= np.sqrt(np.sum(ir_r ** 2))
    wl = signal.fftconvolve(x[:, 0], ir_l)[:len(x)]
    wr = signal.fftconvolve(x[:, 1], ir_r)[:len(x)]
    return x + wet * np.stack([wl, wr], 1)


music = reverb(music, 2.6, .30)
fx = reverb(fx, 1.4, .16, 6000)

# duck music a touch under dense SFX moments & overall mix
mix = music * .85 + fx * 1.0
# fades
fi = int(.3 * SR); mix[:fi] *= np.linspace(0, 1, fi)[:, None]
fo = int(1.2 * SR); mix[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5
peak = np.max(np.abs(mix)); mix = mix / peak * .89
sf.write(sys.argv[2] if len(sys.argv) > 2 else 'out/mix.wav', mix.astype(np.float32), SR)
print('peak', peak, 'written')
