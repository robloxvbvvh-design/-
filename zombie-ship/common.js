// Общая библиотека рисования для серий «Дима и зомби» (canvas 1280×720).
// Серия задаёт WORDS, DISP, PH, DURATION и функцию frame(t).
const W=1280,H=720,PI=Math.PI;
const cv=document.getElementById('c'), ctx=cv.getContext('2d');
const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
const lerp=(a,b,t)=>a+(b-a)*t;
const seg=(t,a,b)=>clamp((t-a)/(b-a));
const ease=x=>x<.5?2*x*x:1-Math.pow(-2*x+2,2)/2;
const easeIn=x=>x*x;
const back=x=>{const c1=1.70158,c3=c1+1;return 1+c3*Math.pow(x-1,3)+c1*Math.pow(x-1,2);};
const hex=c=>[1,3,5].map(i=>parseInt(c.substr(i,2),16));
const mix=(a,b,t)=>{const A=hex(a),B=hex(b);return '#'+A.map((v,i)=>Math.round(lerp(v,B[i],t)).toString(16).padStart(2,'0')).join('');};
const FONT='Inter, DejaVu Sans, sans-serif';

function rr(x,y,w,h,r){ctx.beginPath();ctx.moveTo(x+r,y);ctx.arcTo(x+w,y,x+w,y+h,r);ctx.arcTo(x+w,y+h,x,y+h,r);ctx.arcTo(x,y+h,x,y,r);ctx.arcTo(x,y,x+w,y,r);ctx.closePath();}
function circle(x,y,r,fill,stroke,lw){ctx.beginPath();ctx.arc(x,y,r,0,2*PI);if(fill){ctx.fillStyle=fill;ctx.fill();}if(stroke){ctx.strokeStyle=stroke;ctx.lineWidth=lw||2;ctx.stroke();}}
function poly(pts){ctx.beginPath();ctx.moveTo(pts[0][0],pts[0][1]);for(let i=1;i<pts.length;i++)ctx.lineTo(pts[i][0],pts[i][1]);}
function outlined(text,x,y,size,fill,stroke='#111',lw=8,weight=900){
  ctx.font=`${weight} ${size}px ${FONT}`;ctx.textAlign='center';ctx.textBaseline='middle';
  ctx.lineJoin='round';ctx.strokeStyle=stroke;ctx.lineWidth=lw;ctx.strokeText(text,x,y);ctx.fillStyle=fill;ctx.fillText(text,x,y);
}

// ---------- Персонаж ----------
const DIMA={skin:'#f2c29b',shirt:'#2f6fd6',pants:'#2d3346',hair:'#5a3a1e',shoes:'#1d1d1d'};
const ZOMBIE={skin:'#8fbf6a',shirt:'#6b5b4b',pants:'#3d4a3a',hair:'#2e3b22',shoes:'#2a2a2a',zombie:true};
const CAPTAIN={skin:'#f2c29b',shirt:'#f4f4f4',pants:'#1f2a44',hair:'#b9b9b9',shoes:'#111111',hat:'captain'};

