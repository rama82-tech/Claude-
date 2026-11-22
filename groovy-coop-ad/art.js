// Shared drawing kit: palette, patterns and product icons. Draws into the global context `x`.
let x = null;
const T = 120, GAP = 8;
const P = { paper:'#FFF1DC', ink:'#2A1748', pink:'#FF3E8A', teal:'#00B8C4', sun:'#FFC531',
            violet:'#7D4CFF', tang:'#FF7420', mint:'#3DD68C', sky:'#5BCEFA', blush:'#F5A9B8', white:'#FFFFFF' };
const rng = seed => { seed = (seed % 2147483646) + 1; return () => (seed = (seed * 16807) % 2147483647) / 2147483647; };
let R = rng(42);

function rr(px,py,w,h,r){ x.beginPath(); x.roundRect(px,py,w,h,r); }

// ---------- patterns ----------
const PAT = {
  dots(s,c1,c2){ x.fillStyle=c1; x.fillRect(0,0,s,s); x.fillStyle=c2;
    for(let i=0;i<4;i++)for(let j=0;j<4;j++){ x.beginPath(); x.arc(15+i*30+(j%2)*15,15+j*30,6,0,7); x.fill(); } },
  zig(s,c1,c2){ x.fillStyle=c1; x.fillRect(0,0,s,s); x.strokeStyle=c2; x.lineWidth=9; x.lineJoin='miter';
    for(let k=0;k<4;k++){ x.beginPath(); for(let i=0;i<=8;i++) x.lineTo(i*s/8, 18+k*30+(i%2?12:-4)); x.stroke(); } },
  check(s,c1,c2){ x.fillStyle=c1; x.fillRect(0,0,s,s); x.fillStyle=c2; const n=4,d=s/n;
    for(let i=0;i<n;i++)for(let j=0;j<n;j++) if((i+j)%2) x.fillRect(i*d,j*d,d,d); },
  stripes(s,cols,h=s){ const d=h/cols.length; cols.forEach((c,i)=>{ x.fillStyle=c; x.fillRect(0,i*d,s,d+1); }); },
  squiggle(s,c1,c2){ x.fillStyle=c1; x.fillRect(0,0,s,s); x.strokeStyle=c2; x.lineWidth=7; x.lineCap='round';
    for(let k=0;k<3;k++){ x.beginPath(); for(let i=0;i<=40;i++){ const u=i/40; x.lineTo(10+u*(s-20), 25+k*35+Math.sin(u*Math.PI*3+k)*9); } x.stroke(); } },
  terrazzo(s,c1,cs,seed=42){ R=rng(seed); x.fillStyle=c1; x.fillRect(0,0,s,s);
    for(let i=0;i<22;i++){ x.fillStyle=cs[i%cs.length]; x.beginPath(); const cx=R()*s,cy=R()*s,r=3+R()*6;
      for(let k=0;k<5;k++){ const a=k/5*6.28+R(); x.lineTo(cx+Math.cos(a)*r*(0.6+R()*.6), cy+Math.sin(a)*r*(0.6+R()*.6)); } x.fill(); } },
  leopard(s,c1,c2){ x.fillStyle=c1; x.fillRect(0,0,s,s);
    for(let i=0;i<9;i++){ const cx=(i%3)*42+18+(Math.floor(i/3)%2)*16, cy=Math.floor(i/3)*40+20;
      x.strokeStyle=c2; x.lineWidth=6; x.lineCap='round'; x.beginPath(); x.arc(cx,cy,11,0.4+i,3.6+i); x.stroke();
      x.fillStyle='#C97A2B'; x.beginPath(); x.arc(cx,cy,4,0,7); x.fill(); } },
  leopardBig(s,c1,c2){ for(let i=0;i<s/120;i++)for(let j=0;j<s/120;j++){ x.save(); x.translate(i*120,j*120); PAT.leopard(120,c1,c2); x.restore(); } },
  rainbow(s,bg){ x.fillStyle=bg; x.fillRect(0,0,s,s); const cs=[P.violet,P.pink,P.tang,P.sun];
    cs.forEach((c,i)=>{ x.strokeStyle=c; x.lineWidth=12; x.beginPath(); x.arc(s/2,s*0.86,50-i*12,Math.PI,0); x.stroke(); }); },
};

