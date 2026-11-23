import fs from 'node:fs/promises';
import path from 'node:path';
import { Presentation, PresentationFile } from '@oai/artifact-tool';
import { PDFDocument } from 'pdf-lib';
import { pathToFileURL } from 'node:url';

const ROOT = process.cwd();
const BASE = path.join(ROOT, 'research/budget_aware_refinement');
const BUILD = path.join(ROOT, '.step9_build');
const OUT = path.join(BASE, 'final_presentation');
const FINAL_PPTX = path.join(OUT, 'DAT_Causal_Decision_Reliability_Final_Presentation.pptx');
const FINAL_PDF = path.join(OUT, 'DAT_Causal_Decision_Reliability_Final_Presentation.pdf');
const SKILL_DIR = 'C:/Users/ehfal/.codex/plugins/cache/openai-primary-runtime/presentations/26.1112.11217/skills/Presentations';
const RUNTIME_PYTHON = 'C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1112-737-0_26.1112.737.0_x64__3k8sg7r9htsxt/dependencies/python/python.exe';

const C = { navy:'#10283F', navy2:'#1B3A56', blue:'#376F9F', teal:'#087F8C', pale:'#EAF2F6', paleTeal:'#E6F4F3', ink:'#162B3A', muted:'#5F7280', line:'#D8E2E8', gray:'#8A9AA5', zero:'#BCC7CD', orange:'#C45A36', red:'#A94336', white:'#FFFFFF', soft:'#F7FAFC' };
const FONT = 'Malgun Gothic';
const W=1280, H=720;
const pres=Presentation.create({slideSize:{width:W,height:H}});

function box(slide,x,y,w,h,fill=C.white,stroke='none',radius=0,name='box'){
  return slide.shapes.add({geometry:radius?'roundRect':'rect',name,position:{left:x,top:y,width:w,height:h},fill,line:{style:'solid',fill:stroke,width:stroke==='none'?0:1},...(radius?{borderRadius:radius}:{})});
}
function text(slide,txt,x,y,w,h,{size=22,color=C.ink,bold=false,align='left',valign='middle',name='text',italic=false}={}){
  const s=slide.shapes.add({geometry:'textbox',name,position:{left:x,top:y,width:w,height:h},fill:'none',line:{style:'solid',fill:'none',width:0}});
  s.text=String(txt); s.text.style={fontSize:size,typeface:FONT,color,bold,italic,alignment:align,verticalAlignment:valign,wrap:'square',autoFit:'shrinkText',insets:0}; return s;
}
function line(slide,x1,y1,x2,y2,color=C.line,width=2){
  if(x1!==x2 && y1!==y2) throw new Error('Only orthogonal editable line segments are supported');
  const horizontal=y1===y2;
  return slide.shapes.add({geometry:'rect',position:{left:Math.min(x1,x2)-(!horizontal?width/2:0),top:Math.min(y1,y2)- (horizontal?width/2:0),width:horizontal?Math.max(Math.abs(x2-x1),0.5):width,height:horizontal?width:Math.max(Math.abs(y2-y1),0.5)},fill:color,line:{style:'solid',fill:'none',width:0}});
}
function circle(slide,cx,cy,r,fill=C.white,stroke=C.teal,sw=2,label='',labelSize=16,labelColor=C.ink){
  const s=slide.shapes.add({geometry:'ellipse',position:{left:cx-r,top:cy-r,width:2*r,height:2*r},fill,line:{style:'solid',fill:stroke,width:sw}});
  if(label) text(slide,label,cx-r+2,cy-r+2,2*r-4,2*r-4,{size:labelSize,color:labelColor,bold:true,align:'center'}); return s;
}
function header(title,kicker='연구 종합',n=null){
  const slide=pres.slides.add(); slide.background.fill=C.white;
  box(slide,0,0,12,H,C.teal);
  text(slide,kicker.toUpperCase(),58,24,760,26,{size:13,color:C.teal,bold:true});
  text(slide,title,58,57,1164,55,{size:32,color:C.navy,bold:true});
  line(slide,58,122,1222,122,C.line,1);
  if(n!==null){ line(slide,58,674,1222,674,C.line,1); text(slide,'DAT 인과 의사결정 신뢰성 연구',58,682,700,20,{size:12,color:C.muted}); text(slide,String(n).padStart(2,'0'),1170,680,50,22,{size:13,color:C.teal,bold:true,align:'right'}); }
  return slide;
}
function note(slide, paragraphs){ slide.speakerNotes.text=paragraphs.join('\n\n'); slide.speakerNotes.setVisible(true); }
function card(slide,x,y,w,h,kpi,label,accent=C.teal,sub=''){
  box(slide,x,y,w,h,C.soft,C.line,14,'kpi-card'); box(slide,x,y,7,h,accent,'none',7);
  text(slide,kpi,x+24,y+15,w-45,46,{size:34,color:accent,bold:true}); text(slide,label,x+24,y+64,w-45,38,{size:17,color:C.ink,bold:true});
  if(sub) text(slide,sub,x+24,y+105,w-45,h-112,{size:14,color:C.muted,valign:'top'});
}
function pill(slide,label,x,y,w,fill=C.pale,color=C.navy){box(slide,x,y,w,32,fill,'none',16);text(slide,label,x+10,y+1,w-20,30,{size:14,color,bold:true,align:'center'});}
function arrow(slide,x1,y,x2,color=C.teal){line(slide,x1,y,x2-12,y,color,3);text(slide,'›',x2-16,y-19,22,38,{size:30,color,bold:true,align:'center'});}
function csvRows(file){return fs.readFile(file,'utf8').then(s=>{const [head,...lines]=s.trim().split(/\r?\n/);const keys=head.split(',');return lines.map(l=>{const v=l.split(',');return Object.fromEntries(keys.map((k,i)=>[k,v[i]]));});});}
function mean(a){return a.reduce((s,x)=>s+x,0)/a.length;}
function fmt(x,d=4){return Number(x).toFixed(d);}