function person(o){
  const d=Object.assign({s:1,f:1,walk:0,phase:0,sit:0,lean:0,armF:null,armB:null,face:'normal',hat:null,rot:0,
    stick:false,stickA:0.25,alpha:1,zombie:false,bob:0,blink:false},o);
  if(d.alpha<=0)return;
  ctx.save();ctx.globalAlpha*=d.alpha;
  ctx.translate(d.x,d.y);ctx.rotate(d.rot);ctx.scale(d.f*d.s,d.s);
  ctx.lineCap='round';ctx.lineJoin='round';
  const hipY=lerp(-100,-58,d.sit)+d.bob;
  const swingOf=side=>Math.sin(d.phase+(side>0?0:PI));
  const neck=[Math.sin(d.lean)*78,hipY-Math.cos(d.lean)*78];
  const sh=[neck[0]-Math.sin(d.lean)*10,neck[1]+Math.cos(d.lean)*10];
  const armDefault=side=>0.55*d.walk*Math.sin(d.phase+(side>0?PI:0))+0.12+d.lean*0.6;

  const arm=(a,side,withStick)=>{
    const e=0.25;
    const el=[sh[0]+Math.sin(a)*36,sh[1]+Math.cos(a)*36];
    const hd=[el[0]+Math.sin(a+e)*34,el[1]+Math.cos(a+e)*34];
    if(withStick){
      const sa=a+e+d.stickA;
      ctx.strokeStyle='#5b3714';ctx.lineWidth=11;
      ctx.beginPath();ctx.moveTo(hd[0]-Math.sin(sa)*18,hd[1]-Math.cos(sa)*18);ctx.lineTo(hd[0]+Math.sin(sa)*105,hd[1]+Math.cos(sa)*105);ctx.stroke();
      ctx.strokeStyle='#8a5a2b';ctx.lineWidth=7;ctx.stroke();
    }
    const shirt=side<0?mix(d.shirt,'#000000',.18):d.shirt, skin=side<0?mix(d.skin,'#000000',.12):d.skin;
    ctx.strokeStyle=skin;ctx.lineWidth=13;ctx.beginPath();ctx.moveTo(el[0],el[1]);ctx.lineTo(hd[0],hd[1]);ctx.stroke();
    ctx.strokeStyle=shirt;ctx.lineWidth=17;ctx.beginPath();ctx.moveTo(sh[0],sh[1]);ctx.lineTo(el[0],el[1]);ctx.stroke();
    circle(hd[0],hd[1],8.5,skin);
  };
  const leg=side=>{
    const sw=d.walk*0.5*swingOf(side);
    const hip=[side*5,hipY];
    let kx=hip[0]+Math.sin(sw)*48,ky=hip[1]+Math.cos(sw)*48;
    const bend=Math.max(0,-swingOf(side))*d.walk*0.6;
    let fx=kx+Math.sin(sw-bend)*50,fy=ky+Math.cos(sw-bend)*50;
    kx=lerp(kx,hip[0]+44,d.sit);ky=lerp(ky,hipY,d.sit);
    fx=lerp(fx,hip[0]+46,d.sit);fy=lerp(fy,0,d.sit);
    ctx.strokeStyle=side<0?mix(d.pants,'#000000',.25):d.pants;ctx.lineWidth=20;
    ctx.beginPath();ctx.moveTo(hip[0],hip[1]);ctx.lineTo(kx,ky);ctx.lineTo(fx,fy);ctx.stroke();
    ctx.fillStyle=d.shoes;rr(fx-9,fy-7,28,13,6);ctx.fill();
  };

  arm(d.armB!=null?d.armB:armDefault(-1),-1,false);
  leg(-1);leg(1);
  // торс
  ctx.strokeStyle=d.shirt;ctx.lineWidth=46;
  ctx.beginPath();ctx.moveTo(0,hipY-10);ctx.lineTo(neck[0],neck[1]+6);ctx.stroke();
  if(d.zombie){ // рваная одежда
    ctx.fillStyle=mix(d.shirt,'#000000',.35);
    circle(-6+neck[0]*.5,hipY-40,6,ctx.fillStyle);circle(10+neck[0]*.4,hipY-22,4,ctx.fillStyle);
    ctx.fillStyle=d.skin;poly([[-14,hipY+10],[-6,hipY-4],[2,hipY+10]]);ctx.fill();
  }
  if(d.hat==='captain'){ // погоны и пуговицы капитана
    ctx.fillStyle='#e0b22e';rr(sh[0]-14,sh[1]-6,28,7,3);ctx.fill();
    for(let i=0;i<3;i++)circle(neck[0]*0.5+8,hipY-22-i*18,3,'#e0b22e');
  }
  // голова
  const hc=[neck[0]+Math.sin(d.lean)*30,neck[1]-Math.cos(d.lean)*30];
  ctx.strokeStyle=d.skin;ctx.lineWidth=15;ctx.beginPath();ctx.moveTo(neck[0],neck[1]+4);ctx.lineTo(hc[0],hc[1]);ctx.stroke();
  ctx.save();ctx.translate(hc[0],hc[1]);ctx.rotate(d.lean*0.4);
  head(d);
  ctx.restore();
  arm(d.armF!=null?d.armF:armDefault(1),1,d.stick);
  ctx.restore();
}

function head(d){
  circle(0,0,32,d.skin,'#1a1a1a',3);
  circle(-20,4,7,mix(d.skin,'#000000',.1),'#1a1a1a',2); // ухо
  if(d.hair){
    ctx.fillStyle=d.hair;ctx.beginPath();ctx.arc(0,-1,34,PI*1.02,PI*1.98);
    if(d.zombie){ctx.lineTo(24,-14);ctx.lineTo(14,-22);ctx.lineTo(4,-12);ctx.lineTo(-8,-22);ctx.lineTo(-20,-10);ctx.lineTo(-33,-4);}
    else {ctx.quadraticCurveTo(20,-30,-4,-18);ctx.quadraticCurveTo(-20,-10,-34,2);}
    ctx.closePath();ctx.fill();
  }
  const f=d.face;
  const eyes=[[6,-4],[22,-4]];
  ctx.lineCap='round';
  if(f==='dead'){
    ctx.strokeStyle='#111';ctx.lineWidth=3;
    for(const [x,y] of eyes){ctx.beginPath();ctx.moveTo(x-5,y-5);ctx.lineTo(x+5,y+5);ctx.moveTo(x+5,y-5);ctx.lineTo(x-5,y+5);ctx.stroke();}
    ctx.beginPath();ctx.moveTo(8,16);ctx.lineTo(24,14);ctx.stroke();
  } else if(f==='zombie'){
    for(const [x,y] of eyes){circle(x,y,7.5,'#f4f1d0','#222',2);}
    circle(8,-3,2.4,'#c00000');circle(23,-6,2.4,'#c00000');
    ctx.fillStyle='#2b0f0f';poly([[4,13],[28,11],[25,22],[8,22]]);ctx.fill();
    ctx.fillStyle='#fff';poly([[8,13],[11,17],[14,13]]);ctx.fill();poly([[18,12.5],[21,17],[24,12]]);ctx.fill();
    ctx.strokeStyle='#4d6b33';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(-14,-14);ctx.lineTo(-4,-22);ctx.stroke();
  } else {
    const big=f==='scared'?8.5:6.5, pr=f==='scared'?2.6:3.4;
    for(const [x,y] of eyes){
      if(d.blink&&f!=='scared'){ctx.strokeStyle='#111';ctx.lineWidth=2.5;ctx.beginPath();ctx.moveTo(x-5,y);ctx.lineTo(x+5,y);ctx.stroke();}
      else {circle(x,y,big,'#fff','#222',1.5);circle(x+2,y,pr,'#111');}
    }
    ctx.strokeStyle='#3a2312';ctx.lineWidth=3;
    if(f==='angry'){ctx.beginPath();ctx.moveTo(0,-17);ctx.lineTo(11,-12);ctx.moveTo(17,-12);ctx.lineTo(28,-17);ctx.stroke();}
    if(f==='scared'){ctx.beginPath();ctx.arc(6,-14,6,PI*1.15,PI*1.85);ctx.stroke();ctx.beginPath();ctx.arc(22,-14,6,PI*1.15,PI*1.85);ctx.stroke();}
    if(f==='scared'){ctx.fillStyle='#4a1a1a';ctx.beginPath();ctx.ellipse(16,17,5.5,7.5,0,0,2*PI);ctx.fill();}
    else if(f==='angry'){ctx.fillStyle='#fff';rr(7,12,19,8,3);ctx.fill();ctx.strokeStyle='#222';ctx.lineWidth=2;ctx.stroke();ctx.beginPath();ctx.moveTo(7,16);ctx.lineTo(26,16);ctx.stroke();}
    else if(f==='happy'){ctx.fillStyle='#4a1a1a';ctx.beginPath();ctx.arc(16,11,10,0.1,PI-0.1);ctx.closePath();ctx.fill();}
    else {ctx.strokeStyle='#4a1a1a';ctx.lineWidth=2.5;ctx.beginPath();ctx.arc(16,10,7,0.3,PI-0.3);ctx.stroke();}
  }
  if(d.hat==='captain')captainHat();
}
function captainHat(){
  ctx.fillStyle='#ffffff';ctx.strokeStyle='#1a1a1a';ctx.lineWidth=2.5;
  ctx.beginPath();ctx.ellipse(2,-34,38,13,0,0,2*PI);ctx.fill();ctx.stroke();
  ctx.fillStyle='#111';rr(-28,-30,58,12,3);ctx.fill();
  ctx.beginPath();ctx.ellipse(22,-18,22,6,0.15,0,PI);ctx.fill();
  circle(2,-26,5,'#e0b22e');
}

