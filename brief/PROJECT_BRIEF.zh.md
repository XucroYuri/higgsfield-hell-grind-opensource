# PROJECT_BRIEF 对照（试点节选）

> **本文件为试点样本**：节选 `PROJECT_BRIEF.md` 中「资产原则（Pre-Production: Assets）」与「技术底座 / Style Prefix + GEO 空间几何」两类段落，作中英对照。
> 原文以同目录 `PROJECT_BRIEF.md` 为权威；此处「原文」块与其同步，冲突以源文件为准。
> 术语遵循 `zh/01-术语表/受控词表.md`；模型/镜头/器材/角色标签保留原文。
> `folder name`、`@tag`、占位符一律不译。

- source_path: `brief/PROJECT_BRIEF.md`
- source_lines: 48–130（资产原则节选）；298–340（Style Prefix / GEO 节选）
- translation_status: **reviewed**
- glossary_version: v0.1

---

# 一、资产原则（Pre-Production: Assets）

## 1. 资产 = 文本 + 图片

**原文 (source)** [L48–L50]

```
An asset is a simple pair: text + image. The text is a full description of the character or place — we call it a descriptor. It goes into every prompt, word for word. The image is a reference — the model uses it as an anchor. Together they keep your hero the same person from shot to shot.
```

**中文对照 (zh)**

```
一个资产（asset）是一个简单组合：文本 + 图片。文本是对角色或地点的完整描述——我们称之为描述符（descriptor）。它逐字进入每一条 prompt。图片是参考——模型把它当作锚点。两者合起来，让主角在镜与镜之间始终是同一个人。
```

## 2. 角色表 = 三张图（其中正面全身无头）

**原文 (source)** [L54–L58]

```
A character sheet is three images:

A close-up of the face, a full body from the front, and a full body from the back. And the front full-body figure has no head. This sounds insane, but it fixed a whole class of broken shots. On wide shots the model kept taking the face from the small full-body figure on the sheet — where the face is tiny and blurry. Remove that head, and the model has only one place to take the face from: the close-up.
```

**中文对照 (zh)**

```
一张角色表（character sheet）是三张图：

一张面部特写、一张正面全身、一张背面全身。而且正面全身的那一尊是【无头】的。这听起来很疯狂，但它修好了一整类坏掉的镜头。之前在一次全景镜头中，模型总去取那尊小小的全身图上——那里面的脸又小又糊——的面孔。去掉那颗头，模型就只剩一个去处可以拿脸：那张特写。
```

## 3. 脸生自 Soul Cinema

**原文 (source)** [L61–L67]

```
Faces were born in Soul Cinema.

It gives the best skin texture, but it is a creative model: one prompt returns several different versions of the face. Pick the most believable one, not the most beautiful one. A "beautiful but fake" face will show its fakeness later, in video — when it is too late to fix. And always check the eyes: even dark eyes need a small light reflection in the pupil (a catch-light). Without it the face looks dead, and no video model can act with a dead face.
```

**中文对照 (zh)**

```
脸生自 Soul Cinema。

它给出最好的皮肤质感，但它是个创作型模型：一条 prompt 会返回好几个不同版本的脸。选最可信的那张，而不是最美的那张。一张“漂亮但假”的脸，往后在视频里就会露出它的假——到那时就来不及修了。并且永远检查眼睛：即便是深色眼睛，瞳孔里也需要一小点亮光反射（眼神光 / catch-light）。没有它，脸就会显得死气沉沉；而没有哪个视频模型能让一张死脸演起来。
```

## 4. 故意把角色表做得朴素

**原文 (source)** [L69–L73]

```
Keep the sheet boring on purpose.

Neutral grey background. Flat light. Real skin with visible pores, no retouch. The cinema look does not live in the character sheet — it lives in the locations and in the video prompts. Bake film grain and cinematic lenses into the sheet, and the character will carry that look into every scene and stop reacting to new light. One more thing we learned: the sheets the model understands best have a large portrait in 3/4 view (the face turned slightly, not straight-on).
```

**中文对照 (zh)**