const [s5,s6]=await Promise.all([
  csvRows(path.join(BASE,'step5_development_v1/STEP5_DEVELOPMENT_SCM_SUMMARY.csv')),
  csvRows(path.join(BASE,'step6_confirmation_v1/STEP6_CONFIRMATION_SCM_SUMMARY.csv')),
]);
if(s5.length!==64||s6.length!==200) throw new Error(`Unexpected frozen summary sizes ${s5.length}/${s6.length}`);
const vals=(rows,key)=>rows.map(r=>Number(r[key]));
const D5=vals(s5,'D_i'),D6=vals(s6,'D_i');
const m5=mean(D5),m6=mean(D6);
const sign=(a)=>[a.filter(x=>x>0).length,a.filter(x=>x<0).length,a.filter(x=>x===0).length];
const types=['FN','FP','REV'];
const typeMeans=Object.fromEntries(types.map(t=>[t,[mean(vals(s5,`${t}_D`)),mean(vals(s6,`${t}_D`))]]));
const sens=(a)=>{const z=[...a].sort((x,y)=>y-x);return [mean(z),mean(z.slice(1)),mean(z.slice(2))];};

// 1. Cover
{
 const s=pres.slides.add(); s.background.fill=C.navy;
 box(s,0,0,18,H,C.teal); pill(s,'최종 연구 발표 · Step 4 FROZEN',76,55,286,'#23445E','#D7EEF0');
 text(s,'인과그래프를 더 정확하게\n수정하는 것만으로\n더 좋은 조작 결정을 보장할까?',76,145,790,220,{size:45,color:C.white,bold:true,valign:'top'});
 text(s,'제한 예산의 오류 수정 순서: 개발 코호트와 독립 재현의 기술적 결과',80,395,880,62,{size:23,color:'#C7D6E0'});
 line(s,80,494,1180,494,'#456178',1);
 card(s,80,526,255,116,'64','개발 SCM · Step 5',C.teal);
 card(s,360,526,255,116,'200','독립 재현 SCM · Step 6',C.blue);
 card(s,640,526,260,116,'B = 1','수정 예산 · gamma = 1',C.orange);
 text(s,'합성 선형 SCM · Option B 기술통계 · 실제 제조 개입은 미검증',80,664,1000,24,{size:14,color:'#C7D6E0'});
 note(s,['오늘 발표의 질문은 인과그래프를 정답에 가깝게 고치면 조작 결정도 반드시 좋아지는가입니다. 연구는 제조공정에서 출발했지만, 여기서 실제 공정에 개입하지 않았습니다. Step 5와 Step 6은 각각 64개와 200개의 합성 SCM을 사용한 별도 코호트입니다.','Decision Regret은 정책이 고른 조작 수준의 정답 손실과 미리 정한 후보 격자에서 가장 낮은 정답 손실의 차이입니다. 이번 분석은 사전등록된 Option B에 따라 기술통계와 재현성을 설명하며, 정책의 확인적 우월성을 주장하지 않습니다.','발표 흐름은 구조 수정, 조작 수준 선택, 정답 손실의 연결을 살펴본 뒤 두 코호트의 결과와 예외를 비교하는 순서입니다.']);
}

// 2. causal-to-decision chain
{
 const s=header('인과그래프에서 조작 결정까지는 여러 단계가 있다','문제 정의',2);
 const stages=[['1','그래프','변수와 방향의 구조'],['2','수정 순서','같은 예산으로 후보 선택'],['3','학습·추천','Ridge 모델이 k를 선택'],['4','정답 평가','GT 손실과 regret']];
 const xs=[72,365,658,951];
 stages.forEach((a,i)=>{box(s,xs[i],218,250,190,i===3?C.paleTeal:C.soft,C.line,16);circle(s,xs[i]+38,255,18,i===3?C.teal:C.navy,C.white,0,a[0],16,C.white);text(s,a[1],xs[i]+24,294,205,39,{size:24,color:C.navy,bold:true});text(s,a[2],xs[i]+24,344,205,46,{size:16,color:C.muted,valign:'top'});if(i<3)arrow(s,xs[i]+260,310,xs[i+1]-8);});
 box(s,98,465,1084,98,C.navy,'none',15); text(s,'한 단계의 개선이 다음 단계의 개선을 자동으로 보장하지 않는다.',130,483,1020,58,{size:26,color:C.white,bold:true,align:'center'});
 text(s,'구조 품질 ≠ 추천 ≠ 실제 개입 손실',98,585,1084,30,{size:18,color:C.teal,bold:true,align:'center'});
 note(s,['이 도식은 연구가 구분하는 네 단계입니다. 먼저 그래프가 있고, 그 그래프를 어떤 수정 후보 순서로 고칠지 정합니다. 고친 그래프에서 Ridge 모델이 조작 수준 k를 추천하고, 마지막에 정답 SCM의 analytic evaluator가 실제 후보 손실을 계산합니다.','SCM은 구조방정식 모형입니다. 각 변수의 값이 부모 변수와 계수, 외생 오차에 따라 정해지는 인과 모델입니다.','그래프 점수는 구조의 유사성을 측정하고, 학습 예측은 관측 자료에서 반응을 추정하며, Decision Regret은 선택 행동이 정답 기준에서 얼마나 손실을 남겼는지 측정합니다. 세 측정은 서로 대체할 수 없습니다. 다음 장에서 연구 질문이 어떻게 좁혀졌는지 설명합니다.']);
}

