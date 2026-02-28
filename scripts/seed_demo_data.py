#!/usr/bin/env python3
"""
演示数据种子脚本 - 金凯博自动化测试
覆盖全业务链: 组织→客户→销售→项目→采购→生产→发货→售后→财务

用法: python scripts/seed_demo_data.py
清除: python scripts/clear_demo_data.py
"""
import sqlite3, os, sys
import bcrypt
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "app.db")

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF")
    c = conn.cursor()
    now = datetime.now().isoformat()
    pw = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode()

    # 1. 部门
    print("创建部门...")
    for did,code,name in [(1,'SALES','销售部'),(2,'PM','项目管理部'),(3,'RD','研发部'),(4,'PROD','生产部'),(5,'SERVICE','客服部'),(6,'PURCHASE','采购部'),(7,'FINANCE','财务部'),(8,'EXEC','总经办')]:
        c.execute("INSERT OR REPLACE INTO departments (id,dept_code,dept_name,level,sort_order,is_active,created_at,updated_at) VALUES (?,?,?,1,?,1,?,?)", (did,code,name,did,now,now))

    # 2. 员工+用户
    print("创建员工和用户...")
    dm = {'总经办':8,'销售部':1,'项目管理部':2,'研发部':3,'生产部':4,'客服部':5,'采购部':6,'财务部':7}
    for eid,ec,name,dept,role,un in [(2,'E002','郑汝才','总经办','常务副总','zhengrc'),(3,'E003','骆奕兴','总经办','副总经理','luoyx'),(4,'E004','符凌维','总经办','副总经理(董秘)','fulw'),(5,'E005','宋魁','销售部','营销总监','songk'),(6,'E006','郑琴','销售部','销售经理','zhengq'),(7,'E007','姚洪','销售部','销售工程师','yaoh'),(8,'E008','常雄','生产部','PMC主管','changx'),(9,'E009','高勇','生产部','生产部经理','gaoy'),(10,'E010','陈亮','项目管理部','项目管理部总监','chenl'),(11,'E011','谭章斌','项目管理部','项目经理','tanzb'),(12,'E012','于振华','研发部','经理','yuzh'),(13,'E013','王俊','研发部','经理','wangj'),(14,'E014','王志红','客服部','客服主管','wangzh'),(15,'E015','李明','采购部','采购主管','lim'),(16,'E016','张华','财务部','财务主管','zhangh'),(17,'E017','刘强','生产部','车间主任','liuq'),(18,'E018','赵敏','销售部','销售助理','zhaom'),(19,'E019','周伟','研发部','软件工程师','zhouw'),(20,'E020','吴芳','客服部','客服工程师','wuf')]:
        c.execute("INSERT OR REPLACE INTO employees (id,employee_code,name,department,role,is_active,created_at,updated_at) VALUES (?,?,?,?,?,1,?,?)", (eid,ec,name,dept,role,now,now))
        c.execute("INSERT OR REPLACE INTO users (id,username,password_hash,employee_id,real_name,department,position,department_id,is_active,is_superuser,solution_credits,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,1,0,0,?,?)", (eid,un,pw,eid,name,dept,role,dm.get(dept,1),now,now))

    # 3. 客户
    print("创建客户...")
    for cid,code,name,short,ind,scale,addr,ct,ph,email,lv,rev,ow in [(1,'CUST001','比亚迪股份有限公司','比亚迪','新能源汽车','large','深圳市坪山区比亚迪路3009号','张伟','13800001001','zhangwei@byd.com','A',5000000,5),(2,'CUST002','宁德时代新能源科技','宁德时代','新能源电池','large','福建省宁德市蕉城区漳湾镇','李刚','13800001002','ligang@catl.com','A',8000000,6),(3,'CUST003','小米科技有限公司','小米','消费电子','large','北京市海淀区清河中街68号','王芳','13800001003','wangfang@xiaomi.com','B',3000000,7),(4,'CUST004','华为技术有限公司','华为','通信设备','large','深圳市龙岗区坂田华为基地','赵明','13800001004','zhaoming@huawei.com','A',10000000,5),(5,'CUST005','OPPO广东移动通信','OPPO','消费电子','large','广东省东莞市长安镇','陈静','13800001005','chenjing@oppo.com','B',2000000,6),(6,'CUST006','立讯精密工业','立讯精密','精密制造','large','广东省东莞市黄江镇','刘峰','13800001006','liufeng@luxshare.com','A',6000000,7),(7,'CUST007','富士康科技集团','富士康','代工制造','large','深圳市龙华区富士康科技园','孙磊','13800001007','sunlei@foxconn.com','B',4000000,5),(8,'CUST008','深圳比克电池','比克电池','新能源电池','medium','深圳市龙岗区宝龙工业区','周洁','13800001008','zhoujie@bak.com.cn','C',1500000,6)]:
        c.execute("INSERT OR REPLACE INTO customers (id,customer_code,customer_name,short_name,industry,scale,address,contact_person,contact_phone,contact_email,customer_level,annual_revenue,status,customer_type,credit_level,payment_terms,sales_owner_id,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,'ACTIVE','enterprise','GOOD','NET30',?,?,?)", (cid,code,name,short,ind,scale,addr,ct,ph,email,lv,rev,ow,now,now))

    # 4. 线索
    print("创建线索...")
    for lid,code,cn,ind,ct,ph,summ,st,sc,ow in [(1,'LD2025001','比亚迪','新能源汽车','张伟','13800001001','ICT在线测试设备需求','WON',95,5),(2,'LD2025002','宁德时代','新能源电池','李刚','13800001002','电池包EOL下线检测','WON',90,6),(3,'LD2025003','小米','消费电子','王芳','13800001003','手机主板FCT功能测试','NEGOTIATION',70,7),(4,'LD2025004','华为','通信设备','赵明','13800001004','5G模块老化测试系统','WON',88,5),(5,'LD2025005','OPPO','消费电子','陈静','13800001005','充电器FCT测试设备','QUALIFIED',60,6),(6,'LD2025006','立讯精密','精密制造','刘峰','13800001006','连接器视觉检测系统','WON',92,7),(7,'LD2025007','富士康','代工制造','孙磊','13800001007','AirPods烧录测试一体机','PROPOSAL',55,5),(8,'LD2025008','比克电池','新能源电池','周洁','13800001008','电芯分容老化柜','INITIAL',30,6),(9,'LD2026001','比亚迪','新能源汽车','张伟','13800001001','刀片电池包检测','QUALIFIED',65,7),(10,'LD2026002','宁德时代','新能源电池','李刚','13800001002','储能系统集成测试','INITIAL',25,5)]:
        c.execute("INSERT OR REPLACE INTO leads (id,lead_code,customer_name,industry,contact_name,contact_phone,demand_summary,status,source,owner_id,priority_score,health_status,health_score,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,'referral',?,?,'GOOD',?,?,?)", (lid,code,cn,ind,ct,ph,summ,st,ow,sc,sc,now,now))

    # 5. 商机
    print("创建商机...")
    for oid,code,lid,cid,name,et,stage,prob,amt,margin,close,ow in [(1,'OPP2025001',1,1,'比亚迪ICT在线测试设备','ICT','WON',95,2800000,35,'2025-09-15',5),(2,'OPP2025002',2,2,'宁德时代EOL检测系统','EOL','WON',90,4500000,30,'2025-10-20',6),(3,'OPP2025003',3,3,'小米手机FCT测试设备','FCT','NEGOTIATION',70,1800000,40,'2026-03-30',7),(4,'OPP2025004',4,4,'华为5G模块老化系统','AGING','WON',88,3500000,32,'2025-11-30',5),(5,'OPP2025005',5,5,'OPPO充电器FCT设备','FCT','PROPOSAL',60,1200000,38,'2026-04-15',6),(6,'OPP2025006',6,6,'立讯连接器视觉检测','VISION','WON',92,3200000,33,'2025-12-15',7),(7,'OPP2025007',7,7,'富士康烧录测试一体机','BURN','PROPOSAL',55,2100000,36,'2026-05-30',5),(8,'OPP2026001',9,1,'比亚迪刀片电池检测','EOL','DISCOVERY',40,5000000,28,'2026-06-30',6)]:
        c.execute("INSERT OR REPLACE INTO opportunities (id,opp_code,lead_id,customer_id,opp_name,equipment_type,stage,probability,est_amount,est_margin,expected_close_date,owner_id,risk_level,health_status,health_score,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,'LOW','GOOD',?,?,?)", (oid,code,lid,cid,name,et,stage,prob,amt,margin,close,ow,prob,now,now))

    # 6. 报价
    print("创建报价...")
    for qid,code,oid,cid,st,v,ow in [(1,'QT2025001',1,1,'APPROVED','2025-12-31',5),(2,'QT2025002',2,2,'APPROVED','2025-12-31',6),(3,'QT2025003',3,3,'PENDING','2026-06-30',7),(4,'QT2025004',4,4,'APPROVED','2025-12-31',5),(5,'QT2025005',5,5,'DRAFT','2026-06-30',6),(6,'QT2025006',6,6,'APPROVED','2026-03-31',7)]:
        c.execute("INSERT OR REPLACE INTO quotes (id,quote_code,opportunity_id,customer_id,status,valid_until,owner_id,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?)", (qid,code,oid,cid,st,v,ow,now,now))

    # 7. 合同
    print("创建合同...")
    for cid,code,name,oid,qid,custid,total,recv,unrecv,sign,eff,exp,ow in [(1,'HT2025001','比亚迪ICT测试设备采购合同',1,1,1,2800000,1400000,1400000,'2025-08-15','2025-08-15','2026-08-15',5),(2,'HT2025002','宁德时代EOL检测系统合同',2,2,2,4500000,2700000,1800000,'2025-09-20','2025-09-20','2026-09-20',6),(3,'HT2025003','华为老化测试系统合同',4,4,4,3500000,1750000,1750000,'2025-10-30','2025-10-30','2026-10-30',5),(4,'HT2025004','立讯视觉检测系统合同',6,6,6,3200000,1920000,1280000,'2025-11-15','2025-11-15','2026-11-15',7),(5,'HT2026001','小米FCT测试设备合同',3,3,3,1800000,0,1800000,'2026-01-10','2026-01-10','2026-07-10',7)]:
        c.execute("INSERT OR REPLACE INTO contracts (id,contract_code,contract_name,contract_type,opportunity_id,quote_id,customer_id,total_amount,received_amount,unreceived_amount,signing_date,effective_date,expiry_date,status,sales_owner_id,created_at,updated_at) VALUES (?,?,?,'SALES',?,?,?,?,?,?,?,?,?,'ACTIVE',?,?,?)", (cid,code,name,oid,qid,custid,total,recv,unrecv,sign,eff,exp,ow,now,now))

    # 8. 项目
    print("创建项目...")
    for pid,code,name,short,cid,cname,pt,stage,st,prog,start,end,camt,budget,cost,pm,pmn,cno in [(1,'PJ2025001','比亚迪ICT在线测试设备','比亚迪ICT',1,'比亚迪股份有限公司','ICT','execution','ACTIVE',75,'2025-09-01','2026-03-01',2800000,2500000,1875000,10,'陈亮','HT2025001'),(2,'PJ2025002','宁德时代EOL检测系统','宁德EOL',2,'宁德时代新能源科技','EOL','execution','ACTIVE',60,'2025-10-15','2026-04-15',4500000,4000000,2400000,10,'陈亮','HT2025002'),(3,'PJ2025003','华为5G老化测试系统','华为老化',4,'华为技术有限公司','AGING','testing','ACTIVE',90,'2025-11-01','2026-02-28',3500000,3200000,2880000,11,'谭章斌','HT2025003'),(4,'PJ2025004','立讯连接器视觉检测','立讯视觉',6,'立讯精密工业','VISION','design','ACTIVE',35,'2025-12-01','2026-06-01',3200000,2800000,980000,11,'谭章斌','HT2025004'),(5,'PJ2026001','小米手机FCT测试设备','小米FCT',3,'小米科技有限公司','FCT','planning','ACTIVE',10,'2026-02-01','2026-07-30',1800000,1600000,160000,10,'陈亮','HT2026001')]:
        c.execute("INSERT OR REPLACE INTO projects (id,project_code,project_name,short_name,customer_id,customer_name,project_type,product_category,stage,status,health,progress_pct,planned_start_date,planned_end_date,contract_amount,budget_amount,actual_cost,pm_id,pm_name,contract_no,priority,is_active,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,'GOOD',?,?,?,?,?,?,?,?,?,'HIGH',1,?,?)", (pid,code,name,short,cid,cname,pt,pt,stage,st,prog,start,end,camt,budget,cost,pm,pmn,cno,now,now))

    # 9. 物料
    print("创建物料...")
    for mid,code,name,unit,price in [(1,'MAT001','PCB测试主板','块',2500),(2,'MAT002','三菱PLC FX5U','台',8500),(3,'MAT003','伺服电机 750W','台',3200),(4,'MAT004','SMC气缸','个',450),(5,'MAT005','基恩士激光传感器','个',6800),(6,'MAT006','欧姆龙继电器','个',85),(7,'MAT007','铝型材 4040','米',65),(8,'MAT008','威纶触摸屏','台',2800),(9,'MAT009','海康工业相机','台',4500),(10,'MAT010','测试治具针床','套',15000),(11,'MAT011','线缆屏蔽','米',12),(12,'MAT012','断路器 3P','个',180),(13,'MAT013','开关电源 24V','台',350),(14,'MAT014','老化负载电阻','个',120),(15,'MAT015','烧录座 QFN48','个',850),(16,'MAT016','步进驱动器','台',680),(17,'MAT017','光纤传感器','个',520),(18,'MAT018','导轨 MGN12H','套',280),(19,'MAT019','电磁阀 5/2','个',320),(20,'MAT020','工控机 i7','台',7500)]:
        c.execute("INSERT OR REPLACE INTO materials (id,material_code,material_name,unit,standard_price,source_type,last_price,safety_stock,current_stock,lead_time_days,is_key_material,is_active,created_at,updated_at) VALUES (?,?,?,?,?,"PURCHASE",?,10,0,7,0,1,?,?)", (mid,code,name,unit,price,price,now,now))

    # 10. 采购订单
    print("创建采购订单...")
    for poid,code,proj,sup,st,amt,dt in [(1,'PO2025001',1,1,'RECEIVED',125000,'2025-09-10'),(2,'PO2025002',2,2,'RECEIVED',340000,'2025-10-20'),(3,'PO2025003',3,3,'RECEIVED',96000,'2025-11-05'),(4,'PO2025004',1,4,'RECEIVED',170000,'2025-11-20'),(5,'PO2025005',2,1,'SHIPPED',85000,'2025-12-10'),(6,'PO2025006',4,5,'APPROVED',204000,'2026-01-15'),(7,'PO2026001',5,2,'DRAFT',68000,'2026-02-01'),(8,'PO2025007',3,4,'RECEIVED',135000,'2025-10-01'),(9,'PO2025008',1,3,'RECEIVED',192000,'2025-09-25'),(10,'PO2026002',4,1,'PENDING',225000,'2026-02-10')]:
        c.execute("INSERT OR REPLACE INTO purchase_orders (id,order_no,project_id,supplier_id,status,total_amount,order_date,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?)", (poid,code,proj,sup,st,amt,dt,now,now))

    # 11. 车间+工人
    print("创建车间和工人...")
    for wid,code,name,wtype,loc in [(1,'WS01','装配一车间','ASSEMBLY','一楼东区'),(2,'WS02','装配二车间','ASSEMBLY','一楼西区'),(3,'WS03','调试车间','TESTING','二楼')]:
        c.execute("INSERT OR REPLACE INTO workshop (id,workshop_code,workshop_name,workshop_type,location,is_active,created_at,updated_at) VALUES (?,?,?,?,?,1,?,?)", (wid,code,name,wtype,loc,now,now))
    for wid,wno,name,ws,pos in [(1,'W001','张三',1,'装配工'),(2,'W002','李四',1,'装配工'),(3,'W003','王五',1,'电气工'),(4,'W004','赵六',2,'装配工'),(5,'W005','钱七',2,'焊接工'),(6,'W006','孙八',2,'电气工'),(7,'W007','周九',3,'调试工程师'),(8,'W008','吴十',3,'调试工程师'),(9,'W009','郑十一',1,'装配组长'),(10,'W010','冯十二',3,'调试组长')]:
        c.execute("INSERT OR REPLACE INTO worker (id,worker_no,worker_name,workshop_id,position,status,is_active,created_at,updated_at) VALUES (?,?,?,?,?,'ACTIVE',1,?,?)", (wid,wno,name,ws,pos,now,now))

    # 12. 生产计划+工单
    print("创建生产计划和工单...")
    for ppid,code,name,proj,ws,start,end,st,prog in [(1,'PP2025001','比亚迪ICT设备生产',1,1,'2025-10-01','2026-01-31','IN_PROGRESS',70),(2,'PP2025002','宁德EOL系统生产',2,2,'2025-11-01','2026-03-15','IN_PROGRESS',50),(3,'PP2025003','华为老化系统生产',3,1,'2025-12-01','2026-02-15','COMPLETED',100),(4,'PP2025004','立讯视觉检测生产',4,2,'2026-01-15','2026-05-01','PLANNED',0),(5,'PP2026001','小米FCT设备生产',5,1,'2026-03-01','2026-06-30','DRAFT',0)]:
        c.execute("INSERT OR REPLACE INTO production_plan (id,plan_no,plan_name,plan_type,project_id,workshop_id,plan_start_date,plan_end_date,status,progress,created_at,updated_at) VALUES (?,?,?,'STANDARD',?,?,?,?,?,?,?,?)", (ppid,code,name,proj,ws,start,end,st,prog,now,now))
    for woid,code,name,plan,proj,ws,st,prog in [(1,'WO2025001','机架组装',1,1,1,'COMPLETED',100),(2,'WO2025002','电气布线',1,1,1,'IN_PROGRESS',70),(3,'WO2025003','框架焊接',2,2,2,'IN_PROGRESS',50),(4,'WO2025004','传感器安装',2,2,2,'PLANNED',0),(5,'WO2025005','柜体组装',3,3,1,'COMPLETED',100),(6,'WO2025006','负载安装',3,3,1,'COMPLETED',100),(7,'WO2025007','系统调试',3,3,3,'COMPLETED',100),(8,'WO2026001','光学平台组装',4,4,2,'PLANNED',0)]:
        c.execute("INSERT OR REPLACE INTO work_order (id,work_order_no,task_name,task_type,production_plan_id,project_id,workshop_id,status,priority,progress,created_at,updated_at) VALUES (?,?,?,'ASSEMBLY',?,?,?,?,'NORMAL',?,?,?)", (woid,code,name,plan,proj,ws,st,prog,now,now))

    # 13. 发货
    print("创建发货单...")
    for doid,code,oid,proj,cid,cn,st,dt,addr in [(1,'DO2025001',1,3,4,'华为技术有限公司','DELIVERED','2026-02-10','深圳市龙岗区坂田华为基地'),(2,'DO2025002',2,1,1,'比亚迪股份有限公司','SHIPPED','2026-02-20','深圳市坪山区比亚迪路3009号'),(3,'DO2026001',3,2,2,'宁德时代新能源科技','PENDING','2026-03-15','福建省宁德市蕉城区漳湾镇')]:
        c.execute("INSERT OR REPLACE INTO delivery_orders (id,delivery_no,order_id,project_id,customer_id,customer_name,delivery_status,delivery_date,receiver_address,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (doid,code,oid,proj,cid,cn,st,dt,addr,now,now))

    # 14. 服务工单
    print("创建服务工单...")
    for tid,code,proj,cid,pt,desc,st,urg in [(1,'ST2025001',3,4,'HARDWARE','华为老化系统温控异常','CLOSED','HIGH'),(2,'ST2025002',1,1,'HARDWARE','比亚迪ICT测试点位偏移','IN_PROGRESS','URGENT'),(3,'ST2025003',2,2,'NETWORK','宁德EOL通信故障','PENDING','MEDIUM'),(4,'ST2026001',4,6,'HARDWARE','立讯视觉光源闪烁','ASSIGNED','HIGH'),(5,'ST2026002',5,1,'SOFTWARE','比亚迪设备软件升级','PENDING','LOW'),(6,'ST2026003',3,4,'HARDWARE','华为老化柜风扇异响','CLOSED','MEDIUM'),(7,'ST2026004',2,2,'HARDWARE','宁德EOL传感器更换','IN_PROGRESS','HIGH'),(8,'ST2026005',5,3,'SOFTWARE','小米FCT治具调试','PENDING','NORMAL')]:
        c.execute("INSERT OR REPLACE INTO service_tickets (id,ticket_no,project_id,customer_id,problem_type,problem_desc,status,urgency,reported_by,reported_time,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,'客户',?,?,?)", (tid,code,proj,cid,pt,desc,st,urg,now,now,now))

    # 15. 发票+回款
    print("创建发票和回款...")
    for iid,code,ct,proj,amt,st,dt in [(1,'INV2025001',1,1,1400000,'PAID','2025-09-30'),(2,'INV2025002',2,2,2250000,'PAID','2025-11-15'),(3,'INV2025003',3,3,1750000,'PAID','2025-12-20'),(4,'INV2025004',2,2,450000,'ISSUED','2026-01-10'),(5,'INV2026001',4,4,1920000,'ISSUED','2026-02-01')]:
        c.execute("INSERT OR REPLACE INTO invoices (id,invoice_code,contract_id,project_id,amount,total_amount,status,issue_date,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)", (iid,code,ct,proj,amt,amt,st,dt,now,now))
    for pid,code,ct,amt,dt,rm in [(1,'PAY2025001',1,1400000,'2025-10-15','预付款50%'),(2,'PAY2025002',2,2250000,'2025-12-01','预付款50%+到货款'),(3,'PAY2025003',3,1750000,'2026-01-10','预付款50%'),(4,'PAY2026001',2,450000,'2026-02-05','验收款10%')]:
        c.execute("INSERT OR REPLACE INTO payments (id,payment_no,contract_id,amount,payment_date,status,remark,created_at,updated_at) VALUES (?,?,?,?,?,'CONFIRMED',?,?,?)", (pid,code,ct,amt,dt,rm,now,now))

    # 16. 满意度
    print("创建满意度...")
    for sid,sno,cn,pc,pn,sc,fb in [(1,'CS2025001','华为技术有限公司','PJ2025003','华为5G老化测试系统',4.5,'交付及时，设备稳定性好'),(2,'CS2025002','比亚迪股份有限公司','PJ2025001','比亚迪ICT在线测试设备',4.0,'功能满足需求'),(3,'CS2025003','宁德时代新能源科技','PJ2025002','宁德时代EOL检测系统',4.2,'检测精度达标'),(4,'CS2026001','立讯精密工业','PJ2025004','立讯连接器视觉检测',3.8,'暂时满意')]:
        c.execute("INSERT OR REPLACE INTO customer_satisfactions (id,survey_no,survey_type,customer_name,project_code,project_name,overall_score,feedback,status,survey_date,created_by,created_at,updated_at) VALUES (?,?,'PROJECT',?,?,?,?,?,'COMPLETED',?,1,?,?)", (sid,sno,cn,pc,pn,sc,fb,now,now,now))

    conn.commit()

    # 验证
    print("\n--- 数据验证 ---")
    for t in ['departments','employees','users','customers','leads','opportunities','quotes','contracts','projects','materials','purchase_orders','workshop','worker','production_plan','work_order','delivery_orders','service_tickets','invoices','payments','customer_satisfactions']:
        cnt = c.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {cnt}")
    conn.close()

    print("\n✅ 演示数据生成完成！")
    print("  8个部门 | 19个员工 | 8个客户 | 10个线索 | 8个商机")
    print("  6个报价 | 5个合同 | 5个项目 | 20种物料 | 10个采购单")
    print("  3个车间 | 10个工人 | 5个生产计划 | 8个工单")
    print("  3个发货单 | 8个服务工单 | 5张发票 | 4笔回款 | 4条满意度")
    print(f"\n  所有用户默认密码: admin123")
    print(f"  清除演示数据: python scripts/clear_demo_data.py")

if __name__ == '__main__':
    main()
