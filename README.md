# ETS 试卷答案提取

E听说（ETS）试卷答题内容的离线提取工具：读取本机 ETS 数据目录，把每套试卷按题型整理成答案文本，支持浏览器页面查看 / 复制 / 下载，也支持命令行直接输出。

- 自动识别当前用户的 ETS 数据目录（Windows：`C:\Users\<用户名>\AppData\Roaming\ETS`；macOS / Linux：`~/ETS`），也支持在页面里一键更改 / 恢复默认
- 按目录时间倒序列出全部试卷，「最新」置顶
- 分节输出：听后选择（带序号）、听后回答（带序号）、听后转述、朗读短文
- 纯 Python 标准库，无第三方依赖，完全离线，数据不上传

## 运行（网页版）

Windows：

- 双击 `start.bat`（有控制台窗口，可看日志）
- 首次运行后可用浏览器打开 <http://127.0.0.1:8890/>

macOS / Linux：

```bash
python3 ets_web.py
```

## 运行（命令行）

```bash
python ets_answers.py                 # 最新一套 → ets_answers.txt
python ets_answers.py all             # 全部试卷
python ets_answers.py "路径\586649"   # 指定试卷文件夹
python ets_answers.py --output out.txt
python ets_answers.py --keep-tags     # 保留 HTML 标签
```

## 更改数据目录

网页右上角「更改目录」：粘贴目录路径后保存（Windows 可在资源管理器地址栏复制路径）。修改结果保存在 `ets-config.json`（已加入 .gitignore），重启后仍生效；「恢复默认」回到当前用户的默认目录。

## 目录结构

```
ets_config.py     目录识别与配置（默认目录 / 更改 / 恢复）
ets_core.py       提取与渲染核心（命令行与网页共用）
ets_answers.py    命令行工具
ets_web.py        本地网页服务
ets-ui/           前端页面（白绿主题，原生 JS，无框架）
ets-config.json   运行后生成：用户自定义数据目录（已在 .gitignore）
start.bat         Windows 一键启动
```

## 依赖

- Python 3.8+，仅标准库（`requirements.txt` 为空即表示无第三方依赖）
- 可选：打包单文件 exe —— `pip install pyinstaller && pyinstaller -F ets_web.py`

## 隐私

全部在本机运行：只读取本地 ETS 数据目录，页面无任何外部网络请求。