```
故意把角色表做得朴素。

中性灰背景。平光。真实可见毛孔的皮肤，不修图。电影感不在角色表里——它活在地点资产与视频 prompt 里。若把胶片颗粒与电影镜头烤进角色表，角色就会把那种质感带进每个场景，从而不再对新光线作出反应。我们还学到一点：模型最容易看懂的角色表，通常带一张 3/4 视角的大幅肖像（脸微微侧过，而不是正对镜头）。
```

## 5. 衣服、伤疤、血迹以“点改”加上

**原文 (source)** [L75–L80]

```
Clothes, scars and blood were added as point changes.

Our workflow — one of the possible ones, but it kept the quality for us: make the point change on the original character sheet in Nano Banana Pro or Seedream 4.5, then bring it onto the original by hand in any graphics editor that works with masks. The mask places only the changed part (the jacket, the scar, the blood) on top of the original; everything else stays untouched, so the original skin texture survives. The rule behind it: an image never runs through a model twice in full. Every extra pass destroys texture and drifts color — after two passes the face turns symmetrical, plastic and lifeless, and that dead texture later hurts the acting in video.
```

**中文对照 (zh)**

```
衣服、伤疤、血迹是作为点改（point change）加上的。

我们的工作流——只是可行方案之一，但它帮我们守住了质量：在 Nano Banana Pro 或 Seedream 4.5 里对原始角色表做点改，再在任意支持蒙版（mask）的图形编辑器里手工把它合回原图。蒙版只把被改动的部分（夹克、伤疤、血迹）叠在原图之上；其余一切保持不动，于是原始皮肤质感得以保留。其背后的规则是：**一张图绝不能被模型整张跑第二遍。** 每多过一遍都会毁掉质感、漂移色彩——两遍之后脸就变得对称、塑料化、毫无生气，而这种死掉的质感往后会伤害视频里的表演。
```

## 6. 每个资产在锁定前都过一遍压力测试

**原文 (source)** [L82–L84]

```
Every asset passed a stress test before we locked it:

Ten generations in different poses and different light. The character must be recognizable in ten out of ten. And not alone — next to the other assets, and in the light of the real scenes ahead. A hero who looks stable alone often breaks when he shares the frame with someone. If the test fails, the problem is your description, not the model. Rewrite the words, test again.
```

**中文对照 (zh)**

```
每个资产在锁定前都过一遍压力测试：

用不同姿势、不同光做十次生成。角色必须十次里十次都还能认出。并且不是单独测——要和别的资产挨在一起，还要放在后续真实场景的光线里测。一个单独看很稳定的主角，往往一和别人同框就崩。如果测试失败，问题在你写的描述，不在模型。改词，再测。
```

## 7. 角色每个状态都是独立资产

**原文 (source)** [L101–L103]

```
Every state of a character is a separate asset.

Wet, wounded, changed clothes — that is @roco, @roco_wet, @roco_blood, each with its own description. Mix the states in one text, and the model starts mixing them between shots. Locations work the same way: day, night and rain are three different assets. Even props: our key artifact had three versions — a full one for close-ups, a small bloodied one for a brief reveal in a palm, and a "hidden" one for clenched-fist shots, where the prompt forbids showing the crystal and allows only blue light between the fingers. Splitting states is cheaper than fighting the model.
```

**中文对照 (zh)**

```
角色的每个状态都是独立资产。

湿身、受伤、换衣——分别是 @roco、@roco_wet、@roco_blood，各自有自己的描述。若把所有状态揉进一段文本，模型就会在镜间把它们混淆起来。地点也一样：白天、夜晚、雨天是三个不同的资产。道具亦然：我们的关键圣物就有三个版本——一个给特写用的完整版、一个装在掌心里短暂揭示用的带血小号版、以及一个给紧握拳头镜头用的“隐藏”版——那个版本 prompt 里禁止显示晶体，只允许指缝间透出蓝光。拆开状态比跟模型较劲更省。

```

## 8. 参考要命名角色 / 位置参考禁止“继承”

**原文 (source)** [L118–L126]

```
When you feed assets to Seedance, name the role of every reference.

References are assets only: characters and locations. Name the role of each one right in the prompt — or the model decides by itself, and decides wrong: it copies the composition instead of the face, or the face instead of the color palette.

@roco for character reference
@jaxx for character reference
@loc_cave_front for location reference

Location references get a direct ban on inheritance: "do not use as a starting frame, do not inherit the composition, the angle or the color — take only the space and the texture." All assets live under tags — @roco, @loc_cave_front — and the same tags are used everywhere: in documents, in prompts, in the interface. One dictionary of names for the whole project.
```