// 3. question evolution
{
 const s=header('초기 질문과 이번 실험은 서로 다른 추정 대상을 가진다','연구 질문',3);
 box(s,70,178,535,355,C.soft,C.line,18); pill(s,'초기 연구 질문',96,202,180,C.pale,C.navy);
 text(s,'어떤 구조 지표가\n다운스트림 결정 품질을\n가장 잘 설명하는가?',98,266,475,130,{size:31,color:C.navy,bold:true,valign:'top'});
 text(s,'구조 지표의 예측·설명력 비교',98,432,450,34,{size:18,color:C.muted});
 box(s,675,178,535,355,C.paleTeal,C.line,18); pill(s,'Step 4–6 실험 질문',701,202,220,'#D4EBE9',C.teal);
 text(s,'같은 B=1 예산에서\n과제 중심 수정 순서가\nID 순서 Global보다\nregret을 줄이는가?',703,263,468,170,{size:29,color:C.navy,bold:true,valign:'top'});
 text(s,'주어진 oracle 오류 후보의 ordering 비교',703,456,450,35,{size:18,color:C.muted});
 arrow(s,615,352,665,C.teal);
 text(s,'연결된 연구 흐름이지만 Step 5–6은 구조 지표 간 우열을 직접 검증하지 않았다.',90,580,1100,46,{size:20,color:C.red,bold:true,align:'center'});
 note(s,['초기의 넓은 질문은 여러 구조 지표가 실제 다운스트림 의사결정 품질을 얼마나 잘 설명하는지 비교하는 것이었습니다. 하지만 초기 데이터에서 안정적인 일반 결론을 얻지 못했고, 이후 Step 4에서 연구 범위를 좁혔습니다.','현재 질문은 오류 후보가 정답 그래프를 기준으로 주어진 뒤, 같은 예산 한 단위를 어떤 순서로 수정하느냐에 관한 것입니다. 그래서 결과는 오류 탐지 능력이나 구조 지표의 우열을 말해주지 않습니다.','두 질문은 그래프에서 의사결정으로 가는 연구 사슬 안에 있지만 같은 추정량은 아닙니다. 이 구분이 발표의 모든 결과 해석에 적용됩니다.']);
}

// 4. matched structure scores
{
 const s=header('같은 구조 점수여도 손실은 달라질 수 있었다','초기 합성 진단',4);
 text(s,'과제 핵심 오류 그래프 vs 주변 오류 그래프',90,168,1100,42,{size:25,color:C.navy,bold:true,align:'center'});
 const x0=150,totalW=980,y=300,h=74; const parts=[['핵심 오류 쪽 손실이 큼',93,C.orange],['작음',4,C.blue],['동률',65,C.gray]];let x=x0;
 for(const [lab,n,col] of parts){const w=totalW*n/162;box(s,x,y,w,h,col,'none',0);if(w>60)text(s,String(n),x,y+12,w,h-24,{size:27,color:C.white,bold:true,align:'center'});x+=w;}
 const legend=[['핵심 오류 쪽 손실이 큼',93,C.orange,150,350],['작음',4,C.blue,535,220],['동률',65,C.gray,830,250]];
 legend.forEach(([lab,n,col,xx,ww])=>{circle(s,xx+6,430,7,col,col,0);text(s,`${lab} · ${n}/162`,xx+22,410,ww,40,{size:16,color:C.ink,bold:true});});
 card(s,142,500,290,120,'162','비교 쌍 · 14개 구조',C.blue);text(s,'같은 구조 점수 조건의 진단',166,599,245,18,{size:12,color:C.muted});
 box(s,470,500,666,110,C.pale,C.line,14);text(s,'존재 증거',497,519,180,32,{size:18,color:C.teal,bold:true});text(s,'점수 동점이 손실 동점을 보장하지는 않는다.',497,552,600,32,{size:23,color:C.navy,bold:true});
 text(s,'162쌍은 독립 공정 162개가 아니며, 모든 점수가 무의미하다는 뜻도 아니다.',115,630,1050,26,{size:15,color:C.muted,align:'center'});
 note(s,['초기 합성 오류 진단에서는 구조 점수가 같은 그래프 쌍을 만들고, 과제 핵심 오류와 주변 오류 중 어느 쪽의 손실이 큰지 비교했습니다. 162쌍 가운데 핵심 오류 쪽 손실이 큰 쌍은 93, 작은 쌍은 4, 동률은 65였습니다.','이 결과의 정확한 의미는 “구조 점수 동점이면 손실도 같아야 한다”는 보장이 없다는 존재 증거입니다. 반복 생성 쌍은 독립적인 실제 공정 표본이 아니므로 독립 SCM 수처럼 읽으면 안 됩니다.','또한 이것은 구조 점수가 쓸모없다는 증거도 아닙니다. 초기 질문에서 어떤 지표가 더 잘 설명하는지를 최종 Step 5–6이 답한 것은 아닙니다.']);
}

