# R2 v0.5.2 检索输入输出协议

输入为 histories.jsonl、rounds.jsonl 和 queries.jsonl。历史中的 turn_id 是单条角色消息，不等于一轮；一轮以 rounds.jsonl 的 round_id 定位。当前问题可同时具有 current_context，检索器须自行消解，不获得作者改写后的显式目标。query_at/query_timezone 为模拟评测时钟，不用执行机器的今天替换。

每道问题仅访问 allowed_frame_ids 且不晚于 query_at 的原文。候选池按同一用户、访问权限和截止时间界定；不由Gold预筛到正确事件。历史是构造的模拟用户—AI对话，不是500名真人日志。

输出每行JSON：
```json
{"query_id":"<输入查询ID>","action":"RETRIEVE","candidate_results":[{"round_id":"<实际轮ID>","rank":1}],"final_injection":[{"message_id":"<原始消息ID>","start":0,"end":2,"text":"原文"}],"confidence":0.7,"latency_ms":12.3}
```

candidate_results 可以直接是排序后的round_id字符串列表。不得重复候选；若提供rank，必须与列表顺序一致。没有外加候选数量限制。

final_injection 必须逐字等于源消息的Unicode码点[start,end)区间；不做Unicode归一化。不得用生成摘要冒充原文。默认不限制注入轮数或token；本系统实际选择什么就提交什么。重复片段计入真实成本，证据覆盖按源位置去重。最终送给下游模型的规范文本使用serialize.py生成，源ID仅在结构化字段中保留，不将随机ID计入文本头。

省略final_injection表示未执行注入策略，注入指标null且分母0；显式[]是实际空注入，正常召回题记零分。纯排序器不被评测器自动补成“注入全部候选”。省略candidate_results表示未提供排名层，不自动从注入倒造排名。完全缺少应测query_id的记录视为缺失输出，该题仍进入评分分母。

action为RETRIEVE、CLARIFY或ABSTAIN。CLARIFY用于输入仍有多个合理指向；ABSTAIN用于合法历史不能支持所问信息，相关讨论存在不代表所问字段已记录。检索器不会获得正确action。动作准确率只判定这三个显式枚举，不把它解释为自动核验了澄清问题或拒答解释的全部内容。

confidence与latency_ms可省略；提供时应是有限数，confidence位于[0,1]、latency_ms非负。没有计时值就不产生P50/P95；同一原始预测重复评分应一致，重新运行计时不保证同值。

只给被测系统Public，不提供Private、逐题审核、主题映射、实验结果或完整ZIP。整体Public包括多个模拟用户；评测驱动器可按环境隔离存储，但不得把作者正确位置提供给检索器。
