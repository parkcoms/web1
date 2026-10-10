import numpy as np, wave
sr=44100;T=88.25;n=int(sr*T)+sr;out=np.zeros(n)
bpm=112;beat=60/bpm;bar=4*beat
rng=np.random.default_rng(7)
f=lambda m:440*2**((m-69)/12)
def add(sig,t0,g=1.0):
    s=int(t0*sr);e=min(n,s+len(sig))
    if s<n: out[s:e]+=g*sig[:e-s]
def kick():
    L=int(.25*sr);t=np.arange(L)/sr;fr=50+90*np.exp(-t*30)
    return np.sin(2*np.pi*np.cumsum(fr)/sr)*np.exp(-t*14)
def hat(open_=False):
    L=int((.12 if open_ else .04)*sr);x=rng.standard_normal(L);x=np.diff(np.concatenate([[0],x]))
    return x*np.exp(-np.arange(L)/sr*(25 if open_ else 90))*.35
def clap():
    L=int(.18*sr);t=np.arange(L)/sr;x=rng.standard_normal(L);x=np.convolve(x,[1,-.6],'same')
    env=np.exp(-t*22)*(1+.6*((t%0.012)<.006)*(t<.03));return x*env*.5
def pluck(m,dur=.45,bright=1.0):
    L=int(dur*sr);t=np.arange(L)/sr;y=np.zeros(L)
    for h in range(1,8):
        y+=np.sin(2*np.pi*f(m)*h*t)/h**1.3*np.exp(-t*(5+h*2.5/bright))
    return y*np.minimum(1,t*400)
def bass(m,dur):
    L=int(dur*sr);t=np.arange(L)/sr;ph=2*np.pi*f(m)*t
    y=np.sin(ph)+.3*np.sin(2*ph)+.12*np.sin(3*ph)
    return y*np.minimum(1,t*200)*np.exp(-t*3)
def bell(m,dur=.6):
    L=int(dur*sr);t=np.arange(L)/sr
    return (np.sin(2*np.pi*f(m)*t)+.25*np.sin(2*np.pi*f(m)*3.01*t)*np.exp(-t*8))*np.exp(-t*5)*np.minimum(1,t*500)
prog=[(48,[60,64,67]),(43,[59,62,67]),(45,[60,64,69]),(41,[60,65,69])]   # C G Am F
mel=[76,79,81,79, 74,79,78,79, 76,72,74,76, 77,76,74,72]
nb=int(T/bar)+1
for b in range(nb):
    t0=b*bar;root,ch=prog[b%4];sec=b//4   # sections every 4 bars
    intro=b<2;outro=t0>T-bar*1.5
    for k in range(4):
        if not intro or k in (0,2): add(kick(),t0+k*beat,.9)
        if k in (1,3) and not intro: add(clap(),t0+k*beat,.55)
    for e in range(8):
        add(hat(open_=(e%2==1 and e==7)),t0+e*beat/2+beat/4*0,.5 if e%2 else .25)
    # bouncy bass 8ths: root, root, octave, root
    for e in range(8):
        mm=root+(12 if e in (2,6) else 0)
        add(bass(mm,beat/2*.9),t0+e*beat/2,.55)
    # offbeat chord stabs (syncopated)
    for pos in (0.5,1.5,2.0,2.5,3.5):
        for m in ch: add(pluck(m,.35),t0+pos*beat,.22)
    # bell melody from bar 4 onward, every other section stronger
    if b>=2:
        for i in range(4):
            add(bell(mel[(b%4)*4+i]),t0+i*beat+(beat/2 if i==3 else 0),.18 if sec%2 else .12)
out=out[:int(sr*T)]
t=np.arange(len(out))/sr
out*=np.minimum(1,t/0.6)*np.clip((T-t)/2.0,0,1)
out=np.tanh(out*1.2)
out=out/np.abs(out).max()*.8
w=wave.open('bgm2.wav','wb');w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((out*32767).astype(np.int16).tobytes());w.close()
print('ok',len(out)/sr)
