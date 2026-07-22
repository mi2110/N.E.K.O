import asyncio
import json
import re
import ssl
import urllib.parse
import urllib.request

from plugin.sdk.plugin import (
    NekoPluginBase, neko_plugin, lifecycle,
    plugin_entry, ui, Ok, Err, SdkError,
)


@neko_plugin
class WebSearch(NekoPluginBase):

    def __init__(self, ctx):
        super().__init__(ctx)
        self._max_results: int = 5
        self._timeout: int = 15
        self._baidu_api_key: str = ""
        self._tavily_api_key: str = ""
        self._frozen: bool = False

    @lifecycle(id="startup")
    async def on_startup(self, **_):
        cfg = await self.config.dump()
        s = cfg.get("settings", {})
        self._max_results = s.get("max_results", 5)
        self._timeout = s.get("timeout", 15)
        self._baidu_api_key = str(s.get("baidu_api_key", "")).strip()
        self._tavily_api_key = str(s.get("tavily_api_key", "")).strip()
        return Ok({"status": "ready"})

    @lifecycle(id="reload")
    async def on_reload(self, **_):
        cfg = await self.config.dump()
        s = cfg.get("settings", {})
        self._max_results = s.get("max_results", 5)
        self._timeout = s.get("timeout", 15)
        self._baidu_api_key = str(s.get("baidu_api_key", "")).strip()
        self._tavily_api_key = str(s.get("tavily_api_key", "")).strip()
        return Ok({"status": "reloaded"})

    @lifecycle(id="config_change")
    async def on_config_change(self, old_config=None, new_config=None, **_):
        if new_config:
            s = new_config.get("settings", {})
            self._max_results = s.get("max_results", self._max_results)
            self._timeout = s.get("timeout", self._timeout)
            self._baidu_api_key = str(s.get("baidu_api_key", self._baidu_api_key)).strip()
            self._tavily_api_key = str(s.get("tavily_api_key", self._tavily_api_key)).strip()
        return Ok({"status": "config_updated"})

    @lifecycle(id="freeze")
    async def on_freeze(self, **_):
        self._frozen = True
        return Ok({"status": "frozen"})

    @lifecycle(id="unfreeze")
    async def on_unfreeze(self, **_):
        self._frozen = False
        return Ok({"status": "unfrozen"})

    @lifecycle(id="shutdown")
    async def on_shutdown(self, **_):
        return Ok({"status": "shutdown"})

    @plugin_entry(
        id="search_web", name="Web Search",
        description="Search the internet for real-time information and web results.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query."},
                "max_results": {"type": "integer", "default": 5, "description": "Max 10."},
            },
            "required": ["query"],
        },
        llm_result_fields=["query", "answer", "count"],
    )
    async def search_web(self, query: str = "", max_results: int = 5, _ctx=None, **_):
        if self._frozen: return Err(SdkError("Plugin frozen."))
        if not query.strip(): return Err(SdkError("Query cannot be empty."))
        max_results = max(1, min(max_results, 10))
        try:
            if self._tavily_api_key:
                results = await self._tavily_search(query.strip(), max_results)
            elif self._baidu_api_key:
                results = await self._baidu_search(query.strip(), max_results)
            else:
                results = await self._ddg_web_search(query.strip(), max_results)
            if not results: return Ok({"query": query, "results": [], "count": 0})
            return Ok({
                "query": query, "results": results, "count": len(results),
                "answer": "Found {0}:`n`n".format(len(results)) + "`n`n".join(
                    "{0}. {1}`n{2}`n{3}".format(i+1, r["title"], r["snippet"], r["url"])
                    for i, r in enumerate(results)),
            })
        except Exception as e:
            return Err(SdkError("Search failed: {0}.".format(e)))

    @plugin_entry(
        id="get_instant_answer", name="Instant Answer",
        description="Get an instant answer for a topic.",
        input_schema={
            "type": "object",
            "properties": {"query": {"type": "string", "description": "The keyword."}},
            "required": ["query"],
        },
        llm_result_fields=["query", "abstract", "abstract_url", "answer", "heading"],
    )
    async def get_instant_answer(self, query: str = "", _ctx=None, **_):
        if self._frozen: return Err(SdkError("Plugin frozen."))
        if not query.strip(): return Err(SdkError("Query cannot be empty."))
        try:
            if self._tavily_api_key:
                r = await self._tavily_search(query.strip(), 1); f = r[0] if r else {}
                return Ok({"query": query, "heading": f.get("title",""), "abstract": f.get("snippet",""),
                    "abstract_url": f.get("url",""), "abstract_source": "Tavily", "answer": f.get("snippet",""),
                    "answer_type": "web_search", "related_topics": []})
            elif self._baidu_api_key:
                r = await self._baidu_search(query.strip(), 1); f = r[0] if r else {}
                return Ok({"query": query, "heading": f.get("title",""), "abstract": f.get("snippet",""),
                    "abstract_url": f.get("url",""), "abstract_source": "Baidu", "answer": f.get("snippet",""),
                    "answer_type": "web_search", "related_topics": []})
            else:
                return Ok(await self._ddg_instant_answer(query.strip()))
        except Exception as e:
            return Err(SdkError("Query failed: {0}.".format(e)))

    # === UI ===

    @ui.context(id="settings")
    async def settings_context(self, _ctx=None):
        return {"config": {
            "max_results": self._max_results, "timeout": self._timeout,
            "baidu_api_key": self._baidu_api_key, "tavily_api_key": self._tavily_api_key,
        }}

    @plugin_entry(
        id="save_settings", name="Save Settings",
        description="Save plugin configuration",
        input_schema={"type": "object", "properties": {"config": {"type": "object", "description": "Config"}}, "required": ["config"]},
    )
    @ui.action(id="update_settings", label="Save Settings", refresh_context=True)
    async def update_settings(self, config: dict = None, _ctx=None, **_):
        if not isinstance(config, dict): return Err(SdkError("config must be an object"))
        mr = int(config.get("max_results", 5)); to = int(config.get("timeout", 15))
        bk = str(config.get("baidu_api_key", "")).strip(); tk = str(config.get("tavily_api_key", "")).strip()
        await self.config.update({"settings": {"max_results": mr, "timeout": to, "baidu_api_key": bk, "tavily_api_key": tk}})
        self._max_results, self._timeout, self._baidu_api_key, self._tavily_api_key = mr, to, bk, tk
        return Ok({"status": "saved"})

    # === Tavily ===
    def _tavily_search_sync(self, query: str, max_results: int) -> list:
        payload = {"api_key": self._tavily_api_key, "query": query, "search_depth": "basic", "max_results": max_results}
        req = urllib.request.Request("https://api.tavily.com/search",
            data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self._timeout, context=ssl.create_default_context()) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        results = []
        for item in data.get("results", []):
            if len(results) >= max_results: break
            t, h, s = str(item.get("title","")).strip(), str(item.get("url","")).strip(), str(item.get("content","")).strip()
            if t and h: results.append({"title": t, "url": h, "snippet": s})
        return results
    async def _tavily_search(self, q: str, m: int) -> list: return await asyncio.to_thread(self._tavily_search_sync, q, m)

    # === Baidu ===
    def _baidu_search_sync(self, query: str, max_results: int) -> list:
        if not self._baidu_api_key: raise RuntimeError("Baidu API Key not configured.")
        payload = {"messages": [{"role": "user", "content": query}], "search_source": "baidu_search_v2",
            "resource_type_filter": [{"type": "web", "top_k": max_results}],
            "block_websites": ["baike.baidu.com","hanyu.baidu.com","zdic.net","dict.baidu.com","zidian.baidu.com"]}
        headers = {"X-Appbuilder-Authorization": "Bearer {0}".format(self._baidu_api_key), "Content-Type": "application/json"}
        req = urllib.request.Request("https://qianfan.baidubce.com/v2/ai_search/web_search",
            data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=self._timeout, context=ssl.create_default_context()) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        if data.get("code"): raise RuntimeError(data.get("message", "Baidu request failed"))
        results = []
        for item in data.get("references", []):
            if len(results) >= max_results: break
            if item.get("type") != "web": continue
            t, h, s = str(item.get("title","")).strip(), str(item.get("url","")).strip(), str(item.get("content","")).strip()
            if t and h: results.append({"title": t, "url": h, "snippet": s})
        return results
    async def _baidu_search(self, q: str, m: int) -> list: return await asyncio.to_thread(self._baidu_search_sync, q, m)

    # === DuckDuckGo ===
    def _ddg_web_search_sync(self, query: str, max_results: int) -> list:
        req = urllib.request.Request("https://html.duckduckgo.com/html/",
            data=urllib.parse.urlencode({"q": query}).encode("utf-8"),
            headers={"User-Agent": "Mozilla/5.0 Chrome/120 Safari/537.36", "Content-Type": "application/x-www-form-urlencoded"})
        with urllib.request.urlopen(req, timeout=self._timeout, context=ssl.create_default_context()) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        results = []
        links = re.findall(r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>([^<]*)</a>', html)
        snips = re.findall(r'<a[^>]*class="result__snippet"[^>]*>([^<]*)</a>', html)
        for i, (href, title) in enumerate(links):
            if len(results) >= max_results: break
            if not title.strip() or not href.strip(): continue
            results.append({"title": title.strip(), "url": href.strip(), "snippet": (snips[i] if i < len(snips) else "").strip()})
        return results
    async def _ddg_web_search(self, q: str, m: int) -> list: return await asyncio.to_thread(self._ddg_web_search_sync, q, m)

    def _ddg_instant_answer_sync(self, query: str) -> dict:
        params = urllib.parse.urlencode({"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"})
        req = urllib.request.Request("https://api.duckduckgo.com/?{0}".format(params),
            headers={"User-Agent": "Mozilla/5.0 Chrome/120 Safari/537.36"})
        with urllib.request.urlopen(req, timeout=self._timeout, context=ssl.create_default_context()) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        result = {"query": query, "heading": data.get("Heading",""), "abstract": data.get("Abstract",""),
            "abstract_url": data.get("AbstractURL",""), "abstract_source": "DuckDuckGo",
            "answer": data.get("Answer",""), "answer_type": data.get("AnswerType",""), "related_topics": []}
        for topic in data.get("RelatedTopics", [])[:5]:
            if isinstance(topic, dict) and "Text" in topic:
                result["related_topics"].append({"text": topic["Text"], "url": topic.get("FirstURL","")})
        return result
    async def _ddg_instant_answer(self, q: str) -> dict: return await asyncio.to_thread(self._ddg_instant_answer_sync, q)