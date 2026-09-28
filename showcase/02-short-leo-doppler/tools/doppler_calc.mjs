const GM=3.986004418e14, RE=6371.0e3, C=299792458;
const d2r=Math.PI/180;
for (const H of [500e3, 550e3]) {
  const r=RE+H, v=Math.sqrt(GM/r), T=2*Math.PI*Math.sqrt(r**3/GM);
  console.log(`h=${H/1e3} km  v=${(v/1e3).toFixed(3)} km/s  period=${(T/60).toFixed(1)} min`);
  for (const mask of [0,10,25]) {
    const e=mask*d2r;
    const lam=Math.acos(RE*Math.cos(e)/r)-e;            // central half-angle of pass
    const pass=2*lam/(2*Math.PI)*T;                     // overhead pass duration (non-rotating Earth)
    const vr=v*(RE/r)*Math.cos(e);                      // max range-rate at mask elevation
    const fd=f=>vr/C*f;
    console.log(`  mask ${mask}°: pass ${(pass/60).toFixed(1)} min, max v_r ${(vr/1e3).toFixed(2)} km/s, fd@2GHz ${(fd(2e9)/1e3).toFixed(1)} kHz, fd@20GHz ${(fd(20e9)/1e3).toFixed(0)} kHz`);
  }
  console.log(`  upper bound (v_r=v): 2GHz ${(v/C*2e9/1e3).toFixed(1)} kHz, 20GHz ${(v/C*20e9/1e3).toFixed(0)} kHz`);
  const rate = v*v*RE/(r*H); // d v_r/dt at zenith (m/s^2)
  console.log(`  max Doppler rate at zenith: 2GHz ${(rate/C*2e9).toFixed(0)} Hz/s, 20GHz ${(rate/C*20e9/1e3).toFixed(1)} kHz/s`);
}
console.log('Earth rotation speed at equator', (2*Math.PI*6378.137e3/86164.1/1e3).toFixed(3),'km/s');
console.log('fractional shift v_r/c', (7.0e3/C).toExponential(2));
