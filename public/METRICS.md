# 指标与固定分母

## 对象

一轮是原始user消息与紧随的assistant回复。对正常召回题，E是作者登记的合法证据单位；单位内全部片段为AND；S是一组充分集合，每集合内单位为AND，不同集合为OR。G为E涉及的原始轮次并集；P为实际注入过非空片段的轮次集合。片段采用未经归一化的Unicode码点位置。

作者的新问题义务与历史证据要求分别记录。隐式结构题登记的是历史关系及条件能否支持本次关联，不把新情境中的事实伪造成历史原话，也不把旧聊天当作新问题解答唯一不可缺少的外部证据。

## 注入层

- RelevantRoundPrecision = |P∩G|/|P|；P空时为0。
- RelevantRoundRecall = |P∩G|/|G|。
- RelevantRoundF1 = 2PR/(P+R)，P+R=0时为0。先逐题计算再宏平均。
- BestPathRoundRecall = max_{s∈S} |P∩rounds(s)|/|rounds(s)|，它不等同普通Recall。
- SufficiencySuccess = 1 当且仅当至少一套s的每个证据单位的全部原文区间均被覆盖；仅命中正确轮次不足。
- SourceClaimRecall = 已被完整证据单位支持的登记历史要求数量/全部登记历史要求数量。它不是新问题推理正确率。
- SpanPurity = 每个注入出现与全部合法证据区间的字符交集之和/所有实际注入出现的字符长度之和。分母空时0，不是token精确率。
- DuplicateCodepoints = 实际注入总字符数−合并同一来源重叠区间后的字符数。不同消息正文相同仍是不同来源。
- PathCoverageRate = 被完整覆盖的已登记充分集合数量/全部登记集合数量。路径枚举数量不均，作为诊断，不作主排名依据。
- InjectionTokens：实际serialize.py规范文本的o200k_base encode_ordinary token数，包含规范头与分隔。原生系统另有不同文本格式时应另报成本，不能用规范成本冒充原生文本成本。
- MinRegisteredSufficientTokens：逐一对已登记路径合并同源相邻/重叠区间、按原始消息先后序列化后取最小token数。它不是所有可能证据、额外拼接方式或原文语义压缩的理论最小值。
- RelativeOverhead = InjectionTokens/MinRegisteredSufficientTokens−1，仅在本次实际注入充分且参考成本已计算时报告；否则null。是成本相对量，不替代充分性。

## 候选层

对前K个返回的完整问答轮计算普通P/R/F1、BestPathRoundRecall和SufficiencySuccess，K=1/3/5/10/20/50。候选不足K时使用实际长度，不虚补。CandidateRecall@K指普通RelevantRoundRecall；CandidateBestPathRecall@K与CandidateSufficiency@K另列。完整候选层同理。排序基线返回整个小历史池时，完整候选充分率100%可能是平凡结果，不能当作精确定位能力。

## 动作、分母和错误

正常召回题有证据指标。歧义或字段缺失题的P/R/F1与证据充分率为null，不套用任意唯一目标。所有题另报ActionAccuracy = 预测action与登记action相同的指示量。当前三道澄清题和一道字段缺失题样本量极小，不推断普遍的澄清/拒答能力。

省略一个可选层该层不进入分母；显式空输出是零；整道题未返回则候选与注入按空输出记零，动作错。输入非法只影响该层，合法候选不因错误注入被清零，合法注入不因候选重复被清零。文本错误不会被修正后偷偷计分。显式选择的预算附录可令超预算注入无效，主评分没有此上限。

每个指标同时给出mean和denominator，分组按集合、召回类型、动作及历史内容标签。历史内容标签T01—T10不表示本次检索线索类型；difficulty仍为UNDEFINED，不反推难度。已发现来源结构错误按题排除，并报告requested/scored/excluded及原因，不把数据错误算成系统失败。

## 不确定性和延迟

主候选Sufficiency@3与注入Sufficiency提供95%环境簇百分位bootstrap，1000次、固定seed=20261019；以模拟用户环境整簇有放回抽样，按抽中题数计算宏均值。空层为null。不把各题当独立用户；区间以当前作者Gold为条件，不衡量Gold语义正确的概率。

latency_ms仅在实际提供合法测量时汇总，P50/P95使用nearest-rank；不补估未知耗时、费用或置信度。baseline runtime.json说明实际测量范围。重复评分不重新测量已有latency_ms。

## 准确性边界

评分不调用LLM裁判，只检查原始位置及已登记的关系支持。它能证明输出覆盖了这份标注，不能证明标注穷尽一切合法语义替代。历史原文库存继承自第六阶段；本次选择和绑定到新查询、重新枚举集合，旧语义审核不自动继承。