// ---------- Эффекты ----------
function bubble(x,y,text,a,size=30){
  if(a<=0)return;ctx.save();ctx.globalAlpha=a;
  ctx.font=`800 ${size}px ${FONT}`;const w=ctx.measureText(text).width+44,h=size*1.9;
  const bx=clamp(x-w/2,12,W-w-12),by=y-h;
  ctx.fillStyle='#fff';ctx.strokeStyle='#111';ctx.lineWidth=4;
  rr(bx,by,w,h,22);ctx.fill();ctx.stroke();
  poly([[x-14,by+h-2],[x+14,by+h-2],[x+2,by+h+24]]);ctx.fill();ctx.stroke();
  ctx.fillRect(x-12,by+h-6,24,6);
  ctx.fillStyle='#111';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(text,bx+w/2,by+h/2+1);
  ctx.restore();
}
function pop(t,t0,dur,text,x,y,color='#ffde3b',size=64,rot=-0.12){
  const u=(t-t0)/dur;if(u<0||u>1)return;
  ctx.save();ctx.globalAlpha=u>0.7?(1-u)/0.3:1;ctx.translate(x,y);ctx.rotate(rot);
  const k=back(Math.min(1,u*4));ctx.scale(k,k);
  outlined(text,0,0,size,color,'#111',10);ctx.restore();
}
function exclaim(t,t0,t1,x,y){
  if(t<t0||t>t1)return;const k=back(seg(t,t0,t0+0.25));
  ctx.save();ctx.translate(x,y);ctx.scale(k,k);outlined('!',0,0,80,'#ff2b2b','#111',10);ctx.restore();
}
function badge(t,n,label,t0){
  const u=seg(t,t0,t0+0.35);if(u<=0)return;const k=back(u);
  ctx.save();ctx.translate(86,86);ctx.scale(k,k);
  circle(0,0,46,'#e53935','#fff',6);outlined(String(n),0,3,56,'#fff','#7a0f0f',6);
  ctx.restore();
  ctx.save();ctx.globalAlpha=u;ctx.textAlign='left';
  ctx.font=`900 40px ${FONT}`;ctx.lineWidth=9;ctx.strokeStyle='#111';ctx.lineJoin='round';ctx.textBaseline='middle';
  ctx.strokeText(label,148,88);ctx.fillStyle='#fff';ctx.fillText(label,148,88);ctx.restore();
}

