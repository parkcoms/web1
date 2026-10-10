import numpy as np, json, wave, sys
meta=json.load(open('v2meta.json'));sr=44100;T=meta['T'];n=int(sr*T)+sr;out=np.zeros(n)
rng=np.random.default_rng(3)
def lp(x,k):return np.convolve(x,np.ones(k)/k,'same')
def env(L,a,d):t=np.arange(L)/sr;return np.minimum(1,t/a)*np.exp(-t/d)
def tone(f,L,d,a=.002):t=np.arange(L)/sr;return np.sin(2*np.pi*f*t)*env(L,a,d)
def sweep(f0,f1,L,d):t=np.arange(L)/sr;fr=np.linspace(f0,f1,L);return np.sin(2*np.pi*np.cumsum(fr)/sr)*env(L,.003,d)
def noise(L):return rng.standard_normal(L)
def mk(kind,dur):
    if kind=='pop':L=int(.12*sr);return .5*sweep(380,900,L,.04)
    if kind=='tick':L=int(.06*sr);return .35*tone(1800,L,.012)+.2*tone(2700,L,.008)
    if kind=='click':L=int(.05*sr);return .5*lp(noise(L),3)*env(L,.0005,.006)+.3*tone(1200,L,.01)
    if kind=='check':L=int(.25*sr);return .3*tone(1318,L,.06)+.25*np.concatenate([np.zeros(int(.07*sr)),tone(1760,L-int(.07*sr),.08)])
    if kind=='ding':L=int(.9*sr);return .22*(tone(1568,L,.35)+.4*tone(3136,L,.15)+.2*tone(2350,L,.25))
    if kind=='stamp':L=int(.35*sr);t=np.arange(L)/sr;return .9*np.sin(2*np.pi*np.cumsum(60+140*np.exp(-t*40))/sr)*np.exp(-t*12)+.4*lp(noise(L),6)*np.exp(-t*30)
    if kind=='thud':L=int(.6*sr);t=np.arange(L)/sr;return 1.0*np.sin(2*np.pi*np.cumsum(45+90*np.exp(-t*25))/sr)*np.exp(-t*6)+.25*lp(noise(L),20)*np.exp(-t*10)
    if kind in('whoosh','swoosh','rise'):
        L=int({'whoosh':.45,'swoosh':.5,'rise':.35}[kind]*sr);t=np.arange(L)/L;x=noise(L)
        k=8 if kind=='rise' else 14;y=lp(x,k)-lp(x,k*6)   # band-limited noise
        g={'whoosh':.55,'swoosh':.45,'rise':.25}[kind];return g*y*np.sin(np.pi*t)**2*4
    if kind=='type':
        L=int(dur*sr);y=np.zeros(L);t0=0
        while t0<dur-.03:
            s=int(t0*sr);c=mk('click',0)*rng.uniform(.4,.8);e=min(L,s+len(c));y[s:e]+=c[:e-s];t0+=rng.uniform(.06,.11)
        return y*.8
    if kind=='scribble':
        L=int(dur*sr);t=np.arange(L)/sr;x=lp(noise(L),4)-lp(noise(L),30)
        return .35*x*(.5+.5*np.abs(np.sin(t*2*np.pi*7)))*np.minimum(1,(dur-t)*10)
    raise ValueError(kind)
for kind,t0,d in meta['SFX']:
    s=mk(kind,d);i=int(t0*sr)
    if i<0:s=s[-i:];i=0
    e=min(n,i+len(s));out[i:e]+=s[:e-i]
out=out[:int(sr*T)];out=np.tanh(out*1.1)*.8
w=wave.open('sfx.wav','wb');w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((out*32767).astype(np.int16).tobytes());w.close()
print('sfx events',len(meta['SFX']))