// 5. Step 3 pilot
{
 const s=header('파일럿은 정책 차이를 찾기보다 설계를 점검했다','연구 발전',5);
 card(s,90,210,470,180,'114 / 114','Step 3 기본 파일럿 regret = 0',C.blue,'두 기존 구조와 직접 과제에 한정된 탐색 실행');
 card(s,720,210,470,180,'456','사전 계획된 보충 구조 진단 실행',C.teal,'혼합 오류와 경로 과제를 포함해 수정 순서의 가능성을 점검');
 arrow(s,580,298,700,C.teal);
 box(s,134,458,1010,100,C.pale,C.line,14);text(s,'설계 교훈',164,474,170,28,{size:17,color:C.teal,bold:true});text(s,'정책을 구별할 수정 후보·과제·예산이 먼저 필요하다.',164,510,930,34,{size:23,color:C.navy,bold:true});
 text(s,'두 진단은 탐색 자료이며 독립 SCM 표본 또는 우월성 증거가 아니다.',160,595,960,28,{size:17,color:C.red,bold:true,align:'center'});
 note(s,['Step 3의 초기 파일럿은 114회 실행 모두 regret이 0이었고, 추천도 no-edit와 바뀌지 않았습니다. 결과가 정책 성능을 지지해서가 아니라 수정할 오류들이 개입 과제의 실질적 효과에 영향을 주지 않는 조건이었기 때문입니다.','보충 456회는 혼합 오류와 서로 다른 예산·과제를 살펴 구조적 수정 순서가 달라질 수 있는 조건을 찾는 진단이었습니다. 반복 정책 실행은 독립 SCM 수를 늘리지 않습니다.','이 단계의 역할은 성능을 선언하는 것이 아니라, Step 4에서 후보 경쟁과 비교 조건을 더 명확히 고정하는 것이었습니다.']);
}

// 6. frozen contract
{
 const s=header('동결된 비교는 좁고 명시적이다','Step 4 계약',6);
 const rows=[['대상 모집단','P | strict Q-common'],['과제','간접 경로만 있는 Action → Target'],['수정 예산','B = 1 · gamma = 1'],['정책','Task-Focused vs ID-ordered Global'],['오류 유형','FN · FP · REV'],['집계','SCM별 유형 차이의 1/3 동일 가중 평균']];
 rows.forEach((r,i)=>{const x=i%2===0?90:655,y=170+Math.floor(i/2)*116;box(s,x,y,530,88,C.soft,C.line,12);text(s,r[0],x+22,y+13,142,28,{size:15,color:C.teal,bold:true});text(s,r[1],x+22,y+44,484,32,{size:21,color:C.navy,bold:true});});
 box(s,90,531,1100,88,C.navy,'none',14);text(s,'Option B',119,546,160,28,{size:16,color:'#9DD9D7',bold:true});text(s,'기술적 추정 · 확인적 우월성/동등성 주장은 보류',119,578,1015,30,{size:23,color:C.white,bold:true});
 note(s,['이 장은 Step 4에서 고정한 조건입니다. Q-common은 동일 SCM/과제에서 FN, FP, REV 세 오류 유형에 구조적으로 적격한 표본을 뜻합니다. 과제는 직접 간선 없이 길이 2 이상의 간접 경로가 있는 경우로 제한됩니다.','B=1은 한 번의 수정 기회입니다. Global은 그래프 전체의 최적 정책이라는 뜻이 아니라 node ID 순서 기준선입니다. Task-Focused는 같은 후보군 안에서 과제 관련성에 따라 우선순위를 두는 정책입니다.','각 오류 유형의 정책 차이를 같은 SCM 안에서 비교하고 1/3씩 평균해 하나의 SCM 결과를 만듭니다. Step 5와 Step 6은 Option B 기술통계입니다. 평균 방향은 보고하지만 확인적 우월성 검정은 하지 않습니다.']);
}

// 7. cohorts and denominators
{
 const s=header('두 코호트는 분모와 결과를 분리해 보존했다','실험 설계',7);
 const cohorts=[{x:85,name:'Step 5 · 개발',n:64,prop:211,rej:145,fail:2,mean:m5,sg:sign(D5),delta:'+1/−1 32/32'},{x:670,name:'Step 6 · 독립 재현',n:200,prop:675,rej:466,fail:9,mean:m6,sg:sign(D6),delta:'+1/−1 100/100'}];
 cohorts.forEach(q=>{box(s,q.x,170,525,405,C.soft,C.line,16);text(s,q.name,q.x+28,192,465,38,{size:24,color:C.navy,bold:true});text(s,`${q.prop} proposals`,q.x+30,251,175,34,{size:20,color:C.blue,bold:true});text(s,`= ${q.rej} Q 거절 + ${q.fail} 구조/task 실패 + ${q.n} admission`,q.x+30,289,470,32,{size:16,color:C.muted});line(s,q.x+30,337,q.x+495,337,C.line,1);text(s,`${q.n} / ${q.n}`,q.x+30,357,180,45,{size:29,color:C.teal,bold:true});text(s,'세 오류 유형 평가 및 composite 완료',q.x+205,366,280,32,{size:16,color:C.ink,bold:true});text(s,`mean D = ${fmt(q.mean,6)}`,q.x+30,421,440,38,{size:24,color:C.navy,bold:true});text(s,`양 / 음 / 0  ${q.sg.join(' / ')}`,q.x+30,469,440,30,{size:17,color:C.ink});text(s,`delta 배정 ${q.delta}`,q.x+30,515,440,26,{size:15,color:C.muted});});
 text(s,'개발 64와 재현 200을 합쳐 새 확인 표본으로 계산하지 않는다.',135,615,1010,28,{size:18,color:C.red,bold:true,align:'center'});
 note(s,['Step 5 개발 코호트는 211개 proposal 중 145개가 Q-common 구조 거절, 2개가 task/topology 실패였고 64개가 admission됐습니다. Step 6은 675개 중 466개 Q 거절, 9개 구조/task 실패, 200개 admission입니다.','두 코호트 모두 admission 후 세 오류 유형의 평가가 완료됐고 해당 요약에는 후속 결측이 없습니다. 제안 후보 수와 적격 SCM 수는 다른 분모입니다. delta는 코호트 내 admission 순서로 +1과 −1이 균형 배정됐습니다.','Step 5와 Step 6은 개발과 별도 RNG namespace의 재현 코호트입니다. 두 결과를 단순 합쳐 N=264짜리 확인 연구라고 부르지 않습니다.']);
}

