import numpy as np, subprocess, json, os
SR=44100
rng=np.random.default_rng(7)
def strike(dur=22.0, amp=1.0, bright=1.0, f0=104.0):
    t=np.arange(int(SR*dur))/SR
    # (ratio, rel amplitude, T60 seconds, beat Hz)
    parts=[(1.000,1.00,19,0.55),(1.505,0.22,9,0.9),(2.000,0.62,13,0.35),(2.48,0.20,7,1.3),(3.01,0.34,8,0.7),
           (3.94,0.16*bright,5,1.1),(4.53,0.12*bright,4.2,0.8),(5.36,0.09*bright,3.2,1.6),(6.71,0.06*bright,2.4,2.1),(8.2,0.035*bright,1.7,2.7)]
    y=np.zeros_like(t)
    for r,a,t60,beat in parts:
        f=f0*r
        glide=1+0.006*np.exp(-t/0.35)*(1 if r>2 else 0.3)
        ph=2*np.pi*np.cumsum(f*glide)/SR
        env=np.exp(-6.9*t/t60)
        wob=1+0.18*np.sin(2*np.pi*beat*t+rng.uniform(0,6))
        y+=a*env*wob*(np.sin(ph+rng.uniform(0,6))+0.5*np.sin(ph*(1+0.0035)+rng.uniform(0,6)))
    # bloom: upper partials swell slightly after the hit, like a big hanging gong
    bloom=(1-np.exp(-t/0.06))
    y*=bloom
    # mallet: soft, low thump
    n=rng.standard_normal(len(t))*np.exp(-t/0.045)
    k=np.exp(-np.arange(200)/40.0); thump=np.convolve(n,k/k.sum(),'same')
    y+=0.9*thump
    y*=np.minimum(1,(dur-t)/1.5).clip(0,1)    # final fade
    return amp*y
def norm(y,peak=0.85): return y/np.max(np.abs(y))*peak
def write(name,y):
    y16=(np.clip(y,-1,1)*32767).astype('<i2')
    import wave
    w=wave.open(name+'.wav','wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(y16.tobytes()); w.close()
one=norm(strike(22),0.85)
soft=norm(strike(16,bright=0.55),0.5)
three=np.zeros(int(SR*36)); 
for i,(off,a) in enumerate([(0,1.0),(7.5,0.9),(15,0.8)]):
    s=strike(36-off-0.01, amp=a); three[int(off*SR):int(off*SR)+len(s)]+=s
three=norm(three,0.85)
write('gong1',one); write('gong-soft',soft); write('gong3',three)
write('sil10',np.zeros(SR*10)); write('sil1',np.zeros(SR*1))
