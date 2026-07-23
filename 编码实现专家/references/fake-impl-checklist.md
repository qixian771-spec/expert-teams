# 假实现检测清单 —— 治"假实现"

> AI 最常糊弄你：看着像做完、其实没做完。**verify 前必须逐项扫过。**
> 原则：**只有"真接线"才算 done**，否则打回重做。

## 一、硬编码 / Mock 数据
- [ ] 函数返回的是写死的假数据，而不是真逻辑 / 真查库？
- [ ] 列表、用户信息、价格等是 placeholder 常量？

## 二、TODO / FIXME / Placeholder
- [ ] 残留 `TODO` / `FIXME` / `XXX` / `placeholder` 注释？
- [ ] 空函数体、`pass` / `return null` / `return {}` / 未实现的 `raise NotImplementedError`？

## 三、没接线（最常见）
- [ ] UI 按钮 / 表单**绑定了真实 handler** 吗？还是点了没反应？
- [ ] 接口**真查库 / 真调上游** 吗？还是返回静态响应？
- [ ] 前端调的后端接口**真实存在** 吗？路径对得上 ENTRY.md 吗？

## 四、假测试
- [ ] 有 `assert true` / 恒真断言吗？
- [ ] 测试被 `skip` / `xit` / `describe.skip` 了吗？
- [ ] 只测了 trivial 路径、没测核心逻辑吗？

## 五、假完成
- [ ] SUMMARY / 汇报写"已实现"，但代码是 stub 吗？
- [ ] "已实现"的功能真的能被端到端走通吗（不只单元过）？

## 扫描手段（可直接执行）
```bash
# 1. 搜待办与占位
grep -rnE "TODO|FIXME|XXX|placeholder|not implemented|NotImplemented" src/ --include=*.{js,ts,py,tsx,jsx,go,java}

# 2. 搜常见假返回（按语言调整）
grep -rnE "return (null|true|false|\{\}|\[\]|\"mock|\"test|\"placeholder)" src/

# 3. 搜被跳过的测试
grep -rnE "\.skip|xit\(|xdescribe\(|@skip|# TODO.*test" tests/ src/

# 4. 检查未引用/疑似死代码（辅助）
#    结合语言工具：vulture(py) / ts-prune(ts) / deadcode 等
```
- [ ] 以上扫描发现的问题都已清零，或有明确跟踪事项。

## 判定
- 全部 ✓ 且无"看着对其实没接线" → 通过，进入 ship
- 任一项命中 → 打回，写明根因，修复后复扫