// 8. D distributions
{
 const s=header('평균은 양수지만, 대부분의 SCM에서는 동률이었다','결과 분포',8);
 const left=185,right=1120,top=205,bottom=525,ymin=-.17,ymax=.65;const ym=v=>bottom-(v-ymin)*(bottom-top)/(ymax-ymin);
 for(const tick of [-.1,0,.1,.2,.3,.4,.5,.6]){const y=ym(tick);line(s,left,y,right,y,tick===0?C.navy:C.line,tick===0?2:1);text(s,tick.toFixed(1),120,y-11,50,20,{size:13,color:C.muted,align:'right'});}
 text(s,'Dᵢ',78,345,54,25,{size:18,color:C.navy,bold:true,align:'center'});
 for(const [rows,center,color,meanv,label] of [[D5,420,C.blue,m5,'Step 5 · n=64'],[D6,875,C.teal,m6,'Step 6 · n=200']]){
  rows.forEach((v,i)=>{const jitter=(((i*37)%101)/100-.5)*(v===0?225:125);const fill=v===0?C.zero:(v>0?C.orange:C.blue);circle(s,center+jitter,ym(v),4,fill,fill,0);});
  const my=ym(meanv);slideDiamond(s,center,my,C.navy);text(s,label,center-115,548,230,27,{size:17,color:C.navy,bold:true,align:'center'});text(s,`mean ${fmt(meanv,5)}  ·  +/−/0 ${sign(rows).join('/')}`,center-170,579,340,27,{size:14,color:C.muted,align:'center'});
 }
 pill(s,'0 동률',225,158,110,C.pale,C.muted);pill(s,'양수',370,158,95,'#F9E9E3',C.orange);pill(s,'음수',490,158,95,'#E9EFF8',C.blue);pill(s,'평균',610,158,95,C.navy,C.white);
 text(s,'점 하나 = SCM 하나 · x축 jitter는 겹침을 보이기 위한 표시용',185,625,920,25,{size:14,color:C.muted,align:'center'});
 note(s,['각 점은 독립 분석 단위인 SCM 하나입니다. 0은 숨기지 않았습니다. Step 5에서는 64개 중 57개, Step 6에서는 200개 중 167개가 두 정책의 composite 차이 0이었습니다.','양수 D는 Global regret에서 Task-Focused regret을 뺀 값이 양수라는 뜻이므로 그 SCM에서는 Task-Focused regret이 더 낮았습니다. 음수 점은 반대입니다.','평균은 각각 0.01466과 0.02007로 양수지만, 대부분의 SCM이 이긴 것은 아닙니다. 소수의 비영 사례가 평균에 기여하고 일부 음수 사례가 이를 반대 방향으로 움직입니다. 이는 기술적 관찰이며 확인적 우월성 증명이 아닙니다.']);
}

// 9. graph to k to regret
{
 const s=header('그래프 수정이 달라도 조작 수준은 대체로 같았다','결과 메커니즘',9);
 const rows=[['FN',76,14],['FP',109,3],['REV',93,25]], x0=280, scale=3.9;
 const colors=[C.gray,C.teal,C.orange];
 rows.forEach((r,i)=>{const y=225+i*115;text(s,r[0],105,y+24,100,38,{size:23,color:C.navy,bold:true});const vals=[r[1],r[2],r[2]];vals.forEach((v,j)=>{const yy=y+j*28;box(s,x0,yy,Math.max(v*scale,4),18,colors[j],'none');text(s,`${v}/200`,x0+v*scale+9,yy-2,86,21,{size:14,color:C.ink,bold:true});});});
 const legends=[['최종 그래프 다름',C.gray],['선택 k 다름',C.teal],['GT regret 다름',C.orange]];legends.forEach((a,i)=>{box(s,278+i*285,585,13,13,a[1]);text(s,a[0],298+i*285,580,230,26,{size:15,color:C.ink});});
 box(s,100,640,1080,34,C.paleTeal,'none',10);text(s,'같은 과제에서 Action은 200/200 일치 · 이번 자료에서 k 차이와 regret 차이는 같은 14/3/25건',115,642,1050,27,{size:15,color:C.navy,bold:true,align:'center'});
 note(s,['회색 막대는 두 정책의 최종 그래프가 다른 SCM 수, 청록 막대는 선택한 조작 수준 k가 다른 수, 주황 막대는 정답 regret이 다른 수입니다. 유형별 분모는 각각 200 SCM입니다.','FN은 그래프 76건, k 14건, regret 14건이 달랐습니다. FP는 109, 3, 3건, REV는 93, 25, 25건입니다. 여기서 k는 동일 Action 변수에 적용되는 표준화된 조작 수준을 뜻합니다.','같은 Action은 두 정책에 동일한 과제를 준 paired 설계의 결과이지 정책 성능 근거가 아닙니다. 같은 k를 선택하면 같은 action 후보와 GT 손실 격자를 사용하므로 GT 손실과 regret은 같습니다. 반대로 k가 다르다고 손실이 반드시 달라지는 것은 아닙니다. 이번 데이터에서는 k 차이 건과 regret 차이 건수가 일치했습니다.']);
}

