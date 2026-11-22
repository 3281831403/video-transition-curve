# video-transition-curve

给成片加转场后，首尾总跳一帧、擦除方向还是反的：缓动曲线端点不回 0/1，首尾各跳一帧；dissolve 不外推端点，t=0 时仍混入 1% 的 B；擦除遮罩方向反了，本该从左往右却从右往左；羽化写死 1 像素、完全忽略 feather 参数；滑动位移不按方向取符号，四个方向都朝同一侧滑；组合转场输出尺寸多出 1 像素；未知 kind 被静默当成 dissolve；t 越界不钳制，像素值冲出 [0,1]；批量转场共用同一张遮罩，任务之间互相串；w=0 不做校验，直接除零。transition/curves.py 是核心，tests/test_curves.py 15个红。要修的是：transition/curves.py 里的 8 个桩函数，按 tests/test_curves.py 的契约补齐实现，让 15 条测试全部转绿。

## 运行方式

```bash
python -m pytest tests -q
```

初始输出恰好为 `15 failed`，没有 collection / import / syntax error；实现完成后应为 `15 passed`。

## 字段表

| 字段 | 取值 |
| --- | --- |
| 所属领域 | 游戏、图形与多媒体 |
| 子方向 | 音视频处理 |
| 任务类型 | Bugfix |
| 语言/框架 | Python 3, pytest |
| 环境可复现等级 | 无外部依赖 |

## 约束

- `tests/test_curves.py` 不可修改，请只修改 `transition/curves.py`。
- 仅使用标准库（`math`）与 `pytest`，离线运行，不使用随机数。
- 进度 `t` 归一化到 `0..1`，数值比较容差 `1e-6`（端点检查 `1e-9`）。
