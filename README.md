# Hell Grind 官方开源镜像

> 本目录是 Higgsfield 公开制作档案的**本地镜像**，且为 **独立 Git 仓库**  
>（与 `../higgsfield-hell-grind-know-how` 分离，远端分别提交）。  
> 遵守工作区铁律：**忠实源头**；禁止以篡改/纠正为目的改内容。  
> 详见 `../AGENTS.md`、`../docs/纪律-开源镜像与迭代开发.md`、`.gitkeep-note.md`。

## 官方入口

https://higgsfield.ai/@higgsfield.studio/projects/hell-grind  

公开 API：`https://fnf.higgsfield.ai`

## 命名铁律

- 官方文件夹 **显示名**（`folder.json` 的 `name`）必须与开源项目一致。  
- 多个同名场次（如两个 `Scene 26`）视为**源头迭代/并行痕迹**，禁止改成 `Scene 26 (2)` 等自创名。  
- 下载期若出现 `Name__xxxxxxxx` 哈希后缀，属于错误便利，**终态须去掉**；不得把哈希后缀当成规范命名。  
- 仅当本机文件系统同级无法容纳两个同名目录时：物理目录用官方 **UUID（folder_id）**，显示名仍只写在元数据里。

## 允许 vs 禁止

| 允许 | 禁止 |
|------|------|
| 下载脚本、映射表、日志 | 改写官方 prompt / 参数冒充原文 |
| 非法字符最小替换；冲突时用官方 UUID 作物理键 | 自创消歧名 / 哈希污染原名 |
| `_media_blobs` 去重存储 | 删除失败 generation「打扫干净」 |
| `meta/` 统计与进度 | 用新生成覆盖 `Assets` 并当官方结果 |

## 主要子目录

| 路径 | 说明 |
|------|------|
| `folders/` | 按场次/功能文件夹的 job_sets 与提示词 |
| `brief/` | 项目 Brief 文本与页面配图 |
| `film/` | 成片参考（HLS 信息 / 本地下载的 mp4） |
| `meta/` | 映射、统计、下载进度（旁路元数据） |
| `scripts/` | 镜像用下载/重命名脚本 |
| `skills/` | 官方技能文件（若取得） |
| `_media_blobs/` | 媒体去重存储 |

## 媒体结构（每场次）

```
Assets/outputs/<job_id>/   # 镜头生成结果
Assets/thumbnails/         # 缩略图
Assets/references/         # 提示词参考素材
```

网页 Brief 配图在 `brief/images/`，与镜头素材分离。

## 语言

说明文档默认中文；档案内官方英/中文提示词保持原样。  