// 10. error type heterogeneity
{
 const s=header('오류 유형별 평균 패턴은 코호트 간 달랐다','유형별 결과',10);
 const x0=205,x1=1080,y0=205,groupH=112,scale=18500;line(s,x0,y0-20,x0,540,C.navy,2);
 [0,.01,.02,.03,.04].forEach(v=>{const x=x0+v*scale;line(s,x,y0-20,x,540,v===0?C.navy:C.line,v===0?2:1);text(s,v.toFixed(2),x-25,548,55,22,{size:13,color:C.muted,align:'center'});});
 types.forEach((t,i)=>{const y=y0+i*groupH;text(s,t,105,y+20,75,30,{size:22,color:C.navy,bold:true});const [a,b]=typeMeans[t];for(const [v,yy,col,lab] of [[a,y,C.blue,'개발'],[b,y+34,C.teal,'재현']]){box(s,x0,yy,x1-x0?Math.max(2,v*scale):2,21,col,'none');text(s,`${lab}  ${fmt(v,4)}`,Math.min(x0+v*scale+10,1005),yy-1,165,24,{size:14,color:C.ink,bold:true});}});
 text(s,'mean Dtype = Global regret − Task-Focused regret · 오류 유형은 SCM 내 반복 측정',205,610,900,28,{size:15,color:C.muted,align:'center'});
 note(s,['Step 5에서 평균 차이는 FN 0.0058, FP 0, REV 0.0382였습니다. Step 6에서는 FN 0.0308, FP 0.0022, REV 0.0273입니다. 두 코호트에서 가장 큰 유형 평균은 달랐습니다.','유형별 관측은 동일 SCM 안에 반복해서 측정된 오류 조건입니다. 유형별 평균을 별개의 독립 표본 비교로 읽거나, FN 또는 REV가 일반적으로 더 중요하다고 결론 내리면 안 됩니다.','유형 패턴이 달라진 원인을 원시 근거만으로 확정할 수 없습니다. 따라서 하위그룹 숫자는 기술적 이질성으로 제시하고 새로운 확인적 주장으로 승격하지 않습니다.']);
}

// 11. extreme sensitivity
{
 const s=header('소수의 큰 차이가 평균에 눈에 띄게 기여했다','민감도',11);
 const a=sens(D5),b=sens(D6),xs=[385,650,915],caps=['전체 표본','최댓값 1개 제외','최댓값 2개 제외'];
 const top=205,bottom=525,max=.024,sc=(bottom-top)/max;
 [0,.005,.010,.015,.020].forEach(v=>{const y=bottom-v*sc;line(s,210,y,1100,y,v===0?C.navy:C.line,v===0?2:1);text(s,v.toFixed(3),145,y-10,50,20,{size:13,color:C.muted,align:'right'});});
 for(let i=0;i<3;i++){for(const [v,x,col,dx] of [[a[i],xs[i]-25,C.blue,-25],[b[i],xs[i]+25,C.teal,25]]){const y=bottom-v*sc;box(s,x-21,y,42,bottom-y,col,'none');text(s,fmt(v,4),x-48,y-26,96,23,{size:14,color:C.ink,bold:true,align:'center'});}text(s,caps[i],xs[i]-130,548,260,30,{size:16,color:C.navy,bold:true,align:'center'});}
 pill(s,'Step 5 개발',340,160,145,C.blue,C.white);pill(s,'Step 6 재현',520,160,145,C.teal,C.white);
 box(s,150,605,980,45,C.pale,C.line,12);text(s,'상위 2개 D 합 기여율: Step 5 69.4% · Step 6 29.4% · 전체 평균이 주 결과이며 제외값은 민감도 진단',165,612,950,31,{size:15,color:C.navy,bold:true,align:'center'});
 note(s,['그림은 전체 코호트 평균과 가장 큰 D를 한 개, 두 개씩 제외했을 때의 평균을 나란히 보여줍니다. 모든 막대는 0에서 시작합니다. Step 5는 0.01466에서 상위 두 사례 제외 시 0.00463, Step 6은 0.02007에서 0.01431로 변합니다.','Step 5 상위 두 사례가 차이 합의 69.4%, Step 6 상위 두 사례가 29.4%를 차지했습니다. 민감도는 평균이 일부 사례에 얼마나 영향을 받는지 보여주는 사전 지정 기술 진단입니다. 주 평균을 대체하거나 SCM을 제외하는 근거로 쓰지 않습니다.','평균은 0에 가까운 다수 사례와 큰 양·음 사례의 크기를 합친 통계량입니다. 그래서 평균이 양수이면서 80% 이상이 정확한 동률일 수 있습니다.']);
}