**中文对照 (zh)**

```
把资产喂给 Seedance 时，要指名每一份参考的角色。

参考只能是资产：即角色与地点。直接在 prompt 里点名每一份参考的角色——否则模型会自己决定，而且往往决定错：它会把构图当脸来复制，或者把脸当调色板来复制。

@roco 作角色参考
@jaxx 作角色参考
@loc_cave_front 作地点参考

地点参考要直接禁止“继承”：只说“不要用作起始帧，不要继承构图、角度或色彩——只取空间与质感。”所有资产都活在标签之下——@roco、@loc_cave_front——同一套标签在全项目通用：文档里、prompt 里、界面里。全项目只有一本名字字典。
```

---

# 二、技术底座 / Style Prefix + GEO 空间几何（节选）

## 1. Style Prefix（逐字贴入每条 prompt 结尾）

**原文 (source)** [L298–L312]

```
Here is our Style Prefix — copied word for word into the end of every prompt:

Style: 8K IMAX. Photorealistic — no 3D render, no game engine, no game-cutscene aesthetic.
Cinematography: floating immersive camera that lives with the actors; natural motivated light; painterly composed frames, strong silhouettes against the light.
Lighting: Natural light only — contre-jour backlight, camera on shadow side, atmospheric haze throughout. Key light from sky and windows only.
Color: 60:30:10 — dominant / secondary / accent.
Camera: Physical cine lens. 180° shutter motion blur.
Skin: Pore-level realism — vellus hair, asymmetric moles, capillary flush, pore-shadow matching on-set light.
Acting: Hollywood — micro-pauses before reactions, precise eye-line, wet living eyes with catch-lights, visible breath and chest rise.
Physics: Gravity and inertia respected — mass has real weight, correct contact shadows. No floating props.
Composition: Rule of thirds + golden ratio. Every person moving from frame one.
Continuity: Characters, props, environment identical across every cut. No identity drift.
Technical: 24fps smooth motion. 8K detail. No jitter.
Audio: Environmental SFX only. No music. No subtitles.
```

**中文对照 (zh)**

```
以下是我们的 Style Prefix——逐字复制，贴在每条 prompt 的结尾：

Style（风格）：8K IMAX。写实摄影——无 3D 渲染、无游戏引擎、无游戏过场动画美学。
Cinematography（摄影）：漂浮式沉浸镜头，与演员共生；自然动机光；如绘画般构图的画面，以强烈剪影映着光线。
Lighting（照明）：只用自然光——逆光背光（contre-jour），镜头置阴影侧，全程大气霾。主光只来自天空与窗户。
Color（色彩）：60:30:10——主调 / 次调 / 点缀。
Camera（镜头）：真实电影镜头。180° 快门运动模糊。
Skin（皮肤）：毛孔级真实——毫毛、不对称的痣、毛细血管泛红、贴合现场光的毛孔阴影。
Acting（表演）：好莱坞式——反应前的微停顿、精确的视线、湿润有生命且带眼神光的眼睛、可见的呼吸与胸口起伏。
Physics（物理）：尊重重力与惯性——质量有真实重量、正确的接触阴影。无悬浮道具。
Composition（构图）：三分法与黄金比例。从第一帧起每个人都在动。
Continuity（连续性）：角色、道具、环境在每个剪切间【完全一致】。无身份漂移（identity drift）。
Technical（技术）：24fps 平滑运动。8K 细节。无抖动。
Audio（音频）：仅环境音效（SFX）。无音乐。无字幕。
```

> 注：这 12 行即「技术底座」——作为固定咒语逐字复用，须进术语表的词统一；专有名词行保留英文，中文释义仅供理解，不覆盖原文行。

## 2. 收尾标签（mandatory）

**原文 (source)** [L314]

```
Technical tags close the prompt: Photoreal. NON-IP. [aspect ratio]. [duration]s. SFX only. NO CGI. Cinematic.
```

**中文对照 (zh)**

```
技术标签收尾 prompt：Photoreal（写实）。NON-IP（非版权角色）。[宽高比]。[时长]s。SFX only（仅环境音效）。NO CGI（无 CGI）。Cinematic（电影感）。
```

