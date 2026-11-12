"""13: how well OrbitStream._roots recovers the turning point that IS the start (v_r = 0, y = 1 exactly) near the
circular speed, against 40-digit roots; and the resulting kind (see V4-1, script 11)."""
import math, numpy as np
from lfphys.core.gravity import orbit_stream as osm
import mpmath as mp
mp.mp.dps=40
for r0,k in ((6.2,1.0001),(6.01,1.000001),(7.0,1.000001),(20.0,1.0000001),(6.2,1.001),(8.0,1.0001)):
    vp=k*math.sqrt(1/(r0-2)); st=osm.OrbitStream(r0,0.0,vp)
    c=[2*st.us,-1.0,2*st.A,st.B]
    print(r0,k,"info",st.info,"Y'",st.Y[1],"ypp0",st.A-1+3*st.us)
    print("   np.roots",np.roots(c),"_roots",st._roots())
    R0,V=mp.mpf(r0),mp.mpf(vp); g2=1/(1-V*V); EM1=g2*(V*V-2/R0); L=mp.sqrt(g2)*V*R0; us=1/R0
    ys=mp.polyroots([2*us,-1,1/(L**2*us)*2,EM1/(L**2*us**2)],maxsteps=400,extraprec=400)
    print("   mp roots", [mp.nstr(y,15) for y in ys], " r:", [mp.nstr(r0/mp.re(y),12) for y in ys])
