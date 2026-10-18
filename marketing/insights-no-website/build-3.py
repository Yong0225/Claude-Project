# Builds slides-3.html (EN) and slides-3-zh.html (ZH): insight slides 07-08.
# Layouts deliberately differ from slides 01-06: 07 = light "race" layout, 08 = centred poster.
HEAD = '''<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<title>{title}</title>
<link rel="stylesheet" href="fonts.css">
<link rel="stylesheet" href="fonts-zh.css">
<style>
  :root{{--ink:#2B2B2B;--bone:#E8E6E1;--mute:rgba(232,230,225,.6);--dim:rgba(232,230,225,.34);--line:rgba(232,230,225,.14);--hot:#FF4A2B;
    --head:{head};--headw:{headw};--headcase:{headcase}}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:#111;font-family:Inter,'Noto Sans SC',system-ui,sans-serif;-webkit-font-smoothing:antialiased}}
  .slide{{width:1080px;height:1350px;position:relative;overflow:hidden;margin:0 auto 40px;padding:56px 80px 52px;display:flex;flex-direction:column}}
  .slide::before{{content:"";position:absolute;inset:0;pointer-events:none;opacity:.06;background-image:radial-gradient(currentColor 1px,transparent 1.4px);background-size:7px 7px}}
  .slide>*{{position:relative;flex-shrink:0}}
  .mono{{font-family:'JetBrains Mono','Noto Sans SC',monospace;letter-spacing:.14em;text-transform:uppercase}}
  .top{{display:flex;justify-content:space-between;align-items:flex-start}}
  .mast{{font-size:16px;line-height:1.6;border-left:3px solid var(--hot);padding-left:16px}}
  .pg{{font-size:15px;text-align:right;line-height:1.6}}
  .src{{font-size:12px;letter-spacing:.04em;text-transform:none}}

  /* ===== 07: light, race layout ===== */
  #s1{{background:var(--bone);color:var(--ink)}}
  #s1 .mast{{color:rgba(43,43,43,.6)}} #s1 .mast b,#s1 .pg b{{color:var(--ink)}} #s1 .pg{{color:rgba(43,43,43,.55)}}
  .hero7{{display:grid;grid-template-columns:auto 1fr;align-items:end;gap:34px;margin-top:40px}}
  .big{{font-family:Anton,Impact,sans-serif;font-size:330px;line-height:.78;letter-spacing:-.02em}}
  .big em{{font-style:normal;color:var(--hot);font-size:.5em;vertical-align:top;margin-left:6px}}
  .hero7 p{{font-size:30px;line-height:1.35;padding-bottom:6px;font-weight:500}}
  .hero7 p b{{font-weight:800}}
  .hero7 .src{{display:block;margin-top:10px;color:rgba(43,43,43,.5);font-family:'JetBrains Mono','Noto Sans SC',monospace}}
  .h7{{font-family:var(--head);font-weight:var(--headw);text-transform:var(--headcase);font-size:80px;line-height:1.02;margin-top:44px;padding-top:34px;border-top:3px solid var(--ink)}}
  .h7 em{{font-style:normal;color:var(--hot)}}
  .race{{margin-top:60px;display:grid;gap:64px}}
  .lane .lb{{font-size:16px;margin-bottom:18px;color:rgba(43,43,43,.6)}}
  .lane .lb b{{color:var(--ink)}}
  .track{{display:flex;align-items:flex-start;position:relative}}
  .track::before{{content:"";position:absolute;left:20px;right:20px;top:19px;height:3px;background:repeating-linear-gradient(90deg,rgba(43,43,43,.35) 0 8px,transparent 8px 14px)}}
  .stop{{flex:1;position:relative;text-align:left;padding-right:10px}}
  .stop i{{display:block;width:42px;height:42px;border-radius:50%;background:var(--bone);border:3px solid var(--ink);margin-bottom:12px;position:relative}}
  .stop span{{font-size:22px;line-height:1.3;display:block}}
  .stop.x i{{background:var(--hot);border-color:var(--hot)}}
  .stop.x i::after{{content:"✕";position:absolute;inset:0;display:grid;place-items:center;color:#fff;font-size:20px;font-weight:800}}
  .stop.x span{{color:var(--hot);font-weight:700}}
  .lane.good .track::before{{background:var(--ink);right:auto;width:calc(100% - 40px)}}
  .stop.w{{flex:3.2}} .stop.w span{{font-weight:700}}
  .stop.ok i{{background:var(--ink)}}
  .stop.ok i::after{{content:"✓";position:absolute;inset:0;display:grid;place-items:center;color:var(--bone);font-size:20px;font-weight:800}}
  .stop.ok span{{font-weight:800}}
  .foot7{{margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end;gap:30px}}
  .foot7 .so{{font-size:28px;font-weight:600}} .foot7 .so b{{color:var(--hot)}}
  .foot7 .src{{color:rgba(43,43,43,.45);font-family:'JetBrains Mono','Noto Sans SC',monospace;text-align:right;max-width:330px;line-height:1.5}}

  /* ===== 08: dark, centred poster ===== */
  #s2{{background:#1f1d1b;color:var(--bone);text-align:center}}
  #s2 .top{{text-align:left}} #s2 .mast,#s2 .pg{{color:var(--mute)}} #s2 .mast b,#s2 .pg b{{color:var(--bone)}}
  #s2 .kick{{font-size:17px;color:var(--hot);margin-top:34px}}
  .stage{{position:relative;height:720px;margin-top:26px}}
  .ph{{position:absolute;top:50px;width:335px;background:#000;border-radius:40px;padding:12px;border:2px solid #444;box-shadow:0 40px 80px rgba(0,0,0,.55)}}
  .ph.l{{left:10px;transform:rotate(-7deg)}} .ph.r{{right:10px;transform:rotate(6deg)}}
  .sc{{border-radius:29px;height:560px;overflow:hidden;text-align:left;font-family:Inter,'Noto Sans SC',sans-serif}}
  .messy{{background:#fff;color:#111;padding:18px 16px}}
  .messy .bar{{display:flex;justify-content:space-between;font-weight:700;font-size:15px}}
  .messy .jpg{{margin-top:14px;height:190px;background:repeating-linear-gradient(0deg,#f3eee4 0 13px,#e2d9c6 13px 14px);position:relative;transform:rotate(-2deg);border:1px solid #ccc;box-shadow:0 4px 10px rgba(0,0,0,.15)}}
  .messy .jpg::after{{content:"MENU_final_v3.jpg";position:absolute;right:8px;bottom:6px;font-family:'JetBrains Mono',monospace;font-size:10px;color:#999}}
  .messy .jpg i{{position:absolute;left:14px;top:16px;width:60%;height:10px;background:#b9ad96;box-shadow:0 26px 0 #b9ad96,0 52px 0 #b9ad96,0 78px 0 #b9ad96,0 104px 0 #b9ad96,0 130px 0 #b9ad96;filter:blur(1.4px)}}
  .messy .lt{{margin-top:20px;display:grid;gap:9px}}
  .messy .lt div{{border:1.5px solid #111;border-radius:30px;text-align:center;padding:10px;font-size:13px;font-weight:600}}
  .messy .dm{{margin-top:12px;font-size:12px;color:#888;text-align:center}}
  .clean{{background:#171513;color:#f2ede4;display:flex;flex-direction:column}}
  .clean .hero{{height:220px;background:linear-gradient(160deg,rgba(0,0,0,.05),rgba(0,0,0,.7)),radial-gradient(circle at 35% 40%,#d9a066,#7a4a2a 55%,#2b1a10);display:flex;flex-direction:column;justify-content:flex-end;padding:18px}}
  .clean .hero b{{font-family:var(--head);font-weight:var(--headw);font-size:30px;letter-spacing:.02em}}
  .clean .hero span{{font-size:12px;opacity:.8;margin-top:3px}}
  .clean .mn{{padding:16px 18px;display:grid;gap:12px;font-size:14px}}
  .clean .mn div{{display:flex;justify-content:space-between;border-bottom:1px dotted rgba(242,237,228,.25);padding-bottom:9px}}
  .clean .mn em{{font-style:normal;opacity:.75}}
  .clean .bk{{margin:auto 18px 18px;background:#f2ede4;color:#171513;text-align:center;padding:13px;border-radius:30px;font-weight:700;font-size:14px}}
  .bub{{position:absolute;top:0;font-size:21px;font-weight:700;padding:12px 18px;border-radius:18px;z-index:3;white-space:nowrap}}
  .bub.l{{left:0;background:var(--bone);color:var(--ink);transform:rotate(-4deg)}}
  .bub.r{{right:0;background:var(--bone);color:var(--ink);transform:rotate(3deg)}}
  .bub.l b{{color:var(--hot)}}
  .tagp{{position:absolute;bottom:0;font-size:14px;color:var(--dim)}} .tagp.l{{left:40px}} .tagp.r{{right:40px}}
  .sticker{{position:absolute;left:50%;top:250px;width:236px;height:236px;margin-left:-118px;border-radius:50%;background:var(--hot);color:#fff;z-index:4;display:flex;flex-direction:column;align-items:center;justify-content:center;box-shadow:0 20px 50px rgba(0,0,0,.5);transform:rotate(-8deg);padding:20px}}
  .sticker b{{font-family:Anton,Impact,sans-serif;font-weight:400;font-size:96px;line-height:.9}}
  .sticker span{{font-size:16px;line-height:1.3;font-weight:700;margin-top:6px}}
  .h8{{font-family:var(--head);font-weight:var(--headw);text-transform:var(--headcase);font-size:78px;line-height:1.03;margin-top:34px}}
  .h8 em{{font-style:normal;color:var(--hot)}}
  .foot8{{margin-top:auto}}
  .foot8 .so{{font-size:25px;color:var(--mute)}} .foot8 .so b{{color:var(--bone)}}
  .foot8 .src{{display:block;margin-top:12px;color:var(--dim);font-family:'JetBrains Mono','Noto Sans SC',monospace}}
</style>
</head>
'''

