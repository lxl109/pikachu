# OpenCLI 使用说明

## 安装状态

- **包名**: `@jackwener/opencli`
- **版本**: 1.7.14
- **安装位置**: `C:\Users\Administrator\AppData\Local\Programs\kimi-desktop\node_modules\@jackwener\opencli`
- **Node.js**: 使用 Cursor 自带的 Node.js v22.22.0

## 运行方式

由于系统 PATH 中没有 Node.js，需要使用完整路径运行：

```bash
# 查看版本
"C:/Users/Administrator/AppData/Local/Programs/cursor/resources/app/resources/helpers/node.exe" \
"C:/Users/Administrator/AppData/Local/Programs/kimi-desktop/node_modules/@jackwener/opencli/dist/src/main.js" \
--version

# 列出所有支持的平台
"C:/Users/Administrator/AppData/Local/Programs/cursor/resources/app/resources/helpers/node.exe" \
"C:/Users/Administrator/AppData/Local/Programs/kimi-desktop/node_modules/@jackwener/opencli/dist/src/main.js" \
list
```

## 常用平台示例

| 平台 | 命令示例 |
|------|---------|
| 微博热榜 | `opencli weibo hot` |
| 知乎热榜 | `opencli zhihu hot` |
| B站热门 | `opencli bilibili hot` |
| 小红书 | `opencli xiaohongshu feed` |
| Twitter/X | `opencli twitter trending` |
| GitHub | `opencli github trending --language python` |
| 36氪 | `opencli 36kr hot` |

## 让 Claude Code 帮你用

直接说需求即可，例如：
- "查一下现在微博上有什么热门话题"
- "帮我看看 B站今天的热门视频"
- "搜索知乎上关于 AI 的讨论"

Claude Code 会自动调用 OpenCLI 获取结果。
