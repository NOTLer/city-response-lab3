from pathlib import Path
from xml.sax.saxutils import escape
import subprocess,json,xml.etree.ElementTree as ET
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1] / 'docs'
nodes={'client':'Веб-клиент\nДиспетчер / Бригада / Администратор','gateway':'API Gateway\nNginx','auth':'Keycloak','authdb':'Keycloak DB\nPostgreSQL','incident':'incident-service','resource':'resource-service','dispatch':'dispatch-service\nSaga worker','operation':'operation-service','notification':'notification-service','broker':'RabbitMQ\ncity.events','smtp':'SMTP\nMailpit'}
for n in ['incident','resource','dispatch','operation','notification']:nodes[n+'db']=n+' DB\nPostgreSQL'
edges=[]
def edge(a,b,l,d=False):edges.append((a,b,l,d))
edge('client','gateway','HTTPS /api/v1/*, /auth/*')
edge('gateway','auth','HTTP /auth/* (OIDC)')
edge('auth','authdb','SQL')
edge('gateway','incident','HTTP /api/v1/incidents[/{id}]')
edge('gateway','resource','HTTP /api/v1/teams')
edge('gateway','dispatch','HTTP /api/v1/dispatches[/{id}[/cancel]]')
edge('gateway','operation','HTTP /api/v1/operations[/{dispatchId}[/*]]')
edge('gateway','notification','HTTP /api/v1/notifications[/{id}/retry]\n/api/v1/notification-preferences')
edge('dispatch','incident','HTTP GET /internal/v1/incidents/{id}')
edge('dispatch','resource','HTTP GET /internal/v1/teams/{id}\nPOST /internal/v1/reservations\nGET /internal/v1/reservations/{dispatchId}\nPOST /internal/v1/reservations/{dispatchId}/confirm\nPOST /internal/v1/reservations/{dispatchId}/release')
edge('dispatch','operation','HTTP PUT, GET /internal/v1/operations/{dispatchId}\nPOST /internal/v1/operations/{dispatchId}/cancel')
for n in ['incident','resource','dispatch','operation','notification']:edge(n,n+'db','SQL; только собственная БД')
edge('incident','broker','incident.created',True)
edge('operation','broker','operation.accepted\noperation.rejected\noperation.completed',True)
edge('dispatch','broker','dispatch.confirmed\ndispatch.cancelled\ndispatch.completed',True)
edge('broker','dispatch','incident.created\noperation.accepted / rejected / completed',True)
edge('broker','operation','dispatch.confirmed',True)
edge('broker','incident','dispatch.completed',True)
edge('broker','notification','dispatch.confirmed / cancelled / completed',True)
edge('notification','smtp','SMTP: отправка письма')
# JWT verification note: no permanent business synchronous dependency on identity server.
dot=['digraph architecture {','graph [rankdir=TB, bgcolor="white", pad=0.4, nodesep=0.8, ranksep=1.2, fontname="DejaVu Sans", label="City Response — контейнеры и взаимодействия\nСплошные: запросы; пунктир: события. JWT проверяют сервисы по кэшированным JWKS Keycloak.", labelloc=t, fontsize=20];','node [shape=box, style="rounded,filled", fillcolor="#eaf2ff", color="#395a86", fontname="DejaVu Sans", fontsize=13, margin="0.18,0.12"];','edge [fontname="DejaVu Sans", fontsize=10, color="#53647a"];']
for id,label in nodes.items():dot.append(f'{id} [label={json.dumps(label,ensure_ascii=False)}'+(',shape=cylinder,fillcolor="#e8f4ec"' if id.endswith('db') else ',fillcolor="#fff0d8"' if id in ['broker','smtp','auth'] else '')+'];')
for a,b,l,d in edges:dot.append(f'{a} -> {b} [label={json.dumps(l,ensure_ascii=False)}'+(',style=dashed,color="#986216",fontcolor="#80520e",constraint=false' if d else '')+'];')
dot.append('}')
(R/'architecture.dot').write_text('\n'.join(dot))
for fmt in ['svg','png','json']:subprocess.run(['dot',f'-T{fmt}',str(R/'architecture.dot'),'-o',str(R/f'architecture.{fmt}')],check=True)
# Editable draw.io version, same nodes and relations; take Graphviz coordinates.
data=json.loads((R/'architecture.json').read_text());bb=list(map(float,data['bb'].split(','))); H=bb[3]
mx=ET.Element('mxfile',host='app.diagrams.net');dia=ET.SubElement(mx,'diagram',id='architecture',name='Architecture');model=ET.SubElement(dia,'mxGraphModel',dx='1600',dy='1200',grid='1',gridSize='10',page='0');root=ET.SubElement(model,'root');ET.SubElement(root,'mxCell',id='0');ET.SubElement(root,'mxCell',id='1',parent='0')
for n in data['objects']:
 if n.get('name') not in nodes:continue
 x,y=map(float,n['pos'].split(','));w=float(n['width'])*72;h=float(n['height'])*72
 cell=ET.SubElement(root,'mxCell',id=n['name'],value=nodes[n['name']],style='rounded=1;whiteSpace=wrap;html=0;fillColor=#eaf2ff;strokeColor=#395a86;',vertex='1',parent='1')
 ET.SubElement(cell,'mxGeometry',x=str(x-w/2),y=str(H-y-h/2),width=str(w),height=str(h),attrib={'as':'geometry'})