def build(T, zh):
    head = HEAD.format(lang='zh-Hans' if zh else 'en', title=T['title'],
                       head="'Noto Sans SC',sans-serif" if zh else "Anton,Impact,sans-serif",
                       headw='900' if zh else '400', headcase='none' if zh else 'uppercase')
    top = lambda n, name: f'''  <div class="top">
    <div class="mast mono"><b>{T['m1']}</b><br>{T['m2']}</div>
    <div class="pg mono"><b>{T['kf']}</b><br>0{n} / 08 — {name}</div>
  </div>'''
    bad = ''.join(f'<div class="stop"><i></i><span>{s}</span></div>' for s in T['bad']) + f'<div class="stop x"><i></i><span>{T["lost"]}</span></div>'
    menu = ''.join(f'<div><span>{a}</span><em>{b}</em></div>' for a, b in T['menu'])
    return head + f'''<body>

<!-- ===================== SLIDE 07 ===================== -->
<section class="slide" id="s1">
{top(7, T['n7'])}

  <div class="hero7">
    <div class="big">77<em>%</em></div>
    <p>{T['s7']}<span class="src">— {T['srcs7']}</span></p>
  </div>

  <div class="h7">{T['h7']}</div>

  <div class="race">
    <div class="lane">
      <div class="lb mono"><b>{T['la']}</b></div>
      <div class="track">{bad}</div>
    </div>
    <div class="lane good">
      <div class="lb mono"><b>{T['lb']}</b></div>
      <div class="track"><div class="stop w"><i></i><span>{T['one']}</span></div><div class="stop ok"><i></i><span>{T['won']}</span></div></div>
    </div>
  </div>

  <div class="foot7">
    <div class="so">{T['f7']}</div>
    <div class="src">{T['src7']}</div>
  </div>
</section>

<!-- ===================== SLIDE 08 ===================== -->
<section class="slide" id="s2">
{top(8, T['n8'])}

  <div class="kick mono">{T['k8']}</div>

  <div class="stage">
    <div class="bub l">{T['b1']}</div>
    <div class="bub r">{T['b2']}</div>
    <div class="ph l"><div class="sc messy">
      <div class="bar"><span>yourrestaurant</span><span>☰</span></div>
      <div class="jpg"><i></i></div>
      <div class="lt"><div>{T['lt1']}</div><div>{T['lt2']}</div><div>{T['lt3']}</div></div>
      <div class="dm">linktr.ee/yourrestaurant</div>
    </div></div>
    <div class="ph r"><div class="sc clean">
      <div class="hero"><b>{T['brand']}</b><span>{T['tagl']}</span></div>
      <div class="mn">{menu}</div>
      <div class="bk">{T['bk']}</div>
    </div></div>
    <div class="sticker"><b>75%</b><span>{T['st']}</span></div>
    <div class="tagp l mono">{T['l1']}</div>
    <div class="tagp r mono">{T['l2']}</div>
  </div>

  <div class="h8">{T['h8']}</div>

  <div class="foot8">
    <div class="so">{T['f8']}</div>
    <span class="src">{T['src8']}</span>
  </div>
</section>

</body>
</html>
'''

