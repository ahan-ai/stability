# 目的
本书介绍分布式服务稳定性建设的各个方面，覆盖了架构设计、监控告警、线上运维等方向，希望给读者提供一个比较全面、体系化的视角。对于软件架构师、初步入职场的工程师、SRE等，相信本书可以提供一定的价值。


# Part 1 概述
1. [稳定性概述](1-overview/README.md)
# Part 2 稳定性架构设计
在稳定性建设中，事前防御是至关重要的一环，所谓“防范于未然”。它着重于在系统设计和开发阶段采取措施，预防潜在的稳定性问题和故障的发生，以确保系统的可靠性和稳定性。同时通过各种自动化的故障测试和演练，提前识别风险。这也是稳定性建设最经济高效的方式。

事前防御的介绍是稳定性建设中篇幅最长的一部分。这一部分，我们会分享几十种常见的稳定性风险，并说明如何通过合理的设计尽可能规避这些风险。

2. [避免单点故障](2-preventive-arch/避免单点故障.md)
1. [备份核心数据](2-preventive-arch/备份.md)
1. [隔离](2-preventive-arch/隔离.md)
1. [删除保护](2-preventive-arch/删除保护.md)
1. [兼容性设计](2-preventive-arch/兼容性设计.md)
1. [流量控制](2-preventive-arch/流量控制.md)
1. [监控告警](2-preventive-arch/监控告警.md)
1. [容灾切换](2-preventive-arch/容灾切换.md)
1. [SOP](2-preventive-arch/SOP.md)
1. [应急指挥](2-preventive-arch/应急指挥.md)

# Part 3 监控&告警

# Part 4 测试

# Part 5 安全