// ---------- Фоны ----------
function waves(x0,x1,y,t,amp,freq,speed,color,lw){
  ctx.strokeStyle=color;ctx.lineWidth=lw;ctx.beginPath();
  for(let x=x0;x<=x1;x+=6){const yy=y+Math.sin(x*freq+t*speed)*amp;x===x0?ctx.moveTo(x,yy):ctx.lineTo(x,yy);}ctx.stroke();
}
function porthole(cx,cy,r,t,o){
  ctx.save();ctx.beginPath();ctx.arc(cx,cy,r,0,2*PI);ctx.clip();
  const hz=cy+12;
  let g=ctx.createLinearGradient(0,cy-r,0,hz);
  g.addColorStop(0,o.night?'#08142e':'#6fb6f2');g.addColorStop(1,o.night?'#22335c':'#d6efff');
  ctx.fillStyle=g;ctx.fillRect(cx-r,cy-r,2*r,2*r);
  if(o.night){circle(cx-22,cy-30,14,'#f4f1c9');for(let i=0;i<7;i++)circle(cx-50+i*17,cy-48+(i*37)%30,1.4,'#fff');}
  ctx.fillStyle=o.night?'#0d2547':'#1f6fb2';ctx.fillRect(cx-r,hz,2*r,r);
  for(let k=0;k<4;k++)waves(cx-r,cx+r,hz+8+k*14,t,3,0.08,3+k,'rgba(255,255,255,.35)',2);
  if(o.alarm){ctx.fillStyle='rgba(255,30,30,.25)';ctx.fillRect(cx-r,cy-r,2*r,2*r);}
  if(o.zhand>0){ // рука зомби хлопает по стеклу
    const yy=lerp(cy+r+60,cy+8,o.zhand);ctx.fillStyle='#7fae5c';ctx.strokeStyle='#3d5a2a';ctx.lineWidth=3;
    ctx.beginPath();ctx.ellipse(cx,yy,26,30,0,0,2*PI);ctx.fill();ctx.stroke();
    ctx.lineCap='round';
    for(let i=0;i<4;i++){const fx=cx-21+i*14;ctx.strokeStyle='#3d5a2a';ctx.lineWidth=13;ctx.beginPath();ctx.moveTo(fx,yy-12);ctx.lineTo(fx-2+i,yy-44+Math.abs(i-1.5)*5);ctx.stroke();
      ctx.strokeStyle='#7fae5c';ctx.lineWidth=9;ctx.stroke();}
    ctx.fillStyle='#7fae5c';ctx.fillRect(cx-22,yy+10,44,60);
  }
  ctx.fillStyle='rgba(255,255,255,.18)';ctx.beginPath();ctx.ellipse(cx-25,cy-25,14,30,-0.7,0,2*PI);ctx.fill();
  ctx.restore();
  circle(cx,cy,r+8,null,'#c9a24a',18);circle(cx,cy,r,null,'#7d5f22',3);
  for(let i=0;i<10;i++){const a=i/10*2*PI;circle(cx+Math.cos(a)*(r+9),cy+Math.sin(a)*(r+9),3,'#8a6a25');}
}
function door(x,y,w,h,open,shake,t){
  ctx.fillStyle='#3b2414';ctx.fillRect(x-14,y-14,w+28,h+14);
  ctx.fillStyle='#120e0c';ctx.fillRect(x,y,w,h);
  const pw=w*(1-open*0.84),sx=Math.sin(t*90)*shake*5;
  ctx.save();ctx.translate(x+sx,y);
  ctx.fillStyle='#8c5a35';ctx.fillRect(0,0,pw,h);
  ctx.strokeStyle='rgba(0,0,0,.3)';ctx.lineWidth=4;
  if(pw>30){ctx.strokeRect(pw*0.15,20,pw*0.7,h*0.38);ctx.strokeRect(pw*0.15,h*0.5,pw*0.7,h*0.42);circle(pw-18,h*0.48,7,'#e0b22e','#6b4b10',2);
    ctx.fillStyle='#e8d9b0';rr(pw/2-20,h*0.08-14,40,20,4);ctx.fill();ctx.fillStyle='#3b2414';ctx.font=`800 14px ${FONT}`;ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText('№7',pw/2,h*0.08-4);}
  ctx.restore();
}
function bed(){
  ctx.fillStyle='#3e2414';ctx.fillRect(100,410,26,150);ctx.fillRect(120,528,18,32);ctx.fillRect(452,528,18,32);
  ctx.fillStyle='#5a351d';ctx.fillRect(112,505,368,26);
  ctx.fillStyle='#f3efe6';rr(120,486,352,24,8);ctx.fill();
  ctx.fillStyle='#ffffff';rr(134,466,90,28,12);ctx.fill();ctx.strokeStyle='#ccc';ctx.lineWidth=2;ctx.stroke();
  ctx.fillStyle='#c0392b';rr(236,482,240,34,10);ctx.fill();
  ctx.strokeStyle='#e57368';ctx.lineWidth=4;for(let i=0;i<4;i++){ctx.beginPath();ctx.moveTo(266+i*55,484);ctx.lineTo(266+i*55,514);ctx.stroke();}
}
function lamp(x,y,night){
  if(night){const g=ctx.createRadialGradient(x,y+20,10,x,y+20,260);g.addColorStop(0,'rgba(255,214,130,.45)');g.addColorStop(1,'rgba(255,214,130,0)');ctx.fillStyle=g;ctx.fillRect(x-260,y-240,520,520);}
  ctx.fillStyle='#6b4b10';ctx.fillRect(x-4,y-30,8,30);
  ctx.fillStyle='#f3d27a';poly([[x-26,y+26],[x+26,y+26],[x+14,y-4],[x-14,y-4]]);ctx.fill();
  ctx.strokeStyle='#a5832b';ctx.lineWidth=2;ctx.stroke();
}
function clock(x,y,r,t){
  circle(x,y,r+6,'#5a351d');circle(x,y,r,'#fbf6e8','#222',2);
  for(let i=0;i<12;i++){const a=i/12*2*PI;ctx.strokeStyle='#222';ctx.lineWidth=i%3?2:4;ctx.beginPath();ctx.moveTo(x+Math.sin(a)*r*.78,y-Math.cos(a)*r*.78);ctx.lineTo(x+Math.sin(a)*r*.92,y-Math.cos(a)*r*.92);ctx.stroke();}
  const m=t*9,h=t*0.75;ctx.lineCap='round';
  ctx.strokeStyle='#111';ctx.lineWidth=5;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x+Math.sin(h)*r*.5,y-Math.cos(h)*r*.5);ctx.stroke();
  ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x+Math.sin(m)*r*.78,y-Math.cos(m)*r*.78);ctx.stroke();
  circle(x,y,4,'#c0392b');
}
function picture(x,y){
  ctx.fillStyle='#5a351d';ctx.fillRect(x-48,y-38,96,76);ctx.fillStyle='#bfe3f5';ctx.fillRect(x-38,y-28,76,56);
  ctx.fillStyle='#1f6fb2';ctx.fillRect(x-38,y+8,76,20);
  ctx.fillStyle='#fff';poly([[x-14,y+8],[x+20,y+8],[x+12,y+16],[x-8,y+16]]);ctx.fill();ctx.fillRect(x+2,y-16,3,24);
  ctx.fillStyle='#e53935';poly([[x+5,y-16],[x+18,y-10],[x+5,y-5]]);ctx.fill();
}
function sign(k){
  if(k<=0)return;const y=lerp(-80,262,back(k));
  ctx.save();ctx.strokeStyle='#3e2414';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(220,y-36);ctx.lineTo(300,y-70);ctx.lineTo(380,y-36);ctx.stroke();
  ctx.fillStyle='#e8c78f';rr(160,y-38,280,62,10);ctx.fill();ctx.strokeStyle='#5a351d';ctx.lineWidth=5;ctx.stroke();
  ctx.fillStyle='#5a351d';ctx.font=`900 30px ${FONT}`;ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText('КОМНАТА ДИМЫ',300,y-6);
  circle(430,y-36,20,'#2e9d4a','#fff',4);ctx.strokeStyle='#fff';ctx.lineWidth=5;ctx.beginPath();ctx.moveTo(421,y-36);ctx.lineTo(428,y-28);ctx.lineTo(440,y-44);ctx.stroke();
  ctx.restore();
}
function cabin(t,o={}){
  const night=!!o.night;
  let g=ctx.createLinearGradient(0,0,0,560);g.addColorStop(0,night?'#4a3424':'#b07a52');g.addColorStop(1,night?'#2e2016':'#7d5134');
  ctx.fillStyle=g;ctx.fillRect(0,0,W,560);
  ctx.strokeStyle='rgba(0,0,0,.18)';ctx.lineWidth=3;for(let x=45;x<W;x+=90){ctx.beginPath();ctx.moveTo(x,26);ctx.lineTo(x,552);ctx.stroke();}
  ctx.fillStyle='rgba(0,0,0,.28)';ctx.fillRect(0,0,W,26);
  g=ctx.createLinearGradient(0,560,0,H);g.addColorStop(0,night?'#3a2616':'#6b4428');g.addColorStop(1,night?'#22160c':'#4a2e1a');
  ctx.fillStyle=g;ctx.fillRect(0,560,W,H-560);
  ctx.strokeStyle='rgba(0,0,0,.2)';ctx.lineWidth=2;for(let i=-10;i<=10;i++){ctx.beginPath();ctx.moveTo(640+i*90,560);ctx.lineTo(640+i*90*1.7,H);ctx.stroke();}
  ctx.fillStyle='#3e2414';ctx.fillRect(0,550,W,12);
  porthole(820,250,72,t,{night,alarm:o.alarm,zhand:o.zhand||0});
  if(o.clock)clock(520,150,44,t);else picture(520,160);
  lamp(660,120,night);
  door(1060,300,140,260,o.doorOpen||0,o.doorShake||0,t);
  if(o.barricade){
    ctx.fillStyle='#8a6136';ctx.fillRect(1062,470,136,90);ctx.strokeStyle='#5a3a1e';ctx.lineWidth=5;ctx.strokeRect(1062,470,136,90);
    ctx.beginPath();ctx.moveTo(1062,470);ctx.lineTo(1198,560);ctx.moveTo(1198,470);ctx.lineTo(1062,560);ctx.stroke();
    ctx.fillStyle='#9c7142';ctx.fillRect(1090,410,84,60);ctx.strokeRect(1090,410,84,60);
  }
  bed();
  sign(o.sign||0);
  if(night){ctx.fillStyle='rgba(10,15,40,.35)';ctx.fillRect(0,0,W,H);}
  if(o.alarm){
    const p=0.5+0.5*Math.sin(t*12);
    ctx.fillStyle=`rgba(255,0,0,${0.10+0.18*p})`;ctx.fillRect(0,0,W,H);
    circle(640,26,22,p>0.5?'#ff3030':'#7a0000','#222',3);
    const gg=ctx.createRadialGradient(640,26,5,640,26,200);gg.addColorStop(0,`rgba(255,40,40,${0.5*p})`);gg.addColorStop(1,'rgba(255,0,0,0)');ctx.fillStyle=gg;ctx.fillRect(440,0,400,230);
  }
}
function deck(t){
  let g=ctx.createLinearGradient(0,0,0,370);g.addColorStop(0,'#2b1d4d');g.addColorStop(.6,'#a8456b');g.addColorStop(1,'#f39a5c');
  ctx.fillStyle=g;ctx.fillRect(0,0,W,370);
  circle(300,360,62,'#ffd27a');
  ctx.fillStyle='rgba(60,30,80,.6)';for(let i=0;i<4;i++){const cx=((i*380+t*14)%1600)-160;ctx.beginPath();ctx.ellipse(cx,80+i*45,110,22,0,0,2*PI);ctx.fill();}
  ctx.fillStyle='#1b3f73';ctx.fillRect(0,360,W,125);
  for(let k=0;k<5;k++)waves(0,W,372+k*22,t,3,0.03,2+k*.5,'rgba(255,255,255,.22)',2);
  ctx.fillStyle='#24203a';poly([[960,362],[1010,340],[1090,340],[1110,362]]);ctx.fill();ctx.fillRect(1030,320,14,22);
  ctx.fillStyle='rgba(80,80,90,.5)';circle(1037+Math.sin(t)*4,306,9,'rgba(80,80,90,.5)');circle(1030,290,12,'rgba(80,80,90,.4)');
  // палуба
  g=ctx.createLinearGradient(0,482,0,H);g.addColorStop(0,'#c69c6d');g.addColorStop(1,'#9b744b');ctx.fillStyle=g;ctx.fillRect(0,482,W,H-482);
  ctx.strokeStyle='rgba(0,0,0,.16)';ctx.lineWidth=2;for(let i=-14;i<=14;i++){ctx.beginPath();ctx.moveTo(640+i*70,482);ctx.lineTo(640+i*70*2.2,H);ctx.stroke();}
  // леера
  ctx.strokeStyle='#eeeeee';ctx.lineWidth=8;ctx.beginPath();ctx.moveTo(0,398);ctx.lineTo(W,398);ctx.stroke();
  ctx.lineWidth=5;ctx.beginPath();ctx.moveTo(0,442);ctx.lineTo(W,442);ctx.stroke();
  ctx.lineWidth=8;for(let x=20;x<W;x+=105){ctx.beginPath();ctx.moveTo(x,398);ctx.lineTo(x,484);ctx.stroke();}
  // спасательный круг
  for(let i=0;i<8;i++){ctx.strokeStyle=i%2?'#ffffff':'#f05a1a';ctx.lineWidth=15;ctx.beginPath();ctx.arc(1110,436,30,i/8*2*PI,(i+1)/8*2*PI);ctx.stroke();}
  // бухта каната
  for(let i=0;i<4;i++){ctx.strokeStyle='#d8c08a';ctx.lineWidth=6;ctx.beginPath();ctx.ellipse(1180,600,46-i*9,14-i*2.5,0,0,2*PI);ctx.stroke();}
}
function crate(x,y,w,h){
  ctx.fillStyle='#8a6136';ctx.fillRect(x,y,w,h);ctx.strokeStyle='#5a3a1e';ctx.lineWidth=5;ctx.strokeRect(x,y,w,h);
  ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x+w,y+h);ctx.moveTo(x+w,y);ctx.lineTo(x,y+h);ctx.stroke();
}
function bridge(t){
  ctx.fillStyle='#cfc8b8';ctx.fillRect(0,0,W,560);
  ctx.fillStyle='#b9b1a0';ctx.fillRect(0,0,W,40);
  for(let i=0;i<4;i++){
    const x=90+i*280,y=70,w=250,h=230;
    ctx.save();ctx.beginPath();ctx.rect(x,y,w,h);ctx.clip();
    const g=ctx.createLinearGradient(0,y,0,y+150);g.addColorStop(0,'#4f5e74');g.addColorStop(1,'#a7b3c2');ctx.fillStyle=g;ctx.fillRect(x,y,w,h);
    ctx.fillStyle='#2e4a6b';ctx.fillRect(x,y+150,w,h);
    for(let k=0;k<4;k++)waves(x,x+w,y+162+k*18,t,3,0.05,3+k,'rgba(255,255,255,.3)',2);
    ctx.strokeStyle='rgba(200,220,255,.35)';ctx.lineWidth=1.5;
    for(let k=0;k<10;k++){const rx=x+((k*53+t*240)%w),ry=y+((k*97+t*600)%h);ctx.beginPath();ctx.moveTo(rx,ry);ctx.lineTo(rx-5,ry+16);ctx.stroke();}
    ctx.restore();ctx.strokeStyle='#33363b';ctx.lineWidth=14;ctx.strokeRect(x,y,w,h);
  }
  ctx.fillStyle='#6b7280';ctx.fillRect(0,388,W,16);
  ctx.fillStyle='#4b5563';ctx.fillRect(0,404,W,156);
  const cols=['#ff4d4d','#4dff88','#ffd84d','#4dc3ff'];
  for(let i=0;i<14;i++){const on=Math.sin(t*5+i*1.7)>0;circle(60+i*70,440,9,on?cols[i%4]:'#2b2f36','#111',2);}
  for(let i=0;i<8;i++){ctx.fillStyle='#2b2f36';rr(80+i*120,475,60,30,5);ctx.fill();}
  circle(1150,490,46,'#0d3b1e','#111',4);
  ctx.strokeStyle='#4dff88';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(1150,490);ctx.lineTo(1150+Math.cos(t*3)*44,490+Math.sin(t*3)*44);ctx.stroke();
  circle(1150+Math.cos(1)*24,490+Math.sin(1)*24,4,'#4dff88');
  ctx.fillStyle='#3a3f47';ctx.fillRect(0,560,W,H-560);
  ctx.strokeStyle='rgba(255,255,255,.07)';ctx.lineWidth=2;for(let i=-10;i<=10;i++){ctx.beginPath();ctx.moveTo(640+i*90,560);ctx.lineTo(640+i*150,H);ctx.stroke();}
}
function wheel(cx,cy,r,rot,post=true){
  if(post){ctx.fillStyle='#5b3714';ctx.fillRect(cx-10,cy,20,560-cy);ctx.fillRect(cx-30,550,60,12);}
  ctx.save();ctx.translate(cx,cy);ctx.rotate(rot);ctx.lineCap='round';
  for(let i=0;i<8;i++){const a=i/8*2*PI;ctx.strokeStyle='#6b4119';ctx.lineWidth=10;ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(Math.cos(a)*(r+22),Math.sin(a)*(r+22));ctx.stroke();
    circle(Math.cos(a)*(r+22),Math.sin(a)*(r+22),8,'#8a5a2b');}
  circle(0,0,r,null,'#8a5a2b',13);circle(0,0,r,null,'#5b3714',3);circle(0,0,16,'#8a5a2b','#5b3714',3);circle(0,0,5,'#e0b22e');
  ctx.restore();
}
function ship(x,y,t,hatOnDima){
  const bob=Math.sin(t*2.2)*5,tilt=Math.sin(t*1.6)*0.025;
  ctx.save();ctx.translate(x,y+bob);ctx.rotate(tilt);
  // дым
  for(let i=0;i<5;i++){const u=((t*0.8+i*0.2)%1);circle(125-u*220,-235-u*90,14+u*26,`rgba(90,90,100,${0.55*(1-u)})`);}
  ctx.fillStyle='#c0392b';ctx.fillRect(100,-230,52,170);ctx.fillStyle='#1d1d1d';ctx.fillRect(100,-230,52,24);
  ctx.fillStyle='#ffffff';ctx.fillRect(100,-170,52,14);
  ctx.fillStyle='#f4f4f4';ctx.fillRect(-150,-140,240,82);ctx.strokeStyle='#999';ctx.lineWidth=3;ctx.strokeRect(-150,-140,240,82);
  ctx.fillStyle='#f4f4f4';ctx.fillRect(-100,-215,170,78);ctx.strokeRect(-100,-215,170,78);
  for(let i=0;i<5;i++){circle(-128+i*46,-100,9,'#8fc6ec','#555',2);}
  // окно рубки с Димой
  ctx.save();ctx.beginPath();rr(-80,-205,130,52,6);ctx.clip();
  ctx.fillStyle='#bfe3f5';ctx.fillRect(-80,-205,130,52);
  person(Object.assign({},DIMA,{x:-15,y:-90,s:0.42,f:1,face:'happy',hat:hatOnDima?'captain':null,armF:1.4,armB:1.2}));
  ctx.restore();ctx.strokeStyle='#555';ctx.lineWidth=4;rr(-80,-205,130,52,6);ctx.stroke();
  // флаг
  ctx.strokeStyle='#333';ctx.lineWidth=4;ctx.beginPath();ctx.moveTo(-230,-60);ctx.lineTo(-230,-150);ctx.stroke();
  ctx.fillStyle='#e53935';ctx.beginPath();ctx.moveTo(-230,-150);for(let i=0;i<=10;i++)ctx.lineTo(-230-i*5,-150+Math.sin(t*8+i)*3+(i===10?0:0));ctx.lineTo(-280,-122);for(let i=10;i>=0;i--)ctx.lineTo(-230-i*5,-122+Math.sin(t*8+i)*3);ctx.closePath();ctx.fill();
  // корпус
  ctx.fillStyle='#1d2433';poly([[-270,-60],[280,-60],[230,30],[-240,30]]);ctx.fill();
  ctx.fillStyle='#b22a1f';poly([[-252,-6],[255,-6],[230,30],[-240,30]]);ctx.fill();
  ctx.fillStyle='#ffffff';ctx.fillRect(-262,-62,535,8);
  ctx.fillStyle='#fff';ctx.font=`900 22px ${FONT}`;ctx.textAlign='left';ctx.textBaseline='middle';ctx.fillText('ДИМА',150,-34);
  ctx.restore();
}
function seaScene(t,hat){
  let g=ctx.createLinearGradient(0,0,0,400);g.addColorStop(0,'#6aa8e8');g.addColorStop(.7,'#ffd3a0');g.addColorStop(1,'#ffb26b');
  ctx.fillStyle=g;ctx.fillRect(0,0,W,400);
  const gg=ctx.createRadialGradient(1020,300,20,1020,300,220);gg.addColorStop(0,'rgba(255,240,180,.9)');gg.addColorStop(1,'rgba(255,240,180,0)');ctx.fillStyle=gg;ctx.fillRect(700,60,640,400);
  circle(1020,300,70,'#fff0b0');
  ctx.fillStyle='rgba(255,255,255,.85)';for(let i=0;i<3;i++){const cx=((i*520+t*20)%1700)-200;ctx.beginPath();ctx.ellipse(cx,90+i*50,90,24,0,0,2*PI);ctx.ellipse(cx+50,80+i*50,60,26,0,0,2*PI);ctx.fill();}
  ctx.strokeStyle='#333';ctx.lineWidth=3;ctx.lineCap='round';
  for(let i=0;i<4;i++){const bx=((i*300+t*60)%1500)-100,by=150+i*30+Math.sin(t*3+i)*8,w=Math.sin(t*10+i)*5;ctx.beginPath();ctx.moveTo(bx-14,by-w);ctx.quadraticCurveTo(bx-6,by-8,bx,by);ctx.quadraticCurveTo(bx+6,by-8,bx+14,by-w);ctx.stroke();}
  ctx.fillStyle='#2f6fae';ctx.fillRect(0,392,W,H-392);
  // остров с зомби уплывает назад
  const ix=lerp(170,-260,seg(t,24.5,28));
  ctx.fillStyle='#d9c27a';ctx.beginPath();ctx.ellipse(ix,402,190,34,0,PI,2*PI);ctx.fill();
  ctx.strokeStyle='#6b4119';ctx.lineWidth=8;ctx.beginPath();ctx.moveTo(ix+90,390);ctx.quadraticCurveTo(ix+100,340,ix+86,300);ctx.stroke();
  ctx.fillStyle='#2e8b3e';for(let i=0;i<5;i++){ctx.beginPath();ctx.ellipse(ix+86+Math.cos(i*1.3)*26,300+Math.sin(i*1.3)*8,30,8,i*1.3,0,2*PI);ctx.fill();}
  for(let i=0;i<3;i++){const wave=Math.sin(t*8+i*2)*0.5;person(Object.assign({},ZOMBIE,{x:ix-70+i*55,y:392,s:0.24,f:1,face:'zombie',armF:2.6+wave,armB:2.4-wave}));}
  for(let k=0;k<4;k++)waves(0,W,410+k*20,t,3,0.025,2+k,'rgba(255,255,255,.25)',2);
  const sx=lerp(300,820,seg(t,24.5,28.5));
  ship(sx,500,t,hat);
  // кильватер
  ctx.fillStyle='rgba(255,255,255,.6)';for(let i=0;i<8;i++){const u=((t*1.2+i/8)%1);ctx.beginPath();ctx.ellipse(sx-260-u*260,528+Math.sin(i)*6,30*(1-u)+6,6,0,0,2*PI);ctx.fill();}
  ctx.fillStyle='#24578f';ctx.beginPath();ctx.moveTo(0,H);for(let x=0;x<=W;x+=10)ctx.lineTo(x,525+Math.sin(x*0.02+t*2.5)*8);ctx.lineTo(W,H);ctx.closePath();ctx.fill();
  for(let k=0;k<3;k++)waves(0,W,545+k*24,t,4,0.022,3+k,'rgba(255,255,255,.3)',2.5);
}