// 12. positive case
{
 const s=header('사례 238: 과제 경로 수정이 더 낮은 regret으로 이어진 경우','설명용 사례 · Task-Focused 유리',12);
 pill(s,'Step 6 · proposal 000238 · Dᵢ = +0.609747',90,153,445,C.paleTeal,C.teal);
 text(s,'과제: V04 → V02 · 간접 경로 두 개',90,205,500,34,{size:20,color:C.navy,bold:true});
 const nodeX=[105,255,405];
 [['V04 · X',295],['V03',295],['V02 · Y',295],['V04 · X',415],['V06',415],['V02 · Y',415]].forEach(([lab,y],i)=>{const col=i%3;box(s,nodeX[col],y,112,48,col===0||col===2?C.paleTeal:C.white,C.teal,12);text(s,lab,nodeX[col]+4,y+4,104,40,{size:16,color:C.navy,bold:true,align:'center'});if(col<2)text(s,'→',nodeX[col]+112,y+8,36,30,{size:22,color:C.teal,bold:true,align:'center'});});
 box(s,590,212,590,152,C.soft,C.line,14);text(s,'Global · ID 순서',615,229,530,30,{size:19,color:C.blue,bold:true});text(s,'V03 → V01 복구 · k=+1',615,267,530,32,{size:18,color:C.ink});text(s,'선택 k의 GT loss 1.469444 · regret 0.914621',615,311,530,28,{size:16,color:C.red,bold:true});
 box(s,590,390,590,152,C.paleTeal,C.line,14);text(s,'Task-Focused',615,407,530,30,{size:19,color:C.teal,bold:true});text(s,'V04 → V03 복구 · 과제 경로 · k=−1',615,445,530,32,{size:18,color:C.ink});text(s,'선택 k의 GT loss 0.554824 · regret 0',615,489,530,28,{size:16,color:C.teal,bold:true});
 text(s,'간선도는 과제 경로 schematic이며 전체 DAG가 아니다 · 선택 사례, 대표성 없음',110,600,1060,28,{size:15,color:C.muted,align:'center'});
 note(s,['Proposal 238은 관찰된 양의 극단 사례를 설명하기 위한 선택 사례이지 대표 표본이 아닙니다. Action V04에서 Target V02로 가는 두 간접 경로가 있었고 그림은 그 경로만 보여줍니다. 전체 DAG가 아닙니다.','FN 유형에서 후보 간선 중 V04→V03은 한 과제 경로에 놓여 있었습니다. B=1에서 Global은 V03→V01 주변 간선을 복구했고 Task-Focused는 V04→V03을 복구했습니다. Global은 k=+1을 선택해 GT loss 1.469444, Task-Focused는 k=−1을 선택해 loss 0.554824로 regret 차이가 0.914621이었습니다.','이 SCM의 FN, FP, REV 차이를 동일 가중하면 D_i=+0.609747입니다. 같은 사례의 FP에서는 두 정책이 동일한 후보를 고르고 regret이 같았습니다. 이 설명은 특정 계수·관측자료·후보 격자에서 일어난 경로이며 보편 규칙이 아닙니다.']);
}

// 13. negative case
{
 const s=header('사례 606: 경로 간선을 고쳐도 Global이 유리할 수 있었다','반례 · Global 유리',13);
 pill(s,'Step 6 · proposal 000606 · Dᵢ = −0.144787',90,153,445,'#E9EFF8',C.blue);
 text(s,'과제: V03 → V02 · 간접 경로 두 개',90,205,500,34,{size:20,color:C.navy,bold:true});
 const nodeX=[105,255,405];
 [['V03 · X',295],['V04',295],['V02 · Y',295],['V03 · X',415],['V06',415],['V02 · Y',415]].forEach(([lab,y],i)=>{const col=i%3;box(s,nodeX[col],y,112,48,col===0||col===2?C.paleTeal:C.white,C.teal,12);text(s,lab,nodeX[col]+4,y+4,104,40,{size:16,color:C.navy,bold:true,align:'center'});if(col<2)text(s,'→',nodeX[col]+112,y+8,36,30,{size:22,color:C.teal,bold:true,align:'center'});});
 box(s,590,212,590,152,C.soft,C.line,14);text(s,'Global · ID 순서',615,229,530,30,{size:19,color:C.blue,bold:true});text(s,'V01 → V04 반전 · k=+1',615,267,530,32,{size:18,color:C.ink});text(s,'선택 k의 GT loss 0.700153 · regret 0',615,311,530,28,{size:16,color:C.teal,bold:true});
 box(s,590,390,590,152,'#FCF1ED',C.line,14);text(s,'Task-Focused',615,407,530,30,{size:19,color:C.teal,bold:true});text(s,'V06 → V03 반전 · 과제 간선 복구 · k=−1',615,445,530,32,{size:18,color:C.ink});text(s,'선택 k의 GT loss 1.134514 · regret 0.434361',615,489,530,28,{size:16,color:C.red,bold:true});
 text(s,'간선도는 과제 경로 schematic이며 전체 DAG가 아니다 · 선택 사례, 대표성 없음',110,600,1060,28,{size:15,color:C.muted,align:'center'});
 note(s,['Proposal 606은 정책의 방향을 뒤집는 반례입니다. Action V03에서 Target V02로 두 간접 경로가 있습니다. REV 유형에서 Task-Focused는 과제 경로에 놓인 V06→V03을 올바른 V03→V06으로 반전했습니다. 하지만 해당 Ridge 추천은 k=−1이었고 GT loss 1.134514, regret 0.434361이었습니다.','Global은 주변의 V01→V04를 반전하고 k=+1을 골랐습니다. 이 값은 같은 후보 격자에서 최적이어서 GT loss와 regret이 0이었습니다. 따라서 과제 경로에 가까운 간선을 복구하는 것이 항상 더 낮은 손실을 보장하지 않습니다.','이 SCM의 FN과 FP 차이는 0, REV 차이는 −0.434361이어서 composite D_i는 −0.144787입니다. 사례 238과 마찬가지로 이 사례는 설명용 극단값이며 모집단 대표성이나 Global의 일반적 우월성 근거가 아닙니다.']);
}

