// Fits the sung-vowel table (VOWEL_LDA in page/index.html): LDA on the note's harmonic envelope with its tilt removed (so a mic's slope cannot move it) plus f0.
// Input: the note list from check/vowel-dump.mjs. Reports leave-one-singer-out accuracy (± 1.96 SE over singers), 'sure' margins and the table.
// Usage: node check/vowel-fit.mjs notes.json
import {readFileSync} from 'fs';
const dump=process.argv[2];const N=JSON.parse(readFileSync(dump)).filter(x=>x.f0<600&&x.env.every(Number.isFinite));
const who=[...new Set(N.map(x=>x.who))],V=[...'aeiou'],L=Math.log;
const fx={env:x=>x.env,'env+F':x=>[...x.env,20*L(x.F1),20*L(x.F2)],'env+F+f0':x=>[...x.env,20*L(x.F1),20*L(x.F2),20*L(x.f0)],F:x=>[20*L(x.F1),20*L(x.F2)]};
function solve(A,b){const n=A.length,M=A.map((r,i)=>[...r,b[i]]);for(let i=0;i<n;i++){let p=i;for(let r=i;r<n;r++)if(Math.abs(M[r][i])>Math.abs(M[p][i]))p=r;[M[i],M[p]]=[M[p],M[i]];for(let r=0;r<n;r++)if(r!==i){const f=M[r][i]/M[i][i];for(let c=i;c<=n;c++)M[r][c]-=f*M[i][c];}}return M.map((r,i)=>r[n]/r[i]);}
function fit(tr,f,ridge){const d=f(tr[0]).length,mu={},W=Array.from({length:d},()=>Array(d).fill(0));for(const v of V){const a=tr.filter(x=>x.t===v).map(f);mu[v]=Array.from({length:d},(_,j)=>a.reduce((s,y)=>s+y[j],0)/a.length);for(const y of a){for(let i=0;i<d;i++)for(let j=0;j<d;j++)W[i][j]+=(y[i]-mu[v][i])*(y[j]-mu[v][j])/tr.length;}}
 const tr_=W.reduce((s,r,i)=>s+r[i],0)/d;for(let i=0;i<d;i++)W[i][i]+=ridge*tr_;const w={};for(const v of V)w[v]=solve(W,mu[v]);return{mu,w};}
const cls=(m,y)=>V.map(v=>[m.w[v].reduce((s,c,j)=>s+c*(y[j]-m.mu[v][j]/2),0),v]).sort((a,b)=>b[0]-a[0]);

const xs=Array.from({length:14},(_,j)=>j-6.5),sxx=xs.reduce((s,x)=>s+x*x,0),det=e=>{const b=e.reduce((s,y,j)=>s+y*xs[j],0)/sxx;return e.map((y,j)=>y-b*xs[j]);};
const f=x=>[...det(x.env),20*L(x.f0)],R=[];
for(const w of who){const m=fit(N.filter(x=>x.who!==w),f,0.03);for(const x of N.filter(x=>x.who===w)){const r=cls(m,f(x));R.push({who:w,t:x.t,f0:x.f0,p:r[0][1],d:r[0][0]-r[1][0]});}}
const pc=a=>{const u=who.map(w=>a.filter(x=>x.who===w)).filter(g=>g.length).map(g=>g.filter(x=>x.p===x.t).length/g.length),me=u.reduce((s,x)=>s+x,0)/u.length,sd=Math.sqrt(u.reduce((s,x)=>s+(x-me)**2,0)/(u.length-1));return `${(100*me).toFixed(1)} ± ${(196*sd/Math.sqrt(u.length)).toFixed(1)}`;};
console.log('left-out singer',pc(R),V.map(v=>v+' '+pc(R.filter(x=>x.t===v))).join(', '));
for(const [lo,hi] of [[0,200],[200,300],[300,400],[400,600]])console.log(lo,hi,R.filter(x=>x.f0>=lo&&x.f0<hi).length,pc(R.filter(x=>x.f0>=lo&&x.f0<hi)));
for(const q of [0.5,1,2,3,5]){const a=R.filter(x=>x.d>=q);console.log('sure',q,pc(a),(100*a.length/R.length).toFixed(0)+'% of notes');}
const m=fit(N,f,0.03),a=V.map(v=>-m.w[v].reduce((s,c,j)=>s+c*m.mu[v][j]/2,0));
console.log('const VOWEL_LDA={'+V.map((v,i)=>`${v}:[${+a[i].toFixed(3)},${m.w[v].map(c=>+c.toFixed(4)).join(',')}]`).join(',')+'};');