for i,(a,b,l,d) in enumerate(edges):
 cell=ET.SubElement(root,'mxCell',id='e'+str(i),value=l,style='edgeStyle=orthogonalEdgeStyle;rounded=0;html=0;endArrow=block;'+('dashed=1;strokeColor=#986216;' if d else ''),edge='1',parent='1',source=a,target=b)
 ET.SubElement(cell,'mxGeometry',relative='1',attrib={'as':'geometry'})
ET.ElementTree(mx).write(R/'architecture.drawio',encoding='utf-8',xml_declaration=True)
(R/'architecture.json').unlink()
# True sequence diagrams: chronological messages and vertical lifelines.
actors=['Клиент','Gateway','dispatch','incident','resource','operation','RabbitMQ','notification']
success=[(0,1,'POST /api/v1/dispatches'),(1,2,'POST /api/v1/dispatches'),(2,1,'202 PREPARING'),(1,0,'202 + dispatchId'),(2,3,'GET /internal/v1/incidents/{id}'),(3,2,'200 OPEN, тип, адрес'),(2,4,'GET /internal/v1/teams/{id}'),(4,2,'200 специализация'),(2,4,'POST /internal/v1/reservations'),(4,2,'201 HELD'),(2,5,'PUT /internal/v1/operations/{dispatchId}'),(5,2,'201 OFFERED'),(2,2,'AWAITING_ACCEPTANCE'),(0,1,'POST /api/v1/operations/{dispatchId}/decision'),(1,5,'decision: ACCEPT'),(5,6,'operation.accepted',True),(6,2,'operation.accepted',True),(2,2,'CONFIRMING'),(2,4,'POST /internal/v1/reservations/{dispatchId}/confirm'),(4,2,'200 CONFIRMED'),(2,2,'ACTIVE + outbox (одна транзакция)'),(2,6,'dispatch.confirmed',True),(6,5,'dispatch.confirmed → ACTIVE',True),(6,7,'dispatch.confirmed → письмо',True),(0,1,'POST /api/v1/operations/{dispatchId}/reports'),(1,5,'ON_SITE, затем COMPLETED'),(5,6,'operation.completed',True),(6,2,'operation.completed',True),(2,4,'POST /internal/v1/reservations/{dispatchId}/release'),(4,2,'200 RELEASED'),(2,2,'COMPLETED + outbox'),(2,6,'dispatch.completed',True),(6,3,'dispatch.completed → CLOSED',True),(6,7,'dispatch.completed → письмо',True)]
failure=[(0,1,'POST /api/v1/dispatches'),(1,2,'Создать PREPARING → 202'),(2,3,'GET /internal/v1/incidents/{id}'),(3,2,'200 OPEN'),(2,4,'GET /internal/v1/teams/{id}'),(4,2,'200 подходящая специализация'),(2,4,'POST /internal/v1/reservations'),(4,2,'201 HELD'),(2,5,'PUT /internal/v1/operations/{dispatchId}'),(5,2,'201 OFFERED'),(2,2,'AWAITING_ACCEPTANCE; истёк acceptBy'),(2,2,'CAS → CANCELLING'),(2,5,'POST /internal/v1/operations/{dispatchId}/cancel'),(5,2,'Ответ потерян после commit CANCELLED'),(2,2,'Резерв удерживается до подтверждения'),(2,5,'Повтор cancel с прежним Idempotency-Key'),(5,2,'200 CANCELLED'),(2,4,'POST /internal/v1/reservations/{dispatchId}/release'),(4,2,'200 RELEASED'),(2,2,'CANCELLED + outbox'),(2,6,'dispatch.cancelled',True),(6,7,'dispatch.cancelled → письмо',True),(6,2,'Запоздалое operation.accepted',True),(2,2,'Inbox: событие обработано; статус не меняется')]
fontpath='/usr/share/fonts/TTF/DejaVuSans.ttf'
if not Path(fontpath).exists():fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font=ImageFont.truetype(fontpath,17);small=ImageFont.truetype(fontpath,16);titlefont=ImageFont.truetype(fontpath,26)
def seq(name,title,msgs):
 W=1900;H=180+len(msgs)*68;xs=[110+i*238 for i in range(len(actors))]
 im=Image.new('RGB',(W,H),'white');d=ImageDraw.Draw(im)
 svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="white"/><defs><marker id="arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><path d="M0,0 L10,4 L0,8" fill="#35587b"/></marker></defs>']
 def txt(x,y,t,f=small,anchor='start'):
  d.text((x,y),t,fill='#233b55',font=f,anchor='mt' if anchor=='middle' else 'lt')
  svg.append(f'<text x="{x}" y="{y+18}" font-family="DejaVu Sans, sans-serif" font-size="{26 if f==titlefont else 17}" text-anchor="{anchor}" fill="#233b55">{escape(t)}</text>')
 def line(x1,y1,x2,y2,dash=False,arrow=False):
  if dash:
   import math
   dist=((x2-x1)**2+(y2-y1)**2)**.5
   for off in range(0,int(dist),12):
    b=min(off+6,dist);d.line((x1+(x2-x1)*off/dist,y1+(y2-y1)*off/dist,x1+(x2-x1)*b/dist,y1+(y2-y1)*b/dist),fill='#35587b',width=2)
  else:d.line((x1,y1,x2,y2),fill='#35587b',width=2)
  if arrow:
   sign=1 if x2>x1 else -1;d.polygon([(x2,y2),(x2-10*sign,y2-5),(x2-10*sign,y2+5)],fill='#35587b')
  svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#35587b" stroke-width="2"'+(' stroke-dasharray="6 6"' if dash else '')+(' marker-end="url(#arrow)"' if arrow else '')+'/>')
 txt(40,20,title,titlefont)
 for i,a in enumerate(actors):
  x=xs[i];d.rounded_rectangle((x-95,70,x+95,115),radius=6,fill='#eaf2ff',outline='#35587b');svg.append(f'<rect x="{x-95}" y="70" width="190" height="45" rx="6" fill="#eaf2ff" stroke="#35587b"/>');txt(x,82,a,font,'middle');line(x,115,x,H-20,True)
 for i,msg in enumerate(msgs):
  a,b,t,*flag=msg;y=160+i*68;label=str(i+1)+'. '+t
  if a==b:
   x=xs[a];w=min(680,max(300,int(d.textlength(label,font=small))+20));d.rectangle((x+8,y-24,x+8+w,y+8),fill='#fff3da');svg.append(f'<rect x="{x+8}" y="{y-24}" width="{w}" height="32" fill="#fff3da"/>');txt(x+16,y-19,label)
  else:
   x1,x2=xs[a],xs[b];line(x1,y,x2,y,bool(flag),True);tw=d.textlength(label,font=small);mid=(x1+x2)/2;tx=max(8,min(W-tw-8,mid-tw/2));d.rectangle((tx-3,y-26,tx+tw+3,y-3),fill='white');svg.append(f'<rect x="{tx-3}" y="{y-26}" width="{tw+6}" height="23" fill="white"/>');txt(tx,y-23,label)
 svg.append('</svg>');(R/(name+'.svg')).write_text('\n'.join(svg));im.save(R/(name+'.png'))
seq('sequence-success','Назначение бригады — успешный путь и завершение',success)
seq('sequence-failure','Срок принятия истёк — компенсация с потерянным ответом',failure)
print('Architecture and sequence diagrams generated')