## 3. GEO SPATIAL LAYOUT（空间几何站位）

**原文 (source)** [L318–L322]

```
The most expensive problem of our early takes: characters teleport, swap places, the camera jumps to the wrong side. The reason is simple: the model does not remember who stood where in the previous shot.

The cure is the GEO SPATIAL LAYOUT block. It is a floor plan of the place in a few lines: the landmark objects, what is on the right, what is on the left, where the camera stands. No heroes, no action — only the place itself. You write it once per scene and paste it into every shot of that scene without changes.
```

**中文对照 (zh)**

```
我们早期镜头里最昂贵的毛病：角色瞬移、换位、镜头跳到错误的一侧。原因很简单：模型不记得上一镜里谁站在哪。

解药是 GEO SPATIAL LAYOUT（空间几何站位）块。它是用几行字写出该地点的平面图：地标物、右边是什么、左边是什么、镜头站在哪里。没有主角，没有动作——只有地点本身。你在每个场景写一次，原封不动贴进该场景的每一镜。
```

**原文 (source)** [L322–L325]（示例）

```
GEO SPATIAL LAYOUT (locked across every shot — pure spatial map):
— PLATFORM = raised circular ritual stone disc at the edge of a cliff.
— ALTAR-MONOLITH: at the cliff edge, MID-RIGHT position relative to the platform.
— RITUAL CENTER: CENTER-LEFT, ~3 m from the altar.
— 180° AXIS: camera ALWAYS stays on the corpse-field side — it NEVER crosses the line.
— BACK-LIGHTING: crimson horizon glow comes from BEHIND the platform, rim-lighting silhouettes from camera's perspective.
```

**中文对照 (zh)**

```
GEO SPATIAL LAYOUT（空间几何 / 站位 —— 跨每镜锁定，纯空间图）：
— PLATFORM（祭坛平台）= 悬崖边缘一座抬升的圆形仪式石盘。
— ALTAR-MONOLITH（祭坛独石）= 位于悬崖边，相对平台【中偏右】。
— RITUAL CENTER（仪式中心）=【中偏左】，距祭坛约 3 米。
— 180° AXIS（180° 轴线）= 镜头【始终】停在尸场一侧——【绝不】越线。
— BACK-LIGHTING（逆光）= 绯红地平辉光来自平台【后方】，从镜头视角给剪影勾边缘光。
```

## 4. GEO 补充要点

**原文 (source)** [L334–L340]

```
GEO is only the map. The look of the place still comes from the location asset — its descriptor and reference go into the prompt next to the map.

Sides exist only from the camera: "frame-left" and "frame-right" — the model does not understand "to the left of the hero." Positions are set from the landmark objects and in meters.

The first second is always a wide shot. One second at the start of the scene, no lines and no action: the model "photographs" the arrangement — who stands where, what lies where, where the light comes from — and holds it in every following shot.
```

**中文对照 (zh)**

```
GEO 只是地图。地点的外观仍来自地点资产——它的描述符与参考图片，要随地图一起放进 prompt。

左右只以镜头为基准：“画面左”“画面右”——模型不懂“主角的左手边”。位置以地标物和米数为基准来定。

开场第一秒永远是一个全景镜头。场景开头的那一秒没有任何台词与动作：模型“拍下”这个安排——谁站哪、什么物件在哪、光从哪来——并在之后每一镜里保持住。
```

---

## 备注（试点）

- 术语对照（待评审入库）：`asset → 资产`；`descriptor → 描述符`；`character sheet → 角色表 / 角色三视图资产`；`headless（front full-body）→ 无头(正面全身)`；`point change → 点改 / 局部修改`；`catch-light → 眼神光`；`stress test → 压力测试`；`Style Prefix → Style 前缀（技术底座）`；`contre-jour → 逆光背光`；`rim-light → 边缘光`；`GEO SPATIAL LAYOUT → GEO 空间几何站位（保留 GEO 标题）`。
- 角色标签 `@roco` / `@jaxx` / `@loc_cave_front` 不译。
- 金额/数字/单位保留原文（texture、grain 等已释义）。
- translation_status: **reviewed**（试点评审通过，零 S0/S1）
