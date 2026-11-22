**按次计费的配音也要预算：MiniMax 按量付费、ElevenLabs、阿里云百炼没写预算就不调**
- Why: Studio 设置页存的 key 现在每条命令都读得到，Studio 对话里的 agent 也能调这几家收费的配音；出图和 Lyria 作曲早就要预算，配音还是直接调用、花账户的钱。
- `bin/vh tts` 和 `bin/vh voices audition` 用 `elevenlabs`、`dashscope`，或者只有按量付费 key（`MINIMAX_API_KEY`）的 `minimax` 时，先读片子的预算（BRIEF 的 `Budget:`，没有再看 `LOCAL.md` 的默认预算）。没有预算、预算是 0，或者这次会超出，就不调，说清要写什么、还差多少；这一步在发出第一个请求、删掉旧配音之前。缺 key 和缺预算都有时，先说缺 key。
- 每个请求先按字数占住估价，回答回来按它报的计费字数结账（MiniMax 的 `usage_characters`、百炼的 `usage.characters`），记进片子的 `assets/spend.jsonl`；结束时多一行：几个请求、花了多少、预算还剩多少。ElevenLabs 的回答不报字数，按估价记，是上限（套餐里含的字数不按次扣），那一行和账上都写明。报错的回答和没发出去的请求记 0；超时的保留估价，并且说可能已经扣了。
- 价格照各家价格页（2026-11-22 读，页面地址写在 `tools/audio/speechcost.py` 里，`python3 tools/audio/speechcost.py` 列出）：MiniMax 国际站 speech-2.8-hd 每百万字符 $100、turbo $60，国内站每万字符 ¥3.5、¥2；ElevenLabs 多语种 v2 每千字符 $0.08；百炼 qwen3-tts-flash 北京每万字符 ¥0.8、新加坡 $0.1。MiniMax 和百炼的页面说一个汉字算 2 个字符，这里所有非 ASCII 字符都按 2 个算，估价只多不少。表里没有的模型按同一接入点最贵的模型算，并说明是估的；表里没有的接入点（比如代理），只要有不为 0 的预算就调，记成"价钱不知道，可能已扣费"。
- 试音按文本文件所在的片子读预算、记账；文本不在任何片子里时不调。
- 照旧用，不要预算：本机的声音（`qwen`、`say`）、不要 key 的 `edge`、Gemini 配音和 `--align gemini`（先用免费额度）、MiniMax 的 Token Plan key（花套餐额度，tts 先用它）。
- 两个预算占位在同一毫秒里时，记账的编号以前会重，结掉一个会把另一个也当成结了；编号现在加了一个计数。
- Studio 设置页和 README"API Key"一节关于预算的那句话照新规则改了。
