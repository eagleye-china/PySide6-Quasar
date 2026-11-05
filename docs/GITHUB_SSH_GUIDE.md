# 企业级 SSH + GitHub 完整操作指南

> 适用场景：Windows PowerShell / Miniconda 环境，企业开发或个人开源项目
> 覆盖内容：SSH 密钥配置、分支保护工作流、Tag 版本发布、多账号管理、常见故障排错、安全红线
> 适配项目：`eagleye-china/pyside-quasar`（本地分支 `master`，远端 SSH 地址已配置）

---

## 一、前置说明

1. 环境：Windows 10/11 + PowerShell / Miniconda PowerShell / Git Bash，需已安装 Git for Windows。
2. 选择 SSH 方式的原因：免去每次输入账号密码，天然支持 tag、MR/PR、CI 流水线，适合长期维护的企业/开源仓库。
3. 本仓库现状：本地分支 `master`，远端 `origin = git@github.com:eagleye-china/pyside-quasar.git`，已完成首次提交并发布 `v0.2.0-alpha` 标签。

---

# 第一部分：SSH 密钥全套配置（Windows）

## 1.1 生成 Ed25519 密钥（企业推荐，优于 RSA）

```powershell
ssh-keygen -t ed25519 -C "zdt168@sina.cn"
```

- 保存路径：直接回车，默认 `C:\Users\Administrator\.ssh\id_ed25519`
- **强烈建议设置 Passphrase（密码短语）**：即使私钥文件泄露，无密码也无法使用，是企业安全强制项。
- 若提示文件已存在：输入 `n` 不覆盖，复用已有密钥。

> ⚠️ 区分两个文件：
> - `id_ed25519` → **私钥，严禁对外泄露，绝不提交任何地方**
> - `id_ed25519.pub` → **公钥，复制内容粘贴到 GitHub 网页**

## 1.2 将公钥添加至 GitHub

1. 打印公钥全部内容：

```powershell
cat C:\Users\Administrator\.ssh\id_ed25519.pub
```

2. 完整复制输出全部文本（以 `ssh-ed25519` 开头）。
3. GitHub 网页 → 右上角头像 → Settings → SSH and GPG keys → New SSH key
   - Title：`Windows-Work-pyside-quasar`（设备标识）
   - Key type：`Authentication key`
   - Key：粘贴复制的公钥 → Add SSH key

## 1.3 验证 SSH 连通性

```powershell
ssh -T git@github.com
```

首次连接提示指纹确认，输入 `yes` 回车。

✅ 成功输出示例：

```
Hi eagleye-china! You've successfully authenticated, but GitHub does not provide shell access.
```

❌ 报错 `Permission denied`：检查公钥粘贴是否完整、是否使用了正确私钥。

## 1.4 Windows ssh-agent 记住密钥密码（避免每次操作输入 passphrase）

PowerShell 管理员权限执行：

```powershell
# 设置 ssh-agent 开机自动启动
Set-Service ssh-agent -StartupType Automatic
Start-Service ssh-agent

# 添加你的私钥
ssh-add C:\Users\Administrator\.ssh\id_ed25519
```

输入 passphrase 后，当前会话的 git 操作不再重复输入密码。

## 1.5 多账号场景 ~/.ssh/config

新建文件 `C:\Users\Administrator\.ssh\config`（无后缀）。

```ssh-config
Host github-work
  HostName github.com
  IdentityFile ~/.ssh/id_ed25519
  User git
```

克隆时使用别名：

```powershell
git clone git@github-work:eagleye-china/pyside-quasar.git
```

> Linux/macOS 需要 `chmod 600 ~/.ssh/config`；Windows 下 Git for Windows 自动处理。

## 1.6 HTTP 远程切换为 SSH 远程

```powershell
# 查看当前 remote
git remote -v

# 修改 remote 地址
git remote set-url origin git@github.com:eagleye-china/pyside-quasar.git
```

---

# 第二部分：企业级分支工作流（master 为主保护分支）

> 规范：**master 分支禁止直接开发、禁止直接 push 日常代码；只接受 PR 合并；只存放可发布里程碑代码；版本 tag 打在 master 上。**

| 分支 | 用途 |
|------|------|
| `master` | 受保护主分支，可发布基线，打版本 tag |
| `feat/xxx-feature` | 新功能开发分支，从 master 切出 |
| `fix/bug-xxx` | 普通缺陷修复分支 |
| `hotfix/crash-xxx` | 线上紧急修复分支 |

## 2.1 标准开发完整流程

### ① 更新本地 master，与远端保持同步

```powershell
git checkout master
git pull origin master
```

### ② 从 master 切出新功能分支

```powershell
git checkout -b feat/migrate-tabs-to-qbasewidget
```

### ③ 在功能分支修改代码并提交

遵循 Conventional Commits：`feat:` / `fix:` / `docs:` / `chore:` / `refactor:`

```powershell
git add .
git commit -m "refactor: migrate Tabs/TabItem to QBaseWidget base class"

# 推送远端特性分支
git push origin feat/migrate-tabs-to-qbasewidget
```

### ④ 在 GitHub 网页创建 Pull Request（PR）

