# AI记忆召回测试基准（ALFU-R2）

**仓库名称**：`AI-Memory-Recall-Benchmark`  
**GitHub description**：An open benchmark for evaluating AI memory retrieval systems using 500 synthetic conversations, 500 recall queries, evidence-level ground truth, deterministic scoring, and reproducible baselines.  
**数据版本**：`R2 v0.5.2`，*作者重建Gold；尚未经过新版独立语义全面审核*。

## 测试内容

本基准包含 **500个模拟用户—AI聊天框、904个完整问答轮、500道重新设计的召回查询**，用于评价AI记忆系统是否能沿模糊指代、事件／时间线索、隐式跨领域关系结构找到原始历史证据。这是**模拟用户历史**，不是500名真人的私人聊天记录。

数据分为50个模拟用户环境；train/dev/test为300/100/100题。查询中243题属于模糊或上下文依赖指代（含3道需澄清、1道所问信息未记录）；257题为隐式结构问题。需要恢复原始证据的正常召回题共496道。

## Gold与证据位置全部公开

- `public/histories.jsonl`：500框原始历史、角色、会话与合法时间。
- `public/queries.jsonl`：500题与允许检索范围；必要时包含合法当前上下文。
- `public/rounds.jsonl`：轮次与消息映射。
- **`gold/gold.jsonl`**：500条标准答案、查询义务、充分证据集合和替代路径。
- **`gold/evidence_positions.jsonl`**：完整正证据位置索引，原始消息ID、Unicode字符偏移、证据原文及摘要。
- `gold/queries_and_gold_review.md`：作者逐题原文支持与关系注释。
- `gold/revision_records.jsonl`：题面和证据版本修订记录。
- `r2bench/`：完全离线可复算的确定性评分器。

解压后直接运行：

```bash
python -m pip install -r requirements.txt
python -m r2bench validate
python scripts/run_public_baselines.py --public public --output outputs
python -m r2bench score --predictions outputs/bm25.jsonl --output scores/bm25
```

主评测**不强行设置最多3轮或2048-token预算**，候选排序和最终注入分开计分；具体公式见[METRICS](public/METRICS.md)。

## 公开Gold的意义与边界

公开全部Gold可以让他人无须向拥有者申请答案，即可复算Precision、Recall、SufficiencySuccess、片段纯度和基线。**但是公开后的test集不再是保密盲测集。**针对公开答案调参或训练所得的成绩，必须标注为 *open-Gold / non-blind*；它不证明对未见答案数据的泛化表现。未来需要公平排名时，应另外采集未公开的测试样本。

**现有Gold属于作者重建版**，不是500题新增独立审核通过的人工标注；语义替代路径的穷尽性和跨集合隐含泄漏尚未被完整证明。具体局限见[Dataset card](DATASET_CARD.md)。

## 复现与输入隔离

先克隆本仓库，在根目录运行上面的命令。Python要求3.10及以上，本次使用3.12.14。

[复现步骤](docs/REPRODUCING.md)说明如何重评已有3000条预测、重跑六个基线以及对接自己的JSONL输出。[输入隔离说明](docs/EVALUATION_ISOLATION.md)说明如何只向被测系统提供Public。`gold/`、`sources/`、`reports/`、`results/`均属于评测侧资料，不交给被测检索器。目录分开本身不等于访问隔离；被测系统不能访问完整仓库、Git历史或网络上的答案。

`results/raw/`与`results/scores/`保留原有实测结果；新增发布检查另行记录，不冒充原实验。来源、隐私筛查范围与哈希核对见[发布核验记录](reports/PUBLICATION_AUDIT.md)。

## 许可与版本

保留仓库现有的[MIT许可证](LICENSE)，Copyright (c) 2026 ICNERO。项目拥有者具有权利的原创代码、模拟数据、标注及文档适用该许可；第三方材料保留各自条款，不由本仓库重新授权，详见[LICENSING.md](LICENSING.md)。这不表示已经逐段完成第三方版权清权。

数据版本仍为v0.5.2；2026年10月22日仅恢复既有产物、整理发布结构与说明，没有重新生成题目或修改冻结历史及Gold。引用时记录实际使用的commit。
