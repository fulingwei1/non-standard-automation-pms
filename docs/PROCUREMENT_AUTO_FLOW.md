# 采购模块自动下单流程

本指南演示如何通过 API/前端完成 **BOM → 采购申请 → 审批 → 自动下单** 的闭环，方便演示或验证。

## 1. 从 BOM 生成采购申请

```bash
curl -X POST "http://localhost:8000/api/v1/bom/1/generate-pr?create_requests=true" \
  -H "Authorization: Bearer <TOKEN>"
```

- 系统会按供应商分组 BOM 行，自动写入 `purchase_requests` 与明细。
- 响应中的 `data.created_requests` 会返回生成的采购申请编号及供应商。

## 2. 检查/补充采购申请

1. 打开前端 **采购申请列表**，可看到刚生成的申请（含供应商、金额、来源信息）。
2. 如需补充信息，可在详情页面编辑备注、需求日期等；确保「指定供应商」字段已填写。

## 3. 提交与审批

```bash
# 提交
curl -X PUT "http://localhost:8000/api/v1/purchase-orders/requests/{id}/submit" \
  -H "Authorization: Bearer <TOKEN>"

# 审批（通过后自动下单）
curl -X PUT "http://localhost:8000/api/v1/purchase-orders/requests/{id}/approve?approved=true" \
  -H "Authorization: Bearer <TOKEN>"
```

- 审批通过后会调用 `auto_create_purchase_orders_from_request`，根据申请明细生成采购订单，并回写 `ordered_qty`、BOM 行 `purchased_qty`。
- 采购申请详情页会显示「已生成采购订单」标记及订单列表，可直接跳转查看。

## 4. 查看采购订单

访问 `/purchase-orders/{order_id}` 可看到 `source_request_no` 字段，明确来源采购申请。

## 5. 手动重新生成（可选）

若审批时因缺少供应商等原因导致自动下单失败，可在补充信息后执行：

```bash
curl -X POST "http://localhost:8000/api/v1/purchase-orders/requests/{id}/generate-orders" \
  -H "Authorization: Bearer <TOKEN>"
```

- 支持 `?force=true` 重新触发，适用于演练或重新分配供应商的场景。

## 6. 前端体验

1. 在前端「采购申请」模块即可完成创建、提交、审批、查看生成订单的操作。
2. 「新建采购申请」页面需要指定供应商，避免审批后无法自动下单。
3. 当采购订单生成后，申请详情右侧会展示订单列表与跳转按钮，便于演示完整链路。
