# 自动战斗脚本整理

本目录保存三个角色自动战斗脚本的原始文本，以及对脚本行为和运行依赖的整理说明。

- `卜灵.txt`：`Douling` 角色脚本与修改需求上下文。
- `雷主.txt`：`Rover` 角色脚本，包含光主、风主和暗主形态分派。
- `心.txt`：`Hsin` 角色脚本与修改需求上下文。
- `脚本理解.md`：对三个脚本的流程、状态、切人策略、依赖和风险的说明。
- `队伍循环轴.md`：固定 1/2/3 号位和启动轴、循环轴的执行规格。
- `rotation_axis.py`：轴规格的独立检查参考实现。
- `卜灵.py`、`雷主.py`、`心.py`：按实际项目调度方式编写的三个固定位置角色类。每个文件都可单独粘贴，不依赖外部轴模块。
- `check_rotation.py`：语法、动作接口和轴顺序检查脚本。

这三个 `.txt` 文件保留了原始内容，包含 Markdown 代码围栏、说明文字和 BaseChar 参考链接，因此它们是脚本设计记录。新增的 `.py` 文件按参考压缩包的角色轴结构实现：使用 `normal_attack()`、`heavy_attack()`、`f_break()` 等 BaseChar 封装，并通过 `task.send_key()` 与 `task.in_team()` 显式切换和确认位置。

运行检查：

```powershell
python check_rotation.py
```

轴状态保存在任务对象的 `_fixed_rotation_state` 上。角色的 `reset_state()` 不会重置该状态，避免框架切人时把轴反复退回启动段；创建新的任务对象时会自动从启动轴开始。

心的第一个 R 成功后进入变形状态，`心.py` 中的 `TRANSFORMED_NORMAL_ATTACK_EXTRA_WAIT` 控制变形后的普攻额外后摇；第二个 R 会等待 `Labels.hsin_lib2` 强化标记后释放。

## Git

当前目录已初始化为 Git 仓库。查看状态、记录变更并提交：

```powershell
git status
git add .
git commit -m "更新自动战斗脚本整理"
```