EN = dict(title='F&amp;B Digital Report III', m1='F&amp;B Digital Report', m2='Diner behaviour digest', kf='Key finding',
  n7='Decision speed', s7='of diners <b>check a restaurant’s website before they go.</b>', srcs7='MGH Restaurant Survey',
  h7='Hungry people don’t dig.<br><em>They pick the easy one.</em>',
  la='Without a website', bad=['Menu in 4 IG highlights', 'No prices listed', 'Hours on Google — right?', 'DM to book, wait'],
  lost='Picked someone else',
  lb='With a website', one='One page: menu · prices · hours · booking', won='Table booked',
  f7='Every extra step is <b>a reason to leave.</b>',
  src7='Source: MGH survey of 1,101 US diners (2019), via restaurantdive.com',
  n8='First impressions', k8='The perceived-value gap',
  b1='<b>“Hmm… is it worth it?”</b>', b2='“Worth the price.”',
  lt1='📋 Menu (updated?)', lt2='📍 Location', lt3='💬 DM to book',
  brand='YOUR RESTAURANT', tagl='Charcoal grill · Since 2012',
  menu=[('Signature short rib', '48'), ('Charcoal chicken', '32'), ('Seasonal greens', '16')], bk='Book a table',
  st='judge credibility by website design', l1='IG only', l2='Own website',
  h8='They judge the restaurant<br><em>before they taste the food.</em>',
  f8='Your food is premium. <b>Make the first impression match.</b>',
  src8='Source: Stanford Web Credibility Project (B.J. Fogg) · all businesses, not restaurant-specific')