const FY=585;
function swingArm(t,t0,n){
  const k=Math.floor((t-t0)/0.5),u=((t-t0)%0.5)/0.5;
  if(t<t0)return 2.7;
  if(k>=n||(k===n-1&&u>=0.25))return 0.8;
  return u<0.25?lerp(2.7,0.8,ease(u/0.25)):lerp(0.8,2.7,ease((u-0.25)/0.75));
}

// ---------- Субтитры (караоке) ----------
function subs(t){
  if(!WORDS.length)return;
  let p=0;for(let i=0;i<PH.length;i++)if(t>=WORDS[PH[i]].s-0.15)p=i;
  const a=PH[p],b=p+1<PH.length?PH[p+1]:WORDS.length;
  ctx.fillStyle='rgba(0,0,0,.6)';ctx.fillRect(0,624,W,96);
  let size=50,gap=24,ws;
  for(;;){ctx.font=`900 ${size}px ${FONT}`;ws=[];let tot=0;for(let i=a;i<b;i++){const w=ctx.measureText(DISP[i]).width;ws.push(w);tot+=w;}
    for(let i=a;i<b-1;i++)if(!DISP[i].endsWith('-'))tot+=gap;if(tot<1200||size<=30){var total=tot;break;}size-=2;}
  let x=W/2-total/2;const y=672;
  ctx.textBaseline='middle';ctx.textAlign='left';ctx.lineJoin='round';
  for(let i=a;i<b;i++){
    const w=WORDS[i],active=t>=w.s&&t<w.e,done=t>=w.e;
    ctx.save();
    const wcx=x+ws[i-a]/2;ctx.translate(wcx,y);
    if(active){const k=1+0.08*Math.sin(Math.min(1,(t-w.s)/0.12)*PI/2);ctx.scale(k,k);}
    ctx.font=`900 ${size}px ${FONT}`;
    ctx.lineWidth=8;ctx.strokeStyle='#000';ctx.strokeText(DISP[i],-ws[i-a]/2,0);
    if(active){ctx.shadowColor='rgba(255,30,30,.9)';ctx.shadowBlur=18;ctx.fillStyle='#ff2424';}
    else ctx.fillStyle=done?'#ffffff':'rgba(255,255,255,.45)';
    ctx.fillText(DISP[i],-ws[i-a]/2,0);
    ctx.restore();
    x+=ws[i-a]+(DISP[i].endsWith('-')?0:gap);
  }
}

