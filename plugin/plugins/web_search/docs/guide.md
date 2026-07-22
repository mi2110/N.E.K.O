# 联网搜索 / Web Search

## 中文

### 获取 API 密钥

**百度千帆**（推荐中文搜索）：https://console.bce.baidu.com/qianfan/ais/console/apiKey
免费每日 100 次搜索额度。登录后创建并复制 API Key。

**Tavily**（推荐英文搜索）：https://tavily.com/
注册获取免费 API Key。

### V1 用户注意：手动配置 API 密钥

当前 N.E.K.O 版本（V1 SDK）不支持在插件面板中保存设置。请按以下步骤手动配置：

1. 打开插件配置文件：
   `C:\Users\你的用户名\AppData\Local\N.E.K.O\plugins\web_search\plugin.toml`
2. 找到文件末尾的 `[settings]` 段落
3. 在 `baidu_api_key = ""` 的引号中间粘贴你的百度 API Key
   示例：`baidu_api_key = "bce-v3/ALTAK-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"`
4. 保存文件
5. 重启 N.E.K.O
6. 打开插件即可生效

>Tavily API Key 同理：`tavily_api_key = "tvly-xxxxxxxxxxxx"`

没有 API Key 时插件会自动使用 DuckDuckGo 搜索（无需配置）。

### 搜索优先级
1. Tavily（最优先，质量最佳）
2. 百度千帆（中文内容）
3. DuckDuckGo（免密钥回退）

### 使用方法
在对话中直接对猫娘说：
- "帮我搜一下今天的新闻"
- "Python 最新版本是多少"
- "台风现在到哪里了"

---

## English

### Getting an API Key

**Baidu Qianfan** (recommended for Chinese): https://console.bce.baidu.com/qianfan/ais/console/apiKey
100 free searches per day. Sign in and create/copy your API Key.

**Tavily** (recommended for English): https://tavily.com/
Sign up for a free API Key.

### V1 Users: Manual API Key Configuration

The current N.E.K.O version (V1 SDK) does not support saving settings from the plugin panel. To configure API keys manually:

1. Open the plugin config file:
   `C:\Users\YourUsername\AppData\Local\N.E.K.O\plugins\web_search\plugin.toml`
2. Find the `[settings]` section at the bottom
3. Paste your Baidu API Key between the quotes: `baidu_api_key = "your-key-here"`
4. Save the file
5. Restart N.E.K.O
6. Open the plugin to activate

>Tavily API Key works the same way: `tavily_api_key = "tvly-xxxxxxxxxxxx"`

Without any API Key, the plugin automatically uses DuckDuckGo (no configuration needed).

### Search Priority
1. Tavily (best quality)
2. Baidu Qianfan (Chinese content)
3. DuckDuckGo (no key required)

### Usage
Ask your neko directly in conversation:
- "Search for today's news"
- "What's the latest Python version"
- "Where is the typhoon"