import { Page, Card, Section, Stack, Field, Input, Text, Button, Alert } from "@neko/plugin-ui"
import type { PluginSurfaceProps } from "@neko/plugin-ui"
import { useLocalState } from "@neko/plugin-ui"

type State = { config: { max_results: number; timeout: number; baidu_api_key: string; tavily_api_key: string } }

export default function SettingsPanel(props: PluginSurfaceProps<State>) {
  const { state } = props
  const [mr, setMr] = useLocalState("mr", () => state.config?.max_results ?? 5)
  const [to, setTo] = useLocalState("to", () => state.config?.timeout ?? 15)
  const [bak, setBak] = useLocalState("bak", () => state.config?.baidu_api_key ?? "")
  const [tak, setTak] = useLocalState("tak", () => state.config?.tavily_api_key ?? "")
  const [saving, sv, sd, er] = [useLocalState("sg",()=>false), useLocalState("sd",()=>false), useLocalState("st",()=>false), useLocalState("er",()=>"")]
  const [savingState, setSaving] = saving; const [saved, setSaved] = sv; const [error, setError] = er
  const [lang, setLang] = useLocalState("ln", () => "zh-CN")
  const _t = (z: string, e: string) => lang === "en" ? e : z
  const cfg = () => ({ max_results: Number(mr) || 5, timeout: Number(to) || 15, baidu_api_key: String(bak).trim(), tavily_api_key: String(tak).trim() })

  async function handleSave() {
    setSaving(true); setError(""); setSaved(false)
    // Try V1-compatible ID first, fallback to V2 ID
    for (const id of ["update_settings", "save_settings"]) {
      try {
        await props.api.call(id, { config: cfg() })
        await props.api.refresh()
        setSaved(true); setTimeout(() => setSaved(false), 2000)
        return
      } catch {}
    }
    setError(_t("保存失败：请检查面板权限", "Save failed: check panel permissions"))
    setSaving(false)
  }

  return (
    <Page title="Web Search">
      <Section>
        <Button tone="default" onClick={() => setLang(lang === "zh-CN" ? "en" : "zh-CN")}>
          {lang === "zh-CN" ? "English" : "中文"}
        </Button>
        <Alert>{_t("配置百度或 Tavily API 密钥。留空自动使用 DuckDuckGo。",
          "Configure Baidu or Tavily API key. Falls back to DuckDuckGo when blank.")}</Alert>
        {error && <Alert><Text>{error}</Text></Alert>}
      </Section>
      <Card title={_t("搜索设置", "Search Settings")}>
        <Stack>
          <Field label={_t("返回条数 (1-10)", "Max Results (1-10)")}>
            <Input value={String(mr)} onChange={(v) => setMr(Math.max(1, Math.min(10, Number(v) || 5)))} />
          </Field>
          <Field label={_t("超时 (5-60s)", "Timeout (5-60s)")}>
            <Input value={String(to)} onChange={(v) => setTo(Math.max(5, Math.min(60, Number(v) || 15)))} />
          </Field>
          <Field label="Baidu AppBuilder API Key">
            <Input value={String(bak)} onChange={(v) => setBak(v)} />
          </Field>
          <Field label="Tavily API Key">
            <Input value={String(tak)} onChange={(v) => setTak(v)} />
          </Field>
          <Button tone={saved ? "success" : "primary"} onClick={handleSave} disabled={savingState}>
            {savingState ? _t("保存中…", "Saving…") : saved ? _t("已保存 ✓", "Saved ✓") : _t("保存设置", "Save Settings")}
          </Button>
        </Stack>
      </Card>
      <Card title={_t("使用提示", "Usage Tips")}>
        <Stack>
          <Text color="secondary">{_t("和猫娘对话时直接说：", "Ask your neko:")}</Text>
          <Text color="muted">{lang === "en" ? "- \"Search for today's news\"" : "- \"帮我搜一下今天的新闻\""}</Text>
          <Text color="muted">{lang === "en" ? "- \"What's the latest Python version\"" : "- \"Python 最新版本是多少\""}</Text>
          <Text color="muted">{lang === "en" ? "- \"Where is the typhoon\"" : "- \"台风现在到哪里了\""}</Text>
        </Stack>
      </Card>
    </Page>
  )
}