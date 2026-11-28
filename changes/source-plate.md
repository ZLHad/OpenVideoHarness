**新组件 `source-plate`：标明出处的铭牌，停多久、字多大由组件兜住**
- Why: 人名、论文、数据和原话的出处，每支片子都在手写一块牌子，常见的两处翻车都是底线：牌子没停够读一遍的时间，标签和 DOI 这类小字低于辅助字的下限。把这两条做成组件的默认行为，比每支片子各自记得要可靠。
- `components/source-plate`：一块铭牌写人物（名字、身份）、论文（题目，作者、刊物和年份，DOI）、数据或原话的出处，标签按 `kind` 和 `lang` 自动给（人物、论文、数据、原话、出处）。不写 `hold` 时，它按 BRIEF 的 Pace 算够读完全部字的时间，算法和 `bin/vh readcheck` 一样；给的 `hold` 低于底线（快读一遍，至少 1.5 秒）会被拉长到底线。没有一行字小于 `floor`（默认 44 px，`feed` 档写 80）。长的论文题目按词换行，中文按字。
- `texts()` 把铭牌上的每一行交给 `window.film.texts`，`bin/vh readcheck` 和 `textcheck` 直接量得到；`boxes()` 给 `window.film.ui(t)`；canvas 和 DOM 两种落笔，DOM 只动 transform、opacity 和 clip-path。标签放在强调色的小色块上，字用黑或白，按色块颜色挑对比高的那个。
- 在这台 Linux x86_64 机器上用 `--engine page` 做了一支 10 秒的有声验证片来试它：第一版里强调色的红字标签压在深色底板上只有 2.5:1，`bin/vh textcheck` 判了失败，所以改成了现在的色块。README、官网和概览图里的组件数从 7 改成 8。
