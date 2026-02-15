"""
话术模板种子数据 - 100+条
"""

SALES_SCRIPT_TEMPLATES = [
    # ===== 首次接触话术 (20条) =====
    {
        "scenario": "first_contact",
        "customer_type": "technical",
        "script_content": "您好，我是XX公司的技术顾问。了解到贵司在寻找XXX解决方案，我们在该领域有成熟的技术架构和实施经验，方便和您深入探讨技术细节吗？",
        "tags": ["技术导向", "专业", "开场"],
        "success_rate": 78.5
    },
    {
        "scenario": "first_contact",
        "customer_type": "commercial",
        "script_content": "您好，我是XX公司的商务经理。贵司最近在XXX项目上有需求吗？我们可以为您提供性价比最优的解决方案，已帮助多家同行业客户实现降本增效。",
        "tags": ["商务导向", "性价比", "开场"],
        "success_rate": 82.3
    },
    {
        "scenario": "first_contact",
        "customer_type": "decision_maker",
        "script_content": "X总您好，我是XX公司的合作伙伴经理。看到贵司在XXX领域的战略布局，我们在该赛道已服务头部企业，希望能为贵司的业务增长提供支持。",
        "tags": ["决策层", "战略", "开场"],
        "success_rate": 85.7
    },
    {
        "scenario": "first_contact",
        "customer_type": "mixed",
        "script_content": "您好，我是XX公司的解决方案专家。针对贵司在XXX方面的挑战，我们有成熟的产品+服务体系，既能满足技术要求，又能控制总体成本，方便约时间详聊吗？",
        "tags": ["综合", "方案导向", "开场"],
        "success_rate": 80.1
    },
    {
        "scenario": "first_contact",
        "customer_type": "technical",
        "script_content": "您好，注意到贵司技术栈使用XXX，我们的产品在该架构下有深度优化，API对接简单，部署周期短，可以先安排技术交流吗？",
        "tags": ["技术兼容", "快速集成"],
        "success_rate": 76.8
    },
    {
        "scenario": "first_contact",
        "customer_type": "commercial",
        "script_content": "您好，我们最近推出针对XXX行业的促销方案，前3个月免费试用，帮助客户快速验证效果，贵司有兴趣了解吗？",
        "tags": ["促销", "低门槛"],
        "success_rate": 79.4
    },
    {
        "scenario": "first_contact",
        "customer_type": "decision_maker",
        "script_content": "X总，贵司在XXX领域的创新令人印象深刻。我们服务的XX企业也在做类似探索，他们通过我们的方案实现了XX%的效率提升，希望能分享给您。",
        "tags": ["标杆案例", "数据驱动"],
        "success_rate": 87.2
    },
    {
        "scenario": "first_contact",
        "customer_type": "technical",
        "script_content": "您好，我们的产品刚发布了新版本，针对XXX痛点做了重大升级，技术白皮书可以发给您参考，您看方便预约demo演示吗？",
        "tags": ["产品更新", "白皮书"],
        "success_rate": 74.6
    },
    {
        "scenario": "first_contact",
        "customer_type": "commercial",
        "script_content": "您好，了解到贵司正在评估XXX方案，我们的报价通常比同类产品低15-20%，且不降低服务质量，方便发送详细对比资料吗？",
        "tags": ["价格优势", "对比"],
        "success_rate": 81.5
    },
    {
        "scenario": "first_contact",
        "customer_type": "mixed",
        "script_content": "您好，我们在XXX行业有10年深耕经验，既有技术实力，又有成本优势。最近刚服务XX公司完成类似项目，可以分享案例给您参考。",
        "tags": ["行业经验", "案例"],
        "success_rate": 83.9
    },
    {
        "scenario": "first_contact",
        "customer_type": "technical",
        "script_content": "您好，我们的技术团队曾在XX公司工作，对XXX领域的技术挑战非常了解，可以为贵司提供定制化的技术方案。",
        "tags": ["团队背景", "定制化"],
        "success_rate": 77.3
    },
    {
        "scenario": "first_contact",
        "customer_type": "decision_maker",
        "script_content": "X总，贵司的XXX战略和我们的产品方向高度契合。我们可以提供从方案设计到落地实施的全流程支持，助力贵司战略目标达成。",
        "tags": ["战略契合", "全流程"],
        "success_rate": 86.4
    },
    {
        "scenario": "first_contact",
        "customer_type": "commercial",
        "script_content": "您好，我们有专门针对中小企业的轻量版方案，价格亲民，功能够用，已有XX家企业在用，可以先试用体验。",
        "tags": ["轻量版", "中小企业"],
        "success_rate": 75.8
    },
    {
        "scenario": "first_contact",
        "customer_type": "technical",
        "script_content": "您好，我们的产品支持私有化部署，数据完全在贵司内网，符合安全合规要求，技术架构灵活可扩展。",
        "tags": ["私有化", "安全"],
        "success_rate": 80.7
    },
    {
        "scenario": "first_contact",
        "customer_type": "mixed",
        "script_content": "您好，我们提供SaaS和私有化两种部署方式，可根据贵司实际需求选择，既能快速上线，又能保证数据安全。",
        "tags": ["灵活部署", "双模式"],
        "success_rate": 79.2
    },
    {
        "scenario": "first_contact",
        "customer_type": "decision_maker",
        "script_content": "X总，我们刚完成C轮融资，投资方包括XX基金，产品和服务会持续迭代升级，是可靠的长期合作伙伴。",
        "tags": ["融资背景", "可靠性"],
        "success_rate": 84.1
    },
    {
        "scenario": "first_contact",
        "customer_type": "commercial",
        "script_content": "您好，我们提供按需付费模式，用多少付多少，没有高额的前期投入，适合预算有限的项目。",
        "tags": ["按需付费", "灵活"],
        "success_rate": 78.9
    },
    {
        "scenario": "first_contact",
        "customer_type": "technical",
        "script_content": "您好，我们的产品开源了部分核心模块，社区活跃度高，技术透明度好，欢迎贵司技术团队评估。",
        "tags": ["开源", "社区"],
        "success_rate": 73.5
    },
    {
        "scenario": "first_contact",
        "customer_type": "mixed",
        "script_content": "您好，我们刚获得XXX行业认证，产品符合国家标准，服务过XX家500强企业，品质有保障。",
        "tags": ["认证", "标杆客户"],
        "success_rate": 82.6
    },
    {
        "scenario": "first_contact",
        "customer_type": "decision_maker",
        "script_content": "X总，看到贵司在XXX领域的快速发展，我们愿意提供战略级支持，包括技术赋能、资源对接等，共同成长。",
        "tags": ["战略合作", "生态"],
        "success_rate": 88.3
    },

    # ===== 需求挖掘话术 (20条) =====
    {
        "scenario": "needs_discovery",
        "customer_type": "technical",
        "script_content": "请问贵司目前在XXX方面遇到的最大技术挑战是什么？我们可以针对性地提供解决方案。",
        "tags": ["痛点挖掘", "技术"],
        "success_rate": 81.2
    },
    {
        "scenario": "needs_discovery",
        "customer_type": "commercial",
        "script_content": "您这边对XXX项目的预算范围大概是多少？我们可以在预算内给出最优方案。",
        "tags": ["预算", "方案"],
        "success_rate": 77.4
    },
    {
        "scenario": "needs_discovery",
        "customer_type": "decision_maker",
        "script_content": "X总，您希望通过XXX项目达成什么样的业务目标？我们可以围绕目标设计实施路径。",
        "tags": ["业务目标", "战略"],
        "success_rate": 85.8
    },
    {
        "scenario": "needs_discovery",
        "customer_type": "technical",
        "script_content": "贵司现有系统使用什么技术栈？我们的产品需要和哪些系统对接？",
        "tags": ["技术对接", "集成"],
        "success_rate": 79.6
    },
    {
        "scenario": "needs_discovery",
        "customer_type": "commercial",
        "script_content": "您这边预计什么时候启动项目？交付时间有硬性要求吗？",
        "tags": ["时间节点", "交付"],
        "success_rate": 76.3
    },
    {
        "scenario": "needs_discovery",
        "customer_type": "mixed",
        "script_content": "您觉得XXX方案最重要的3个要素是什么？技术、价格、服务，还是其他？",
        "tags": ["需求优先级", "综合"],
        "success_rate": 80.7
    },
    {
        "scenario": "needs_discovery",
        "customer_type": "technical",
        "script_content": "贵司对系统性能有什么具体指标要求？比如并发量、响应时间等。",
        "tags": ["性能指标", "技术要求"],
        "success_rate": 78.9
    },
    {
        "scenario": "needs_discovery",
        "customer_type": "decision_maker",
        "script_content": "除了当前需求，未来1-2年贵司在XXX方面还有什么规划？我们可以提前布局。",
        "tags": ["长期规划", "前瞻"],
        "success_rate": 84.2
    },
    {
        "scenario": "needs_discovery",
        "customer_type": "commercial",
        "script_content": "您这边决策流程是怎样的？需要几方审批？我们可以准备相应的材料。",
        "tags": ["决策流程", "准备"],
        "success_rate": 75.8
    },
    {
        "scenario": "needs_discovery",
        "customer_type": "technical",
        "script_content": "贵司对数据安全和隐私保护有什么特殊要求？我们会严格遵守。",
        "tags": ["安全合规", "隐私"],
        "success_rate": 82.1
    },
    {
        "scenario": "needs_discovery",
        "customer_type": "mixed",
        "script_content": "您之前有用过类似产品吗？体验如何？有哪些不满意的地方？",
        "tags": ["竞品对比", "痛点"],
        "success_rate": 79.4
    },
    {
        "scenario": "needs_discovery",
        "customer_type": "commercial",
        "script_content": "您这边是一次性采购，还是分期实施？我们可以灵活配合。",
        "tags": ["采购模式", "灵活"],
        "success_rate": 77.6
    },
    {
        "scenario": "needs_discovery",
        "customer_type": "technical",
        "script_content": "贵司有自己的开发团队吗？需要我们提供技术培训和支持吗？",
        "tags": ["技术支持", "培训"],
        "success_rate": 80.3
    },
    {
        "scenario": "needs_discovery",
        "customer_type": "decision_maker",
        "script_content": "X总，您希望项目ROI达到什么水平？多久能看到效果？",
        "tags": ["ROI", "效果"],
        "success_rate": 86.5
    },
    {
        "scenario": "needs_discovery",
        "customer_type": "mixed",
        "script_content": "您这边对售后服务有什么期望？我们提供7*24小时技术支持。",
        "tags": ["售后服务", "支持"],
        "success_rate": 78.7
    },
    {
        "scenario": "needs_discovery",
        "customer_type": "technical",
        "script_content": "贵司是否需要定制化开发？我们有专业的定制团队。",
        "tags": ["定制化", "开发"],
        "success_rate": 81.9
    },
    {
        "scenario": "needs_discovery",
        "customer_type": "commercial",
        "script_content": "您这边有参考的竞品报价吗？我们可以给出更有竞争力的方案。",
        "tags": ["竞品", "报价"],
        "success_rate": 76.2
    },
    {
        "scenario": "needs_discovery",
        "customer_type": "decision_maker",
        "script_content": "这个项目对贵司来说优先级如何？我们可以配合贵司的节奏推进。",
        "tags": ["优先级", "配合"],
        "success_rate": 83.4
    },
    {
        "scenario": "needs_discovery",
        "customer_type": "technical",
        "script_content": "贵司对产品的可扩展性有什么要求？未来业务量增长我们都能支持。",
        "tags": ["可扩展性", "未来"],
        "success_rate": 79.8
    },
    {
        "scenario": "needs_discovery",
        "customer_type": "mixed",
        "script_content": "除了产品本身，您还需要我们提供哪些配套服务？培训、运维、咨询？",
        "tags": ["配套服务", "综合"],
        "success_rate": 80.5
    },

    # ===== 方案讲解话术 (20条) =====
    {
        "scenario": "solution_presentation",
        "customer_type": "technical",
        "script_content": "我们的技术架构采用XXX设计，具有高可用、高性能、易扩展的特点。这张架构图展示了各模块之间的关系，您看有什么疑问吗？",
        "tags": ["架构", "技术细节"],
        "success_rate": 82.7
    },
    {
        "scenario": "solution_presentation",
        "customer_type": "commercial",
        "script_content": "我们的方案分为基础版、标准版、旗舰版三个套餐，价格从XX到XX不等，您可以根据实际需求选择，后期也能平滑升级。",
        "tags": ["套餐", "价格"],
        "success_rate": 79.3
    },
    {
        "scenario": "solution_presentation",
        "customer_type": "decision_maker",
        "script_content": "这个方案能帮助贵司实现XXX目标，预计ROI为XX，6个月即可回本。我们已有XX家标杆客户验证过效果。",
        "tags": ["ROI", "标杆"],
        "success_rate": 87.1
    },
    {
        "scenario": "solution_presentation",
        "customer_type": "technical",
        "script_content": "我们的API文档非常完善，支持RESTful和GraphQL两种接口，开发者友好，集成周期通常在1-2周。",
        "tags": ["API", "开发"],
        "success_rate": 80.9
    },
    {
        "scenario": "solution_presentation",
        "customer_type": "commercial",
        "script_content": "总体费用包括产品授权费、实施费、年度维保费三部分，第一年总投入XX万，后续每年维保费XX万。",
        "tags": ["费用构成", "透明"],
        "success_rate": 78.2
    },
    {
        "scenario": "solution_presentation",
        "customer_type": "mixed",
        "script_content": "整个实施分为4个阶段：需求确认、系统搭建、数据迁移、上线培训，总周期3个月，每个阶段都有明确的验收标准。",
        "tags": ["实施计划", "阶段"],
        "success_rate": 81.6
    },
    {
        "scenario": "solution_presentation",
        "customer_type": "technical",
        "script_content": "我们的系统支持Docker容器化部署，可以快速部署在Kubernetes集群上，运维成本低。",
        "tags": ["容器化", "K8s"],
        "success_rate": 79.4
    },
    {
        "scenario": "solution_presentation",
        "customer_type": "decision_maker",
        "script_content": "我们不仅提供产品，还会输出最佳实践和行业洞察，帮助贵司建立竞争优势。",
        "tags": ["最佳实践", "洞察"],
        "success_rate": 85.3
    },
    {
        "scenario": "solution_presentation",
        "customer_type": "commercial",
        "script_content": "我们提供30天免费试用，试用期内全功能开放，满意后再签约，零风险。",
        "tags": ["试用", "零风险"],
        "success_rate": 83.8
    },
    {
        "scenario": "solution_presentation",
        "customer_type": "technical",
        "script_content": "我们的产品通过了ISO27001、等保三级等认证，安全性有保障，这是认证证书。",
        "tags": ["认证", "安全"],
        "success_rate": 81.2
    },
    {
        "scenario": "solution_presentation",
        "customer_type": "mixed",
        "script_content": "我们的客户成功团队会全程跟进，从需求分析到上线运营，确保项目成功落地。",
        "tags": ["客户成功", "跟进"],
        "success_rate": 80.7
    },
    {
        "scenario": "solution_presentation",
        "customer_type": "decision_maker",
        "script_content": "这个方案已在XX行业头部企业落地，案例包括XX公司、XX公司，效果显著，可以安排客户互访。",
        "tags": ["行业案例", "互访"],
        "success_rate": 88.4
    },
    {
        "scenario": "solution_presentation",
        "customer_type": "technical",
        "script_content": "我们提供完整的SDK和代码示例，支持Java、Python、Go等主流语言，降低开发成本。",
        "tags": ["SDK", "多语言"],
        "success_rate": 79.8
    },
    {
        "scenario": "solution_presentation",
        "customer_type": "commercial",
        "script_content": "我们支持分期付款，首付XX%，验收合格后付XX%，尾款XX%，减轻现金流压力。",
        "tags": ["分期", "灵活"],
        "success_rate": 77.9
    },
    {
        "scenario": "solution_presentation",
        "customer_type": "mixed",
        "script_content": "我们的方案具有很好的扩展性，未来可以无缝接入更多功能模块，保护您的投资。",
        "tags": ["扩展性", "保值"],
        "success_rate": 82.3
    },
    {
        "scenario": "solution_presentation",
        "customer_type": "technical",
        "script_content": "系统性能方面，我们支持千万级并发，响应时间<100ms，这是压测报告供参考。",
        "tags": ["性能", "压测"],
        "success_rate": 80.1
    },
    {
        "scenario": "solution_presentation",
        "customer_type": "decision_maker",
        "script_content": "通过我们的方案，贵司可以降低XX%的运营成本，提升XX%的业务效率，这是详细的效益分析。",
        "tags": ["降本", "增效"],
        "success_rate": 86.7
    },
    {
        "scenario": "solution_presentation",
        "customer_type": "commercial",
        "script_content": "我们的价格比竞品A低15%，比竞品B低20%，但功能和服务不打折扣，这是对比表。",
        "tags": ["价格对比", "优势"],
        "success_rate": 78.5
    },
    {
        "scenario": "solution_presentation",
        "customer_type": "technical",
        "script_content": "我们支持灰度发布、A/B测试等高级功能，帮助贵司安全、平稳地推进业务创新。",
        "tags": ["灰度", "创新"],
        "success_rate": 79.2
    },
    {
        "scenario": "solution_presentation",
        "customer_type": "mixed",
        "script_content": "我们提供1年免费技术支持和产品升级，后续按年续费，费用仅为首次采购的20%。",
        "tags": ["免费支持", "续费"],
        "success_rate": 81.8
    },

    # ===== 价格谈判话术 (15条) =====
    {
        "scenario": "price_negotiation",
        "customer_type": "commercial",
        "script_content": "我们的报价已经是底价了，但考虑到是长期合作，可以赠送XX服务，价值XX万。",
        "tags": ["底价", "赠送"],
        "success_rate": 76.4
    },
    {
        "scenario": "price_negotiation",
        "customer_type": "commercial",
        "script_content": "如果您能在本月签约，我们可以额外提供5%的折扣，这是季度末特惠。",
        "tags": ["时间限定", "折扣"],
        "success_rate": 79.8
    },
    {
        "scenario": "price_negotiation",
        "customer_type": "decision_maker",
        "script_content": "X总，价格确实是考量因素，但更重要的是方案能否真正解决问题、带来价值。我们的ROI计算表明，投入回报比超过1:3。",
        "tags": ["价值", "ROI"],
        "success_rate": 84.2
    },
    {
        "scenario": "price_negotiation",
        "customer_type": "commercial",
        "script_content": "我们可以提供分期付款方案，降低一次性投入压力，同时保证服务质量。",
        "tags": ["分期", "灵活"],
        "success_rate": 77.6
    },
    {
        "scenario": "price_negotiation",
        "customer_type": "technical",
        "script_content": "虽然价格比某些竞品略高，但我们提供更完善的技术支持和更快的响应速度，这是隐性价值。",
        "tags": ["技术支持", "价值"],
        "success_rate": 78.3
    },
    {
        "scenario": "price_negotiation",
        "customer_type": "commercial",
        "script_content": "如果贵司能一次性签3年合同，我们可以给到20%的优惠，锁定长期价格。",
        "tags": ["长期", "优惠"],
        "success_rate": 80.5
    },
    {
        "scenario": "price_negotiation",
        "customer_type": "decision_maker",
        "script_content": "我们理解贵司的预算压力，可以先做POC验证价值，确认效果后再谈正式合作。",
        "tags": ["POC", "验证"],
        "success_rate": 82.7
    },
    {
        "scenario": "price_negotiation",
        "customer_type": "commercial",
        "script_content": "这个价格包含了产品、实施、培训、1年维保的全部费用，没有隐藏成本。",
        "tags": ["透明", "全包"],
        "success_rate": 76.9
    },
    {
        "scenario": "price_negotiation",
        "customer_type": "mixed",
        "script_content": "我们可以调整方案范围，去掉一些非核心功能，降低总价，满足您的预算。",
        "tags": ["调整范围", "降价"],
        "success_rate": 79.1
    },
    {
        "scenario": "price_negotiation",
        "customer_type": "commercial",
        "script_content": "如果您能推荐其他客户，我们可以提供渠道返点或折扣优惠。",
        "tags": ["推荐", "返点"],
        "success_rate": 75.8
    },
    {
        "scenario": "price_negotiation",
        "customer_type": "decision_maker",
        "script_content": "我们愿意将部分费用与项目效果挂钩，达成目标再付款，共担风险。",
        "tags": ["效果付费", "共担"],
        "success_rate": 85.6
    },
    {
        "scenario": "price_negotiation",
        "customer_type": "commercial",
        "script_content": "我们的价格是按照XXX标准定的，业内同等方案都在这个价位，可以提供市场调研报告。",
        "tags": ["市场价", "合理"],
        "success_rate": 77.2
    },
    {
        "scenario": "price_negotiation",
        "customer_type": "technical",
        "script_content": "如果贵司有开发能力，我们可以只提供核心组件，您自己集成，降低总成本。",
        "tags": ["部分采购", "降本"],
        "success_rate": 78.7
    },
    {
        "scenario": "price_negotiation",
        "customer_type": "mixed",
        "script_content": "我们理解价格是重要因素，但也请考虑实施风险、后续服务等综合成本，我们在这些方面有优势。",
        "tags": ["综合成本", "风险"],
        "success_rate": 80.4
    },
    {
        "scenario": "price_negotiation",
        "customer_type": "commercial",
        "script_content": "这次虽然利润很薄，但我们看重长期合作机会，希望通过优质服务赢得您的信任。",
        "tags": ["长期", "信任"],
        "success_rate": 81.3
    },

    # ===== 异议处理话术 (15条) =====
    {
        "scenario": "objection_handling",
        "customer_type": "commercial",
        "script_content": "您说价格高，我理解。但如果算上实施效率、后续维护成本，我们的总拥有成本（TCO）其实更低。我给您做个详细对比？",
        "tags": ["价格异议", "TCO"],
        "success_rate": 79.5
    },
    {
        "scenario": "objection_handling",
        "customer_type": "technical",
        "script_content": "您担心技术不成熟，可以理解。我们已有XX个生产环境案例，稳定运行XX年，可以安排技术团队交流或现场考察。",
        "tags": ["技术异议", "案例"],
        "success_rate": 82.1
    },
    {
        "scenario": "objection_handling",
        "customer_type": "commercial",
        "script_content": "您说竞品更便宜，确实。但他们的服务响应时间是48小时，我们是2小时，这个差异值不值这个价差？",
        "tags": ["竞品对比", "服务"],
        "success_rate": 77.8
    },
    {
        "scenario": "objection_handling",
        "customer_type": "decision_maker",
        "script_content": "您说暂时不需要，我理解。但市场变化很快，提前布局能抢占先机。我们可以先做小范围试点？",
        "tags": ["时机异议", "试点"],
        "success_rate": 80.6
    },
    {
        "scenario": "objection_handling",
        "customer_type": "technical",
        "script_content": "您担心和现有系统不兼容？我们有标准API和适配器，已和XX、XX系统成功对接，技术风险可控。",
        "tags": ["兼容性", "技术"],
        "success_rate": 81.4
    },
    {
        "scenario": "objection_handling",
        "customer_type": "commercial",
        "script_content": "您说预算不够，我们可以分阶段实施，先做核心模块，后续再扩展，分散投入。",
        "tags": ["预算", "分阶段"],
        "success_rate": 78.9
    },
    {
        "scenario": "objection_handling",
        "customer_type": "decision_maker",
        "script_content": "您说要再看看其他方案，完全支持。我们可以提供对比维度清单，帮您更客观地评估？",
        "tags": ["对比", "支持"],
        "success_rate": 83.2
    },
    {
        "scenario": "objection_handling",
        "customer_type": "technical",
        "script_content": "您担心数据安全？我们支持私有化部署，数据不出您的内网，且通过了等保三级认证。",
        "tags": ["安全", "私有化"],
        "success_rate": 84.7
    },
    {
        "scenario": "objection_handling",
        "customer_type": "commercial",
        "script_content": "您说之前用过类似产品体验不好？能具体说说哪些地方不满意吗？我们可以针对性改进。",
        "tags": ["历史问题", "改进"],
        "success_rate": 76.3
    },
    {
        "scenario": "objection_handling",
        "customer_type": "mixed",
        "script_content": "您担心实施周期太长？我们有快速部署方案，核心功能2周可上线，这是详细计划。",
        "tags": ["周期", "快速"],
        "success_rate": 79.7
    },
    {
        "scenario": "objection_handling",
        "customer_type": "decision_maker",
        "script_content": "您说决策链太长？我们可以协助准备决策材料，包括ROI分析、风险评估、对标报告等，加速流程。",
        "tags": ["决策", "材料"],
        "success_rate": 81.8
    },
    {
        "scenario": "objection_handling",
        "customer_type": "technical",
        "script_content": "您担心后续升级麻烦？我们支持热更新，不停机升级，对业务零影响。",
        "tags": ["升级", "零影响"],
        "success_rate": 80.2
    },
    {
        "scenario": "objection_handling",
        "customer_type": "commercial",
        "script_content": "您说公司规模小？恰恰相反，我们专注服务，响应更快，决策更灵活，这是优势。",
        "tags": ["公司规模", "优势"],
        "success_rate": 75.6
    },
    {
        "scenario": "objection_handling",
        "customer_type": "technical",
        "script_content": "您说功能不够？我们可以定制开发，或者集成第三方组件，满足您的特殊需求。",
        "tags": ["功能", "定制"],
        "success_rate": 78.4
    },
    {
        "scenario": "objection_handling",
        "customer_type": "mixed",
        "script_content": "您担心售后服务？我们提供7*24技术支持，SLA承诺2小时响应，1天解决，写进合同。",
        "tags": ["售后", "SLA"],
        "success_rate": 82.9
    },

    # ===== 成交话术 (10条) =====
    {
        "scenario": "closing",
        "customer_type": "commercial",
        "script_content": "那我们就这样定了？我现在安排商务准备合同，您看什么时候方便签？",
        "tags": ["成交", "推进"],
        "success_rate": 80.3
    },
    {
        "scenario": "closing",
        "customer_type": "decision_maker",
        "script_content": "X总，感谢您的信任！我们一定全力以赴，确保项目成功，让您满意。合同我明天送过来？",
        "tags": ["感谢", "承诺"],
        "success_rate": 85.7
    },
    {
        "scenario": "closing",
        "customer_type": "technical",
        "script_content": "技术方案确认了，我安排技术团队和您对接详细需求，同时走合同流程，您看可以吗？",
        "tags": ["技术确认", "双线推进"],
        "success_rate": 81.4
    },
    {
        "scenario": "closing",
        "customer_type": "commercial",
        "script_content": "您这边还有什么顾虑吗？如果没有，我们尽快启动，早启动早见效。",
        "tags": ["确认顾虑", "催促"],
        "success_rate": 78.6
    },
    {
        "scenario": "closing",
        "customer_type": "mixed",
        "script_content": "那我整理一份正式方案和报价，明天发给您审核，通过后我们就签约启动，可以吗？",
        "tags": ["正式方案", "流程"],
        "success_rate": 79.9
    },
    {
        "scenario": "closing",
        "customer_type": "decision_maker",
        "script_content": "X总，这个项目对贵司意义重大，我们会配置最强团队，确保按时高质量交付。",
        "tags": ["承诺", "保障"],
        "success_rate": 84.2
    },
    {
        "scenario": "closing",
        "customer_type": "commercial",
        "script_content": "如果您现在签约，我可以向公司申请额外的优惠或赠品，您看需要吗？",
        "tags": ["临门一脚", "优惠"],
        "success_rate": 77.5
    },
    {
        "scenario": "closing",
        "customer_type": "technical",
        "script_content": "我们的技术团队已做好准备，随时可以启动。您这边确定后，我们3天内完成环境搭建。",
        "tags": ["准备就绪", "效率"],
        "success_rate": 80.7
    },
    {
        "scenario": "closing",
        "customer_type": "mixed",
        "script_content": "非常高兴能和贵司合作！我们会把这个项目当作标杆来做，期待长期合作。",
        "tags": ["合作", "期待"],
        "success_rate": 82.1
    },
    {
        "scenario": "closing",
        "customer_type": "decision_maker",
        "script_content": "X总，我们已经讨论得很充分了，如果您同意，我安排法务走流程，下周就能签约。",
        "tags": ["推进", "时间点"],
        "success_rate": 83.8
    },
]

