# Git Sync to Main - 自动同步到主分支

## 功能描述

这个 skill 帮助你在完成开发后，自动执行以下 Git 操作流程：

1. 提交当前分支的所有更改
2. 切换到 main 分支
3. 合并当前开发分支到 main
4. 推送 main 分支到远程仓库
5. 返回到原来的开发分支

## 使用场景

- 完成一个功能开发，需要将代码合并到 main 分支
- 需要快速同步本地开发分支到主分支
- 避免手动执行多个 Git 命令的繁琐操作

## 工作流程

```
当前分支 (feature/xxx)
    ↓
1. git add . && git commit && git push
    ↓
2. git push origin feature/xxx:main (直接推送到 main)
    ↓
完成！(自动停留在当前分支)
```

**核心优化**：
- 使用 `git push origin feature/xxx:main` 直接将当前分支推送到远程 main
- 无需切换分支，无需本地合并
- 2条命令完成所有操作

## 使用方法

直接告诉 Kiro：

- "帮我同步代码到 main 分支"
- "提交并合并到主分支"
- "完成开发，同步到 main"

## 执行步骤

### 步骤 1: 检查当前分支状态

首先检查当前所在的分支和工作区状态：

```bash
git status
git branch --show-current
```

**注意事项：**
- 如果当前已经在 main 分支，提示用户先切换到开发分支
- 如果工作区没有更改，询问用户是否仍要同步

### 步骤 2: 提交并推送当前分支

一条命令完成提交和推送：

```bash
git add . && git commit -m "用户提供的提交信息" && git push origin $(git branch --show-current)
```

**注意事项：**
- 如果用户没有提供提交信息，使用默认信息：`"feat: 完成开发并同步到 main"`
- 如果没有需要提交的更改，只执行 push
- 如果是新分支首次推送，自动使用 `-u` 参数

### 步骤 3: 直接推送到远程 main 分支

使用 Git 的远程分支推送语法，直接将当前分支推送到 main：

```bash
git push origin $(git branch --show-current):main
```

**注意事项：**
- 这个命令会将当前分支的内容直接推送到远程 main 分支
- 无需切换分支，无需本地合并
- 如果远程 main 有新提交，会提示需要先拉取（使用 --force 可强制推送，但不推荐）
- 推送成功后，当前分支保持不变

### 步骤 4: 显示操作总结

显示完成的操作摘要：

```
✅ 同步完成！

📝 提交信息: "feat: 完成开发并同步到 main"
📤 推送当前分支: feature/xxx → origin/feature/xxx ✓
� 同步到 main: feature/xxx → origin/main ✓
🔙 当前分支: feature/xxx (未改变)

⏱️  总耗时: 3秒

下一步建议:
- 继续在当前分支开发新功能
- 如果需要，可以删除已合并的分支: git branch -d feature/xxx
```
- 继续在当前分支开发新功能
```

## 错误处理

### 场景 1: 当前在 main 分支

```
❌ 错误: 当前已在 main 分支

请先切换到开发分支，例如:
git checkout -b feature/new-feature
```

### 场景 2: 工作区有未提交的更改但用户取消提交

```
❌ 操作取消

工作区有未提交的更改，请先提交或暂存:
git add .
git commit -m "your message"
```

### 场景 3: 远程 main 有新提交

```
⚠️  推送被拒绝

远程 main 分支有新的提交，无法直接推送。

建议操作:
1. 先拉取并合并远程 main 的更新到当前分支
   git pull origin main --rebase
   
2. 解决可能的冲突

3. 再次执行同步命令

或者使用强制推送（⚠️ 危险，会覆盖远程 main）:
git push origin feature/xxx:main --force
```

### 场景 4: 当前分支推送失败

```
⚠️  推送当前分支失败

无法推送 feature/xxx 到远程仓库。
可能原因:
- 网络问题
- 权限不足
- 远程分支有新提交需要先拉取

建议操作:
1. 检查网络连接
2. 如果是新分支: git push -u origin feature/xxx
3. 如果远程有更新: git pull origin feature/xxx --rebase

是否继续合并到 main 分支？(y/n)
```

### 场景 5: Main 分支推送失败

```
⚠️  推送失败

main 分支已在本地合并，但推送到远程失败。
可能原因:
- 网络问题
- 权限不足
- 远程分支有新提交

请稍后手动推送: git push origin main
```

## 安全检查

在执行操作前，进行以下安全检查：

1. **检查是否有未保存的更改**
   - 如果有，询问用户是否提交

2. **检查是否有未推送的提交**
   - 如果有，提示用户当前分支有未推送的提交

3. **检查远程仓库连接**
   - 确保可以连接到远程仓库

4. **检查分支保护规则**
   - 如果 main 分支有保护，提示用户可能需要通过 PR

## 高级选项

用户可以通过以下方式自定义行为：

- **强制推送到 main**: "强制同步到 main"（会覆盖远程 main，危险操作）
- **仅推送当前分支**: "只推送当前分支，不同步到 main"
- **同步后删除分支**: "同步到 main 并删除当前分支"

## 示例对话

**用户**: "帮我同步代码到 main 分支"

**Kiro**: 
```
📋 当前状态:
- 当前分支: feature/video-upload
- 未提交更改: 5 个文件

请提供提交信息（回车使用默认信息）:
```

**用户**: "feat: 完成视频上传功能"

**Kiro**:
```
✅ 正在执行同步流程...

1. ✅ 提交并推送 feature/video-upload
2. ✅ 直接同步到远程 main 分支

🎉 同步完成！(总耗时: 3秒)
```

## 注意事项

1. **确保有提交权限**: 需要有推送到 main 分支的权限
2. **团队协作**: 如果团队使用 PR 流程，此 skill 可能不适用
3. **分支保护**: 如果 main 分支有保护规则，推送可能失败
4. **备份重要更改**: 在执行前确保重要更改已备份

## 相关命令

如果需要手动执行，可以使用以下命令：

```bash
# 方法 1: 最简洁（推荐）
BRANCH=$(git branch --show-current)
git add . && git commit -m "your message" && git push origin $BRANCH && git push origin $BRANCH:main

# 方法 2: 一行命令
git add . && git commit -m "your message" && git push origin $(git branch --show-current) && git push origin $(git branch --show-current):main

# 方法 3: 强制推送到 main（危险）
git push origin $(git branch --show-current):main --force
```

## 核心优势

✅ **速度快**: 只需 2 条命令，3 秒完成
✅ **不切换分支**: 始终停留在当前开发分支
✅ **无需本地合并**: 直接推送到远程 main
✅ **简单安全**: 减少操作步骤，降低出错概率