1. 仓库页面会弹出创建 PR 提示，目标分支选择 `master`。
2. 填写变更说明：改动范围、测试点、关联任务。
3. 等待 CI 流水线执行（lint、单元测试），完成代码评审。
4. CI 全部通过 + 评审通过，网页端合并 PR 到 master。
5. 合并完成后删除远端特性分支并清理本地分支：

```powershell
git checkout master
git pull origin master
git branch -d feat/migrate-tabs-to-qbasewidget
```

## 2.2 Hotfix 紧急修复流程

```powershell
git checkout master
git pull origin master
git checkout -b hotfix/fix-animation-gc-crash

# 修改代码后
git add .
git commit -m "fix: fix animation libshiboken already deleted GC crash"
git push origin hotfix/fix-animation-gc-crash
```

同样通过 PR 合入 master。

## 2.3 版本 Tag 发布流程

> annotated tag（带注释标签）是企业发布强制要求，不要使用轻量 tag。

```powershell
# 切换到 master，确保代码是最新合并完成的里程碑
git checkout master
git pull origin master

# 创建带注释 tag
git tag -a v0.3.0-alpha -m "v0.3.0-alpha：L3 Table 组件落地，完善斑马纹与单元格自定义渲染"

# 推送分支 + tag 到远端
git push origin master --tags
```

只推送单个 tag（不推分支）：

```powershell
git push origin v0.3.0-alpha
```

## 2.4 仓库保护配置（GitHub 网页端企业级设置）

仓库 → Settings → Branches → Branch protection rules → Add rule，填入 `master`

✅ 推荐勾选规则：

1. **Require a pull request before merging**：必须 PR 才能合并，禁止直接 push
2. **Require approvals**：至少 1 个评审批准
3. **Require status checks to pass before merging**：CI 不通过禁止合并
4. **Do not allow bypassing the above settings**
5. ❗ 禁止 force push 到 master（禁止 `git push -f origin master`）

> ⚠️ 开启保护后，本地无法直接 `git push origin master` 推送普通代码，只能通过网页 PR 合并；里程碑 tag 不受此限制。

---

# 第三部分：高频日常命令速查表

```powershell
# 查看远端信息
git remote -v

# 拉取远端更新，不合并
git fetch origin

# 拉取并合并当前分支
git pull origin master

# 查看本地分支
git branch

# 查看所有 tag
git tag

# 删除本地 tag
git tag -d v0.2.0-alpha

# 删除远端 tag
git push origin --delete v0.2.0-alpha

# 撤销最近一次 commit（保留代码，只撤销提交）
git reset --soft HEAD~1

# 查看提交日志
git log --oneline --graph
```

---

# 第四部分：常见故障排查

## 问题 1：`ssh -T git@github.com` 报 Permission denied (publickey)

1. 确认公钥完整粘贴到 GitHub，无多余换行空格；
2. 确认使用的私钥与上传的公钥配对；
3. 执行 `ssh-add` 加载私钥；
4. 检查防火墙/代理是否阻断 22 端口；企业网络若屏蔽 22 端口，可在 `~/.ssh/config` 增加 `Port 443`。

## 问题 2：git commit 中文乱码

PowerShell 设置 git 编码：

```powershell
git config --global core.quotepath false
git config --global i18n.commitEncoding utf-8
git config --global i18n.logOutputEncoding utf-8
```

> 已提交的乱码 commit 无法自动修复，后续新 commit 中文正常。

## 问题 3：提示 `src refspec xxx does not match any`

本地不存在该分支。先完成至少一次 commit，核对本地分支名称。

## 问题 4：已配置 SSH，git 仍弹出账号密码输入框

```powershell
git remote -v
```

确认 origin 地址是 `git@github.com:...`，而不是 `https://github.com/...`；若是 HTTPS，执行 `git remote set-url` 切换为 SSH 地址。

## 问题 5：tag 打错，需要重新发布

```powershell
# 删除本地 tag
git tag -d v0.2.0-alpha

# 删除远端 tag
git push origin --delete v0.2.0-alpha

# 重新打 tag 并推送
git tag -a v0.2.0-alpha -m "修正注释"
git push origin --tags
```

---

# 第五部分：安全红线（企业强制遵守）

1. **私钥文件绝不提交 git、不在聊天中转发、不上传云盘备份**；私钥只保存在用户目录 `.ssh`，不放入项目目录。
2. 私钥必须设置 passphrase，防止密钥文件泄露后被盗用。
3. master 分支严禁直接 `git push`，全部变更走 PR 评审。
4. 禁止在 master 分支本地直接写业务代码。
5. 禁止强制推送 `git push -f` 到受保护的 master 分支。
6. `.gitignore` 严格配置，禁止提交：虚拟环境、缓存、密钥、日志、打包产物。

---

# 附：Commit 规范速查（Conventional Commits）

| Type | 用途 | 示例 |
|------|------|------|
| `feat` | 新功能 / 里程碑版本 | `feat: release v0.3.0-alpha ...` |
| `fix` | bug 修复 | `fix: fix animation GC crash` |
| `docs` | 文档修改 | `docs: update GITHUB_SSH_GUIDE` |
| `refactor` | 重构（不改变外部行为） | `refactor: migrate tabs to QBaseWidget` |
| `chore` | 构建、依赖、CI 配置 | `chore: update gitignore` |
| `test` | 单元测试 | `test: add table model unit tests` |