// ---------- icons (drawn centred in an s×s tile) ----------
function ol(){ x.strokeStyle=P.ink; x.lineWidth=5; x.lineJoin='round'; x.lineCap='round'; }
const ICON = {
  tee(s,c){ ol(); x.fillStyle=c; x.beginPath();
    x.moveTo(40,24); x.lineTo(24,34); x.lineTo(14,56); x.lineTo(30,63); x.lineTo(34,54); x.lineTo(34,98); x.lineTo(86,98);
    x.lineTo(86,54); x.lineTo(90,63); x.lineTo(106,56); x.lineTo(96,34); x.lineTo(80,24); x.quadraticCurveTo(60,40,40,24); x.fill(); x.stroke();
    x.fillStyle=P.ink; x.font='18px Bungee'; x.textAlign='center'; x.fillText('ROCK',60,78); },
  sock(s,c){ ol(); x.fillStyle=c; x.beginPath(); x.moveTo(46,16); x.lineTo(76,16); x.lineTo(76,70); x.quadraticCurveTo(78,100,50,102);
    x.lineTo(30,102); x.quadraticCurveTo(18,100,20,88); x.quadraticCurveTo(22,78,36,74); x.lineTo(46,66); x.closePath(); x.fill(); x.stroke();
    x.fillStyle=P.sun; x.fillRect(48,22,26,8); x.fillStyle=P.pink; x.fillRect(48,36,26,8);
    x.fillStyle=P.ink; [[54,56],[66,62],[56,82],[40,88]].forEach(([a,b])=>{x.beginPath();x.arc(a,b,4,0,7);x.fill();}); },
  crystal(s,c){ ol(); x.fillStyle=c; x.beginPath(); x.moveTo(60,12); x.lineTo(84,40); x.lineTo(76,104); x.lineTo(44,104); x.lineTo(36,40); x.closePath(); x.fill(); x.stroke();
    x.beginPath(); x.moveTo(36,40); x.lineTo(84,40); x.moveTo(60,12); x.lineTo(60,104); x.stroke();
    x.fillStyle='rgba(255,255,255,.55)'; x.beginPath(); x.moveTo(60,14); x.lineTo(60,40); x.lineTo(40,40); x.fill(); },
  candle(s,c){ ol(); x.fillStyle=c; rr(40,52,40,52,4); x.fill(); x.stroke();
    x.fillStyle=P.sun; x.beginPath(); x.moveTo(60,14); x.quadraticCurveTo(80,40,60,46); x.quadraticCurveTo(40,40,60,14); x.fill(); x.stroke();
    x.beginPath(); x.moveTo(60,46); x.lineTo(60,52); x.stroke(); },
  vinyl(s,c,spin=0){ x.save(); x.translate(60,60); x.rotate(spin); x.fillStyle=P.ink; x.beginPath(); x.arc(0,0,48,0,7); x.fill();
    x.strokeStyle='rgba(255,255,255,.18)'; x.lineWidth=2; for(let r=22;r<46;r+=6){ x.beginPath(); x.arc(0,0,r,0,7); x.stroke(); }
    x.fillStyle=c; x.beginPath(); x.arc(0,0,18,0,7); x.fill(); x.fillStyle=P.paper; x.fillRect(-2,-14,4,9);
    x.fillStyle=P.ink; x.beginPath(); x.arc(0,0,3,0,7); x.fill(); x.restore(); },
  cassette(s,c){ ol(); x.fillStyle=c; rr(14,32,92,58,6); x.fill(); x.stroke(); x.fillStyle=P.paper; rr(24,42,72,22,3); x.fill(); x.stroke();
    x.fillStyle=P.ink; [44,76].forEach(a=>{x.beginPath();x.arc(a,53,6,0,7);x.fill();}); x.beginPath(); x.moveTo(34,90); x.lineTo(40,74); x.lineTo(80,74); x.lineTo(86,90); x.stroke(); },
  pad(s,c){ ol(); x.fillStyle=c; rr(12,40,96,44,10); x.fill(); x.stroke(); x.fillStyle=P.ink;
    x.fillRect(24,58,24,8); x.fillRect(32,50,8,24); [[82,56],[94,66]].forEach(([a,b])=>{x.fillStyle=P.pink;x.beginPath();x.arc(a,b,6,0,7);x.fill();x.stroke();});
    x.fillStyle=P.ink; x.fillRect(54,66,6,3); x.fillRect(64,66,6,3); },
  heart(s,c){ ol(); x.fillStyle=c; x.beginPath(); x.moveTo(60,100); x.bezierCurveTo(10,66,18,22,60,42); x.bezierCurveTo(102,22,110,66,60,100); x.fill(); x.stroke(); },
  spark(s,c){ x.fillStyle=c; const st=(cx,cy,r)=>{ x.beginPath(); for(let i=0;i<8;i++){ const a=i*Math.PI/4, rad=i%2?r*.28:r; x.lineTo(cx+Math.cos(a)*rad, cy+Math.sin(a)*rad);} x.fill(); };
    st(60,58,40); st(94,26,14); st(28,96,12); },
  hanger(s,c){ ol(); x.lineWidth=6; x.strokeStyle=c; x.beginPath(); x.arc(60,30,10,Math.PI,2.2*Math.PI); x.lineTo(60,46); x.lineTo(14,84); x.lineTo(106,84); x.closePath(); x.stroke(); },
  shades(s,c){ ol(); x.fillStyle=c; x.beginPath(); x.moveTo(14,50); x.lineTo(54,50); x.lineTo(50,74); x.quadraticCurveTo(32,82,18,72); x.closePath(); x.fill(); x.stroke();
    x.beginPath(); x.moveTo(66,50); x.lineTo(106,50); x.lineTo(102,72); x.quadraticCurveTo(88,82,70,74); x.closePath(); x.fill(); x.stroke();
    x.beginPath(); x.moveTo(54,54); x.quadraticCurveTo(60,48,66,54); x.stroke(); },
  bolt(s,c){ ol(); x.fillStyle=c; x.beginPath(); x.moveTo(68,10); x.lineTo(30,66); x.lineTo(56,66); x.lineTo(46,110); x.lineTo(90,48); x.lineTo(64,48); x.closePath(); x.fill(); x.stroke(); },
  hen(s,c){ ol(); // a round little hen: the coop's mascot
    x.fillStyle=P.white; x.beginPath(); x.ellipse(60,70,34,30,0,0,7); x.fill(); x.stroke();
    x.fillStyle=P.pink; x.beginPath(); x.arc(52,34,8,0,7); x.arc(62,30,8,0,7); x.arc(72,35,7,0,7); x.fill();
    x.fillStyle=P.white; x.beginPath(); x.arc(62,50,18,0,7); x.fill(); x.stroke();
    x.fillStyle=P.sun; x.beginPath(); x.moveTo(78,50); x.lineTo(92,55); x.lineTo(78,60); x.fill(); x.stroke();
    x.fillStyle=P.ink; x.beginPath(); x.arc(68,47,3.5,0,7); x.fill();
    x.strokeStyle=P.ink; x.beginPath(); x.arc(52,74,14,0.2,2.4); x.stroke();
    x.fillStyle='#FF7BA9'; x.beginPath(); x.arc(58,58,4,0,7); x.fill(); },
};
