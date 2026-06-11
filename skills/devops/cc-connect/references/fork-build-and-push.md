# cc-connect Fork: 编译 + 推送 GitHub 完整流程

## 环境

- WSL2 (Ubuntu)，无Go
- Windows Go 1.26.2: `/mnt/c/Program Files/Go/bin/go.exe`
- Windows GitHub CLI: `gh.exe`，账号 `ruiyangruiyi`
- 源码: `/mnt/d/work/cc-connect/` (从 chenhg5/cc-connect git clone)

## 编译

```bash
cd /mnt/d/work/cc-connect
/mnt/c/Program\ Files/Go/bin/go.exe build -tags no_web -o cc-connect.exe ./cmd/cc-connect/
```

产出 ~30M exe。`-tags no_web` 必须加（web/dist不存在）。

## 推送到自有 Fork

### 1. 创建 GitHub 仓库

```bash
cd /mnt/d/work/cc-connect
/mnt/c/Program\ Files/GitHub\ CLI/gh.exe repo create cc-connect-fork \
  --public \
  --description "cc-connect with allow_bots support for Discord bot-to-bot communication" \
  --source .
```

⚠️ 会报 `Unable to add remote "origin"` 因为源码已有origin指向原作者。

### 2. 修改 remote

```bash
git remote rename origin upstream
git remote add origin https://github.com/ruiyangruiyi/cc-connect-fork.git
```

- `upstream` → chenhg5/cc-connect（方便以后同步更新）
- `origin` → ruiyangruiyi/cc-connect-fork

### 3. 推送（workflow权限坑）

**直接推会失败：**
```
refusing to allow a Personal Access Token to create or update workflow
`.github/workflows/ci.yml` without `workflow` scope
```

即使删了 `.github/workflows/` 目录也不行——git历史里还包含这些文件。

**解法：用 orphan branch 创建干净历史**

```bash
git checkout --orphan clean-main
git add -A   # 当前工作目录（不含workflows，因为已删除）
git commit -m "feat(discord): cc-connect fork with allow_bots support"
git push origin clean-main:main --force
```

这会创建一个全新的root commit，不含workflow文件，推送成功。

⚠️ **.gitignore 坑：** 新建的 `config-example/` 等目录下的文件可能被 `.gitignore` 忽略，导致 `git add -A` 不会包含它们。强制添加：
```bash
git add -f config-example/config.toml README.md
git commit -m "docs: add README and config example"
git push origin clean-main:main --force
```

### 4. 提交改动

改动在同一个orphan commit里，或后续正常commit即可（因为历史里已无workflow文件）。

## 替换部署

```bash
# 备份旧的
cp /mnt/c/Users/24045/AppData/Roaming/npm/node_modules/cc-connect/bin/cc-connect.exe \
   /mnt/c/Users/24045/AppData/Roaming/npm/node_modules/cc-connect/bin/cc-connect.exe.bak

# 复制新的
cp /mnt/d/work/cc-connect/cc-connect.exe \
   /mnt/c/Users/24045/AppData/Roaming/npm/node_modules/cc-connect/bin/cc-connect.exe
```

⚠️ 如果cc-connect正在运行，exe文件被锁定会 Permission denied。先停服务再替换。

## 后续同步上游

```bash
git fetch upstream
git merge upstream/main
# 解决冲突后推送
git push origin main
```
