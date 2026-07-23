# 深度调研工作流（调研专家引擎）

> 本文件是「调研专家」的执行手册，内嵌完整 Deep Research 工作流（大纲 → 并行搜索 → 报告）。
> 适用：竞品调研、行业分析、技术选型、现有方案对比、市场/尽职调查。
> 依赖：WebSearch 能力；子 agent `web-search-agent`（定义见 `../agents/web-search-agent.md`）。

## 总览

```
用户给出调研话题 topic
   ↓ Step 1 生成大纲（模型知识 + 1 个 web-search-agent 补充）→ outline.yaml + fields.yaml
   ↓ 用户确认 items / 字段 / 时间范围 / 批次
Step 2 并行深度搜索（分批启动多个 web-search-agent）→ results/*.json（validate_json.py 校验）
   ↓
Step 3 汇总报告 → generate_report.py → report.md
   ↓
产出物回流：竞品/行业/技术报告 → 项目资料库 + 产品专家需求评估/PRD 输入
```

产物目录：`{当前工作目录}/{topic_slug}/`
- `outline.yaml`：调研对象(items) + 执行配置
- `fields.yaml`：字段定义（分类 + name + description + detail_level + required）
- `results/`：逐项结构化 JSON
- `report.md`：最终汇总报告

---

## Step 1 · 生成大纲（/research 等价）

### 1.1 模型内部知识生成初步框架
基于 topic，利用模型已有知识生成：调研对象 items 列表 + 建议字段框架。
用 **AskUserQuestion** 确认：items 是否需要增减？字段框架是否满足？

### 1.2 Web Search 补充
用 AskUserQuestion 询问**时间范围**（最近 6 个月 / 2024 年至今 / 不限）。

启动 1 个 `web-search-agent`（后台），**Prompt 模板（严格复述，仅替换变量）**：

```
## 任务
调研话题: {topic}
当前日期: {YYYY-MM-DD}

基于以下初步框架，补充最新 items 和推荐调研字段。

## 已有框架
{step1_output}

## 目标
1. 验证已有 items 是否遗漏重要对象
2. 根据遗漏对象进行补充 items
3. 继续搜索 {topic} 相关且 {time_range} 内的 items 并补充
4. 补充新 fields

## 输出要求
直接返回结构化结果（不写文件）：

### 补充 Items
- item_name: 简要说明（为什么应该加入）
...

### 推荐补充字段
- field_name: 字段描述（为什么需要这个维度）
...

### 信息来源
- [来源1](url1)
- [来源2](url2)
```

### 1.3 询问用户已有字段
用 AskUserQuestion 询问用户是否有已定义的字段文件，如有则读取并合并。

### 1.4 生成 Outline（分离文件）
合并 step1、step2 输出与用户字段，生成两个文件：

**outline.yaml**（items + 配置）：
- `topic`: 调研主题
- `items`: 调研对象列表（name / category / description）
- `execution`:
  - `batch_size`: 并行 agent 数量（AskUserQuestion 确认）
  - `items_per_agent`: 每 agent 调研项数（AskUserQuestion 确认）
  - `output_dir`: 结果目录（默认 `./results`）

**fields.yaml**（字段定义）：
- 字段分类与定义
- 每字段：`name`、`description`、`detail_level`（极简 → 简要 → 详细）
- `required`: 是否必填
- `uncertain`: 不确定字段列表（deep 阶段自动填充）

### 1.5 输出并确认
- 创建 `./{topic_slug}/`，保存 `outline.yaml` 与 `fields.yaml`
- 展示给用户确认

---

## Step 2 · 并行深度搜索（/research-deep 等价）

### 2.1 自动定位 Outline
在当前工作目录查找 `*/outline.yaml`，读取 items 与 execution 配置。

### 2.2 断点续传检查
检查 `output_dir` 下已完成 JSON，跳过已完成的 items。

### 2.3 分批执行
- 按 `batch_size` 分批（每批完成需用户同意才进行下一批）
- 每个 agent 负责 `items_per_agent` 个项目
- 后台并行启动 `web-search-agent`（禁用 task output）

**Prompt 模板（严格复述，仅替换变量）**：

```
## 任务
调研 {item_related_info}，输出结构化 JSON 到 {output_path}

## 字段定义
读取 {fields_path} 获取所有字段定义

## 输出要求
1. 按 fields.yaml 定义的字段输出 JSON
2. 不确定的字段值标注 [不确定]
3. JSON 末尾添加 uncertain 数组，列出所有不确定的字段名
4. 所有字段值必须使用中文输出（调研过程可用英文，但最终 JSON 值为中文）

## 输出路径
{output_path}

## 验证
完成 JSON 输出后，运行验证脚本确保字段完整覆盖：
python ~/.codebuddy/skills/产品专家团/scripts/validate_json.py -f {fields_path} -j {output_path}
验证通过后才算完成任务。
```

参数：
- `{item_related_info}`：item 完整 yaml（name + category + description）
- `{fields_path}`：`{topic}/fields.yaml` 绝对路径
- `{output_path}`：`{output_dir}/{item_name_slug}.json`（slugify：空格→`_`，去特殊字符）
- `{output_dir}`：`outline.yaml` 中 `execution.output_dir`（默认 `./results`）

### 2.4 等待与监控
- 等待当前批次完成 → 启动下一批 → 显示进度

### 2.5 汇总
全部完成后输出：完成数量、失败/不确定标记项、输出目录。

---

## Step 3 · 汇总报告（/research-report 等价）

### 3.1 定位结果目录
查找 `*/outline.yaml`，读取 topic 与 output_dir。

### 3.2 扫描可选摘要字段
读取所有 JSON，提取适合目录显示的字段（数值型 / 简短指标，如 stars、score、估值、发布日期）。
用 AskUserQuestion 询问用户：目录除 item 名称外还需显示哪些字段？

### 3.3 生成转换脚本
在 `{topic}/` 下生成 `generate_report.py`，要求：
- 读取 `output_dir` 所有 JSON + `fields.yaml`
- 覆盖每个 JSON 全部字段值
- 跳过值含 `[不确定]` 的字段、跳过 `uncertain` 数组所列字段、跳过 None / 空字符串
- 兼容扁平 / 嵌套两种 JSON 结构（字段查找：顶层 → category 映射 key → 遍历嵌套 dict）
- 复杂值格式化：list of dicts 每行 ` | ` 分隔；长文本 >100 字符加 `<br>` 或 blockquote
- 收集 JSON 有但 fields.yaml 未定义的字段 → "其他信息"
- 目录（带锚点跳转 + 用户所选摘要字段）+ 详细内容（按字段分类）
- 保存到 `{topic}/report.md`

### 3.4 执行脚本
运行 `python {topic}/generate_report.py`，产出 `report.md`。

---

## 追加能力（可选）
- **补充 items**：定位 `outline.yaml`，询问用户/可启动 agent 搜索更多对象，追加并去重。
- **补充字段**：定位 `fields.yaml`，询问用户输入或 agent 搜索，追加字段分类与 detail_level。

## 产物回流提醒
调研完成后：
1. 将 `report.md`（及 `results/`）上传项目资料库，形成统一上下文。
2. 把竞品 / 行业 / 技术结论作为**输入**，交给「产品专家」做需求价值评估与 PRD 撰写。
3. 如发现需要补充调研对象 / 字段，使用上述追加能力迭代。