# 异议处理策略库（20+条）
OBJECTION_HANDLING_STRATEGIES = [
    {
        "objection_type": "价格太高",
        "strategy": "强调价值和ROI，提供TCO对比，突出服务和质量优势",
        "scripts": [
            "价格确实是考量因素，但更重要的是投入产出比。我们的方案能带来XX%的效率提升，6个月即可回本。",
            "如果只看单价，我们确实不是最便宜的。但算上实施成本、维护成本、机会成本，我们的总拥有成本最低。",
            "我们可以提供分期付款或效果付费方案，降低一次性投入压力。"
        ],
        "success_rate": 78.5
    },
    {
        "objection_type": "技术不成熟",
        "strategy": "提供成功案例、技术白皮书、试用机会，邀请技术交流或现场考察",
        "scripts": [
            "我们的技术已在XX家企业稳定运行XX年，可以安排客户互访或技术交流。",
            "我们提供30天免费POC，您可以充分验证技术可行性，零风险。",
            "这是我们的技术架构白皮书和性能测试报告，欢迎您的技术团队评估。"
        ],
        "success_rate": 82.3
    },
    {
        "objection_type": "竞品更好",
        "strategy": "承认竞品优势，突出自己的差异化价值，提供客观对比",
        "scripts": [
            "XX确实是优秀的产品，但我们在XXX方面有独特优势，更适合您的场景。",
            "我们可以提供客观的对比分析表，列出各方面的差异，帮您做决策。",
            "竞品强在XXX，我们强在XXX，关键看哪个更符合您的需求。"
        ],
        "success_rate": 76.8
    },
    {
        "objection_type": "暂时不需要",
        "strategy": "创造紧迫感，强调提前布局的价值，提供低门槛方案",
        "scripts": [
            "市场变化很快，竞争对手可能已在布局，提前准备能抢占先机。",
            "我们可以先做小范围试点，验证价值后再推广，风险可控。",
            "虽然暂时不急，但了解方案总是好的，我们可以先保持联系。"
        ],
        "success_rate": 74.2
    },
    {
        "objection_type": "预算不足",
        "strategy": "提供灵活付款方案，调整方案范围，强调长期收益",
        "scripts": [
            "我们支持分期付款，首付只需XX%，减轻现金流压力。",
            "可以先做核心模块，控制预算，后续再扩展。",
            "投资这个项目的回报远超成本，建议优先保障预算。"
        ],
        "success_rate": 79.6
    },
    {
        "objection_type": "决策周期长",
        "strategy": "协助准备决策材料，加速流程，提供限时优惠",
        "scripts": [
            "我们可以协助准备ROI分析、风险评估等决策材料，加速审批。",
            "如果能在本月签约，我们提供额外5%折扣，您看能否推动？",
            "我们理解流程需要时间，可以先签意向书锁定方案。"
        ],
        "success_rate": 77.4
    },
    {
        "objection_type": "兼容性问题",
        "strategy": "提供技术方案，展示集成案例，承诺技术支持",
        "scripts": [
            "我们有标准API和适配器，已和XX系统成功对接，技术风险可控。",
            "可以先做兼容性测试，确认可行后再推进。",
            "我们的技术团队会全程支持对接，确保顺利集成。"
        ],
        "success_rate": 81.7
    },
    {
        "objection_type": "数据安全担忧",
        "strategy": "强调安全措施，提供认证证书，支持私有化部署",
        "scripts": [
            "我们通过了ISO27001、等保三级认证，安全性有保障。",
            "支持私有化部署，数据完全在您的内网，不出本地。",
            "我们签署严格的保密协议，确保数据安全。"
        ],
        "success_rate": 84.3
    },
    {
        "objection_type": "实施周期长",
        "strategy": "提供快速部署方案，分阶段实施，展示实施计划",
        "scripts": [
            "我们有快速部署方案，核心功能2周可上线。",
            "可以分阶段实施，先上关键模块，快速见效。",
            "这是详细的实施计划，每个阶段都有明确时间节点。"
        ],
        "success_rate": 78.9
    },
    {
        "objection_type": "售后服务担心",
        "strategy": "承诺SLA，展示服务团队，提供案例证明",
        "scripts": [
            "我们提供7*24技术支持，SLA承诺2小时响应，写进合同。",
            "我们有专业的客户成功团队，全程跟进您的使用情况。",
            "现有客户对我们的服务满意度达95%，可以提供推荐信。"
        ],
        "success_rate": 83.1
    },
    {
        "objection_type": "功能不满足",
        "strategy": "提供定制化服务，集成第三方，承诺持续迭代",
        "scripts": [
            "我们可以定制开发，满足您的特殊需求。",
            "可以集成第三方组件，补充功能短板。",
            "产品持续迭代，您的需求会纳入规划。"
        ],
        "success_rate": 76.5
    },
    {
        "objection_type": "公司规模小",
        "strategy": "突出灵活性，展示融资背景，强调专注度",
        "scripts": [
            "我们规模虽小，但更灵活，响应更快，决策更高效。",
            "我们刚完成C轮融资，有充足资金支持产品研发。",
            "我们专注在这个领域，比大公司更懂行业。"
        ],
        "success_rate": 75.3
    },
    {
        "objection_type": "之前有不好体验",
        "strategy": "了解具体问题，承诺改进，提供试用验证",
        "scripts": [
            "能具体说说之前哪里不满意吗？我们针对性改进。",
            "我们和之前的产品不同，可以先试用对比。",
            "我们会吸取教训，避免重复问题。"
        ],
        "success_rate": 74.8
    },
    {
        "objection_type": "需要领导审批",
        "strategy": "协助准备材料，提供决策依据，主动对接领导",
        "scripts": [
            "我可以准备一份详细的方案和ROI分析，帮您汇报。",
            "如果方便，我可以直接向您的领导讲解方案。",
            "我们有现成的决策模板，可以直接使用。"
        ],
        "success_rate": 80.2
    },
    {
        "objection_type": "还要对比其他方案",
        "strategy": "支持对比，提供对比维度，保持跟进",
        "scripts": [
            "完全理解，货比三家是应该的。我们可以提供对比清单帮您评估。",
            "对比时可以关注XXX这几个维度，更客观全面。",
            "对比后如有疑问随时联系我，我会详细解答。"
        ],
        "success_rate": 79.7
    },
    {
        "objection_type": "团队使用习惯",
        "strategy": "提供培训，强调易用性，展示学习曲线",
        "scripts": [
            "我们提供完整的培训和文档,学习曲线很平缓。",
            "产品界面友好，大多数功能开箱即用。",
            "我们会安排专人驻场指导，确保团队顺利上手。"
        ],
        "success_rate": 77.6
    },
    {
        "objection_type": "扩展性问题",
        "strategy": "展示架构设计，说明扩展能力，提供案例",
        "scripts": [
            "我们的架构设计支持水平扩展，业务量增长10倍也没问题。",
            "已有客户从日活1万增长到100万，系统稳定运行。",
            "支持模块化扩展，未来可以灵活添加新功能。"
        ],
        "success_rate": 81.4
    },
    {
        "objection_type": "行业经验不足",
        "strategy": "展示行业案例，突出学习能力，提供顾问支持",
        "scripts": [
            "我们虽然是新进入者，但已服务XX家行业客户。",
            "我们的团队有XX年行业经验，快速理解需求。",
            "我们可以引入行业专家作为顾问，确保方案合理。"
        ],
        "success_rate": 73.9
    },
    {
        "objection_type": "合同条款问题",
        "strategy": "灵活调整，寻求共识，必要时升级谈判",
        "scripts": [
            "合同条款可以协商，我们的目标是双赢。",
            "这个条款的考虑是XXX，我们可以调整表述。",
            "如果这个条款是障碍，我请示领导看能否调整。"
        ],
        "success_rate": 78.3
    },
    {
        "objection_type": "ROI不明确",
        "strategy": "提供计算模型，展示标杆案例，承诺效果跟踪",
        "scripts": [
            "这是我们的ROI计算模型，可以根据您的数据测算。",
            "XX客户通过我们的方案，6个月节省了XX万成本。",
            "我们可以设置效果指标，定期跟踪评估ROI。"
        ],
        "success_rate": 82.8
    },
]


def get_all_templates():
    """获取所有模板"""
    return SALES_SCRIPT_TEMPLATES


def get_all_strategies():
    """获取所有异议策略"""
    return OBJECTION_HANDLING_STRATEGIES


if __name__ == "__main__":
    print(f"共有 {len(SALES_SCRIPT_TEMPLATES)} 条话术模板")
    print(f"共有 {len(OBJECTION_HANDLING_STRATEGIES)} 条异议处理策略")
    
    # 统计各场景数量
    from collections import Counter
    scenario_counts = Counter([t["scenario"] for t in SALES_SCRIPT_TEMPLATES])
    print("\n各场景话术数量：")
    for scenario, count in scenario_counts.items():
        print(f"  {scenario}: {count}条")
