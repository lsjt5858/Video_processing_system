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
1. git add . && git commit
    ↓
2. git push origin feature/xxx (推送当前分支)
    ↓
3. git checkout main
    ↓
4. git pull origin main (拉取最新 main)
    ↓
5. git merge feature/xxx
    ↓
6. git push origin main
    ↓
7. git checkout feature/xxx (返回原分支)
```

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
- 如果工作区没有更改，询问用户是否仍要合并

### 步骤 2: 提交当前分支的更改

询问用户提交信息，然后提交所有更改：

```bash
git add .
git commit -m "用户提供的提交信息"
```

**注意事项：**
- 如果用户没有提供提交信息，使用默认信息：`"feat: 完成开发并同步到 main"`
- 如果没有需要提交的更改，跳过此步骤

### 步骤 3: 推送当前分支到远程

在切换分支前，先推送当前分支的提交到远程：

```bash
git push origin $CURRENT_BRANCH
```

**注意事项：**
- 确保当前分支的更改已同步到远程
- 如果是新分支首次推送，使用 `git push -u origin $CURRENT_BRANCH`
- 如果推送失败，提示用户检查网络或权限

### 步骤 4: 切换到 main 分支

```bash
git checkout main
```

**注意事项：**
- 如果 main 分支不存在，尝试 master 分支
- 如果切换失败，终止流程并报告错误

### 步骤 5: 拉取最新的 main 分支

拉取远程 main 分支的最新代码：

```bash
git pull origin main
```

**注意事项：**
- 必须拉取最新代码，避免推送时的冲突
- 如果拉取失败（如有冲突），提示用户手动解决
- 拉取失败时，自动返回原分支

### 步骤 6: 合并开发分支到 main

```bash
git merge $CURRENT_BRANCH --no-ff -m "Merge branch '$CURRENT_BRANCH' into main"
```

**注意事项：**
- 使用 `--no-ff` 保留分支历史
- 如果合并有冲突，提示用户手动解决冲突后再继续
- 合并失败时，自动返回原分支

### 步骤 7: 推送 main 分支到远程

```bash
git push origin main
```

**注意事项：**
- 如果推送失败，提示用户检查权限或网络
- 推送失败不影响返回原分支

### 步骤 8: 返回原开发分支

```bash
git checkout $CURRENT_BRANCH
```

**注意事项：**
- 确保返回到原分支，即使前面的步骤失败
- 返回后显示当前分支状态

### 步骤 9: 显示操作总结

显示完成的操作摘要：

```
✅ 操作完成！

📝 提交信息: "feat: 完成开发并同步到 main"
� 推送当前分支: feature/xxx → origin/feature/xxx (成功)
�🔀 合并分支: feature/xxx → main
📤 推送 main: main → origin/main (成功)
🔙 当前分支: feature/xxx

下一步建议:
- 如果需要，可以删除已合并的分支: git branch -d feature/xxx
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

### 场景 3: 合并冲突

```
⚠️  合并冲突

检测到合并冲突，请手动解决冲突后执行:
1. 解决冲突文件
2. git add .
3. git commit
4. git push origin main
5. git checkout feature/xxx
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

- **跳过推送当前分支**: "同步到 main，不推送当前分支"（不推荐）
- **使用 rebase 而非 merge**: "同步到 main，使用 rebase"
- **推送后删除分支**: "同步到 main 并删除当前分支"
- **仅推送当前分支**: "只推送当前分支，不合并到 main"

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

1. ✅ 提交更改到 feature/video-upload
2. ✅ 推送 feature/video-upload 到远程
3. ✅ 切换到 main 分支
4. ✅ 拉取远程 main 分支
5. ✅ 合并 feature/video-upload 到 main
6. ✅ 推送 main 分支到远程
7. ✅ 返回 feature/video-upload 分支

🎉 同步完成！
```

## 注意事项

1. **确保有提交权限**: 需要有推送到 main 分支的权限
2. **团队协作**: 如果团队使用 PR 流程，此 skill 可能不适用
3. **分支保护**: 如果 main 分支有保护规则，推送可能失败
4. **备份重要更改**: 在执行前确保重要更改已备份

## 相关命令

如果需要手动执行，可以使用以下命令：

```bash
# 保存当前分支名
BRANCH=$(git branch --show-current)

# 提交更改
git add .
git commit -m "your message"

# 推送当前分支到远程
git push origin $BRANCH

# 切换到 main 并合并
git checkout main
git pull origin main
git merge $BRANCH --no-ff
git push origin main

# 返回原分支
git checkout $BRANCH
```