// 14. conclusions
{
 const s=header('발견은 “일부 조건에서 달라질 수 있다”까지다','결론과 한계',14);
 card(s,85,174,320,145,'0.01466','Step 5 평균 D · 57/64 동률',C.blue,'양수 6 · 음수 1');
 card(s,480,174,320,145,'0.02007','Step 6 평균 D · 167/200 동률',C.teal,'양수 25 · 음수 8');
 card(s,875,174,320,145,'2 코호트','평균 방향은 양수로 관찰',C.orange,'확인적 우월성 검정은 하지 않음');
 box(s,85,365,525,218,C.soft,C.line,15);text(s,'이번 연구가 보여준 것',112,389,460,31,{size:19,color:C.teal,bold:true});text(s,'• 일부 SCM에서 ordering이 k와 regret을 바꿈\n• 그래프 차이와 결정 차이는 다름\n• 평균은 동률·극단값을 함께 요약',112,435,460,112,{size:18,color:C.navy,valign:'top'});
 box(s,670,365,525,218,'#FCF1ED',C.line,15);text(s,'아직 모르는 것',697,389,460,31,{size:19,color:C.red,bold:true});text(s,'• 어느 정책이 일반적으로 우월한가\n• 어떤 구조 지표가 가장 좋은가\n• 실제 TEP/DAT 공정의 효과·안전·비용',697,435,460,112,{size:18,color:C.navy,valign:'top'});
 text(s,'합성 선형 SCM · 완전 관측 · oracle 수정 후보 · B=1 · 기술적 추정',135,620,1010,28,{size:16,color:C.muted,bold:true,align:'center'});
 note(s,['핵심 결과는 두 코호트의 평균 D가 양수였다는 점과, 동시에 대부분이 정확한 동률이었다는 점입니다. Step 5의 평균은 0.01466이며 57/64가 0, Step 6은 0.02007이며 167/200이 0입니다. 두 결과 방향은 비슷하게 관찰됐지만 이는 Option B 기술적 재현이지 확인적 우월성 검정이 아닙니다.','연구는 oracle 오류 후보가 이미 주어진 상황에서 B=1 수정 순서를 평가했습니다. 정책은 스스로 그래프 오류를 발견하는 시스템이 아닙니다. Global은 ID-ordered 기준선이며 최적 정책이 아닙니다.','합성 선형 모델과 완전 관측, 제한된 모집단·과제·조작 격자에서 나온 결과입니다. 실제 제조공정의 개입 효과, 복구, 안전성, 수율 또는 경제 효과는 측정하지 않았습니다. 초기 구조지표 간 우열도 아직 확정되지 않았습니다.']);
}

function slideDiamond(slide,cx,cy,color){
  slide.shapes.add({geometry:'diamond',position:{left:cx-8,top:cy-8,width:16,height:16},fill:color,line:{style:'solid',fill:color,width:0}});
}

await fs.mkdir(BUILD,{recursive:true}); await fs.mkdir(OUT,{recursive:true});
for(let i=0;i<pres.slides.items.length;i++){
  const sl=pres.slides.items[i]; const png=await pres.export({slide:sl,format:'png',scale:2});
  await fs.writeFile(path.join(BUILD,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
}
const pdfDoc=await PDFDocument.create();
for(let i=1;i<=pres.slides.items.length;i++){
  const bytes=await fs.readFile(path.join(BUILD,`slide-${String(i).padStart(2,'0')}.png`));
  const img=await pdfDoc.embedPng(bytes); const page=pdfDoc.addPage([960,540]); page.drawImage(img,{x:0,y:0,width:960,height:540});
}
await fs.writeFile(FINAL_PDF,await pdfDoc.save());
for(let si=0;si<pres.slides.items.length;si++){
  for(const sh of pres.slides.items[si].shapes.items){const p=sh.position;if(p.width<0||p.height<0||!Number.isFinite(p.width)||!Number.isFinite(p.height))console.log('BAD_SHAPE',si+1,sh.name,JSON.stringify(p));}
}
const candidate=path.join(BUILD,'candidate.pptx'); await (await PresentationFile.exportPptx(pres)).save(candidate);
const {finalizePresentation}=await import(pathToFileURL(path.join(SKILL_DIR,'container_tools/artifact_tool_utils.mjs')).href);
const result=await finalizePresentation({
  explicitTotalSlideCount:14,
  requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],
  fontPolicy:{basis:'design',families:[FONT]},
  workspaceDir:ROOT,candidatePath:candidate,finalPath:FINAL_PPTX,
  pythonExecutable:RUNTIME_PYTHON,
  integrityValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit'],
  verifyArtifactToolImport:true,
  receiptPath:path.join(BUILD,'pptx-validation.json'),
});
console.log(JSON.stringify({slides:pres.slides.items.length,pptx:FINAL_PPTX,pdf:FINAL_PDF,finalizer:result},null,2));