ZH = dict(title='餐饮数字化报告 III', m1='餐饮数字化报告', m2='食客行为观察', kf='重点发现',
  n7='决定速度', s7='的客人去之前，<br><b>会先看餐厅网站。</b>', srcs7='MGH 食客调查',
  h7='客人肚子饿，<br><em>不会慢慢找。</em>',
  la='没有网站', bad=['菜单藏在 4 个 Highlight', '价钱没写', '营业时间，Google 对吗？', 'DM 订位，等你回'],
  lost='换了一间',
  lb='有网站', one='一页看完：菜单 · 价钱 · 时间 · 订位', won='订到位了',
  f7='多一个步骤，<b>就多一个理由走人。</b>',
  src7='来源：MGH 美国食客调查（1,101 人，2019），引自 restaurantdive.com',
  n8='第一印象', k8='没网站，看起来就不值钱',
  b1='<b>“这个价钱，值得吗？”</b>', b2='“贵得有道理。”',
  lt1='📋 菜单（最新吗？）', lt2='📍 地址', lt3='💬 DM 订位',
  brand='你的餐厅', tagl='炭火烧烤 · 始于 2012',
  menu=[('招牌牛小排', '48'), ('炭烤鸡', '32'), ('时令青菜', '16')], bk='立即订位',
  st='的人看网站<br>判断靠不靠谱', l1='只有 IG', l2='有自己的网站',
  h8='还没吃到，<br><em>客人已经在打分了。</em>',
  f8='你的菜够好，<b>第一印象也要配得上。</b>',
  src8='来源：Stanford Web Credibility Project（B.J. Fogg）· 调查对象为各行业，非只限餐厅')

open('slides-3.html', 'w').write(build(EN, False))
open('slides-3-zh.html', 'w').write(build(ZH, True))
