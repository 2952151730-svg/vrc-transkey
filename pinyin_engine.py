import os
import sys
import json
from pathlib import Path
from typing import List, Tuple, Dict, Optional

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", BASE_DIR))
else:
    BASE_DIR = Path(__file__).resolve().parent
    BUNDLE_DIR = BASE_DIR

DATA_DIR = BASE_DIR / "data"
BASE_DICT_PATH = (DATA_DIR / "base_dict.tsv") if (DATA_DIR / "base_dict.tsv").exists() else (BUNDLE_DIR / "data" / "base_dict.tsv")
USER_DICT_PATH = DATA_DIR / "user_dict.json"

# 句尾高频语气助词（当最后一个音节只打声母如 l, m, b, n, a 时优先匹配）
SENTENCE_FINAL_PARTICLES = {
    "l": ("了", 60_000_000),
    "m": ("吗", 45_000_000),
    "b": ("吧", 45_000_000),
    "n": ("呢", 40_000_000),
    "a": ("啊", 40_000_000),
    "d": ("的", 50_000_000),
    "z": ("着", 25_000_000),
    "g": ("个", 30_000_000),
    "r": ("人", 25_000_000),
}

INITIAL_CONSONANTS = set("bpmfdtnlgkhjqxrzcsyw")
DIGRAPH_INITIALS = {"zh", "ch", "sh"}


class PinyinEngine:
    def __init__(self):
        self.full_map: Dict[str, List[Tuple[str, int]]] = {}       # 全拼 -> [(word, freq)]
        self.jianpin_map: Dict[str, List[Tuple[str, int]]] = {}    # 简拼 -> [(word, freq)]
        self.mixed_map: Dict[str, List[Tuple[str, int]]] = {}      # 混拼 (首字全拼+后续声母 或 末字声母) -> [(word, freq)]
        self.single_syllables = set()                              # 标准单字拼音音节集合
        self.single_char_map: Dict[str, List[Tuple[str, int]]] = {} # 单字音节 -> [(char, freq)]
        self.initial_char_map: Dict[str, List[Tuple[str, int]]] = {} # 声母 -> [(char, freq)]
        self.word_to_jp: Dict[str, str] = {}                      # 词语 -> 简拼 (支持自适应词频反向提权)
        self.user_history = {}                                     # {query: {word: count}}
        self.word_total_count = {}                                 # {word: count}

        self.load_user_dict()
        self.load_base_dict()

    def load_user_dict(self):
        """加载用户历史选词与自适应记忆"""
        if USER_DICT_PATH.exists():
            try:
                with open(USER_DICT_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.user_history = data.get("history", {})
                    self.word_total_count = data.get("words", {})
            except Exception as e:
                print(f"[PinyinEngine] 读取用户词频文件异常: {e}")
                self.user_history = {}
                self.word_total_count = {}

    def save_user_dict(self):
        """持久化保存用户自适应词频"""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(USER_DICT_PATH, "w", encoding="utf-8") as f:
                json.dump({
                    "history": self.user_history,
                    "words": self.word_total_count
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[PinyinEngine] 保存用户记忆词频失败: {e}")

    def record_choice(self, query: str, word: str):
        """记录用户选词习惯，使其在下次输入时自动提权置顶 (同时对该词的声母简拼生效)"""
        q = query.strip().lower()
        if not q or not word:
            return
        if q not in self.user_history:
            self.user_history[q] = {}
        self.user_history[q][word] = self.user_history[q].get(word, 0) + 1
        self.word_total_count[word] = self.word_total_count.get(word, 0) + 1

        # 同时为该词的简拼建立自适应联想记忆 (如用全拼输入 zhudong 选择 主动，下次输入 zd 时 主动 同样优先排在最前)
        jp = self.word_to_jp.get(word, "")
        if jp and jp != q:
            if jp not in self.user_history:
                self.user_history[jp] = {}
            self.user_history[jp][word] = self.user_history[jp].get(word, 0) + 1

        self.save_user_dict()

    def load_base_dict(self):
        if not BASE_DICT_PATH.exists():
            print(f"[PinyinEngine] 基础词典文件不存在: {BASE_DICT_PATH}")
            return

        t_entries = []
        with open(BASE_DICT_PATH, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 4:
                    word, full_py, jp, freq_str = parts[0], parts[1], parts[2], parts[3]
                    freq = int(freq_str) if freq_str.isdigit() else 100
                elif len(parts) >= 2:
                    word, full_py = parts[0], parts[1]
                    jp = ""
                    freq = int(parts[2]) if len(parts) >= 3 and parts[2].isdigit() else 100
                else:
                    continue

                t_entries.append((word, full_py, jp, freq))
                self.full_map.setdefault(full_py, []).append((word, freq))
                if jp:
                    self.jianpin_map.setdefault(jp, []).append((word, freq))
                    if word not in self.word_to_jp:
                        self.word_to_jp[word] = jp
                if len(word) == 1:
                    self.single_syllables.add(full_py)
                    self.single_char_map.setdefault(full_py, []).append((word, freq))
                    # 记录声母单字表
                    for init in ("zh", "ch", "sh", full_py[0]):
                        if full_py.startswith(init):
                            self.initial_char_map.setdefault(init, []).append((word, freq))
                            break

        # 构建全方位多音节混拼索引 (全方位支持简全混拼：首字母+后全拼、前声母+末全拼、首全拼+后声母等)
        # 针对前 ~46,000 高频常用词 (权重 >= 20,000) 建立极速混拼索引，兼顾 10 万+ 核心收词与超低内存占用
        for word, full_py, jp, freq in t_entries:
            if freq < 20000:
                continue
            if len(word) >= 2 and jp and len(jp) == len(word):
                syls = self.split_syllables_by_jp(full_py, jp)
                if syls and len(syls) == len(word):
                    # 1. 首字全拼 + 后续字声母 (例如: 喜欢 xih, 干嘛 ganm, 为什么 weism)
                    k1 = syls[0] + jp[1:]
                    if k1 != full_py and k1 != jp:
                        self.mixed_map.setdefault(k1, []).append((word, freq))

                    # 2. 首字声母 + 后续字全拼 (例如: 喜欢 xhuan, 干嘛 gma, 不知道 bzhidao, 对不起 dbuqi, 没关系 mguanxi)
                    k2 = jp[0] + "".join(syls[1:])
                    if k2 != full_py and k2 != jp:
                        self.mixed_map.setdefault(k2, []).append((word, freq))

                    if len(syls) >= 3:
                        # 3. 前 N-1 声母 + 末字全拼 (例如: 你干嘛 ngma, 不好了 bhle, 怎么了 zmle, 为什么 wsme)
                        k3 = jp[:-1] + syls[-1]
                        if k3 != full_py and k3 != jp:
                            self.mixed_map.setdefault(k3, []).append((word, freq))

                        # 4. 前 N-1 全拼 + 末字声母 (例如: 你干嘛 niganm, 掉线了 diaoxianl, 烦死了 fansil)
                        k4 = "".join(syls[:-1]) + jp[-1]
                        if k4 != full_py and k4 != jp:
                            self.mixed_map.setdefault(k4, []).append((word, freq))

                        # 5. 三字词特化：首声母 + 中全拼 + 末声母 (例如: 你干嘛 nganm, 不回了 nbhl)
                        if len(syls) == 3:
                            k5 = jp[0] + syls[1] + jp[2]
                            if k5 != full_py and k5 != jp:
                                self.mixed_map.setdefault(k5, []).append((word, freq))

        # 预排序所有桶，保证高词频在前
        for d in (self.full_map, self.jianpin_map, self.mixed_map, self.single_char_map, self.initial_char_map):
            for k in d:
                d[k].sort(key=lambda x: x[1], reverse=True)

        print(f"[PinyinEngine] 智能拼音引擎就绪: {len(t_entries)} 词目 (支持全拼/简拼/混拼/整句词图切分/分步选词)")

    def split_syllables_by_jp(self, full_py: str, jp: str) -> Optional[List[str]]:
        """利用简拼声母序列约束，将连续拼音精准切分为单字音节列表"""
        k = len(jp)
        if k <= 1:
            return [full_py]
        n = len(full_py)

        def backtrack(s_idx: int, j_idx: int) -> Optional[List[str]]:
            if j_idx == k:
                return [] if s_idx == n else None
            target_init = jp[j_idx]
            rem_len = n - s_idx
            if rem_len < (k - j_idx):
                return None
            for l in range(min(6, rem_len - (k - j_idx - 1)), 0, -1):
                sub = full_py[s_idx:s_idx + l]
                if sub in self.single_syllables and sub.startswith(target_init):
                    tail = backtrack(s_idx + l, j_idx + 1)
                    if tail is not None:
                        return [sub] + tail
            return None

        return backtrack(0, 0)

    def segment_syllables(self, text: str) -> List[Tuple[str, str, int, int]]:
        """
        使用动态规划将拼音串切分为最少音节序列:
        返回 [(token, type, start_idx, end_idx), ...]
        type: 'full' (完整音节) | 'init' (声母简拼)
        """
        n = len(text)
        if n == 0:
            return []

        # dp[i] = (cost, path_list)
        dp = [(float("inf"), []) for _ in range(n + 1)]
        dp[0] = (0.0, [])

        for i in range(n):
            base_cost, base_path = dp[i]
            if base_cost == float("inf"):
                continue

            # 1. 尝试匹配完整单字音节 (长度 1~6)
            for length in range(min(6, n - i), 0, -1):
                sub = text[i:i + length]
                if sub in self.single_syllables:
                    # 越长的合法音节略微优先，避免把 xian 拆成 xi + an
                    step_cost = 1.0 - (length * 0.03)
                    # 如果把鼻音韵尾 n/g 强行拆给下一音节但下一音节不合法，则自然在后续淘汰
                    new_cost = base_cost + step_cost
                    if new_cost < dp[i + length][0]:
                        dp[i + length] = (new_cost, base_path + [(sub, "full", i, i + length)])

            # 2. 尝试匹配翘舌音声母 zh, ch, sh
            if i + 2 <= n and text[i:i + 2] in DIGRAPH_INITIALS:
                sub = text[i:i + 2]
                new_cost = base_cost + 1.32
                if new_cost < dp[i + 2][0]:
                    dp[i + 2] = (new_cost, base_path + [(sub, "init", i, i + 2)])

            # 3. 尝试匹配单字母声母
            if text[i] in INITIAL_CONSONANTS:
                sub = text[i]
                new_cost = base_cost + 1.38
                if new_cost < dp[i + 1][0]:
                    dp[i + 1] = (new_cost, base_path + [(sub, "init", i, i + 1)])

        return dp[n][1]

    def _compose_from_lattice(self, tokens: List[Tuple[str, str, int, int]]) -> List[Tuple[str, int, int]]:
        """
        基于音节切分序列进行词图动态规划组词 (Word-Lattice Viterbi DP)
        例如:
          ['wo', 'xi', 'huan', 'ni'] -> '我' + '喜欢' + '你' = '我喜欢你'
          ['diao', 'xian', 'l']      -> '掉线' + '了' = '掉线了'
          ['fan', 'si', 'l']         -> '烦死' + '了' = '烦死了'
          ['hao', 'fan', 'a']        -> '好烦' + '啊' = '好烦啊'
        返回: [(composed_word, consumed_char_len, score), ...]
        """
        m = len(tokens)
        if m == 0:
            return []

        results = []

        # 辅助函数：获取跨度 tokens[i:j] 的最佳词及权重
        def get_span_candidates(i: int, j: int) -> List[Tuple[str, float]]:
            span = tokens[i:j]
            span_len = j - i
            raw_py = "".join(t[0] for t in span)
            all_full = all(t[1] == "full" for t in span)

            cands = []
            if span_len == 1:
                tok, ttype, _, _ = span[0]
                if ttype == "full" and tok in self.single_char_map:
                    for w, f in self.single_char_map[tok][:6]:
                        cands.append((w, float(f)))
                else:
                    # 句尾助词特化增强 (如句末打 l -> 了, m -> 吗, b -> 吧)
                    if j == m and tok in SENTENCE_FINAL_PARTICLES:
                        pw, pf = SENTENCE_FINAL_PARTICLES[tok]
                        cands.append((pw, float(pf)))
                    if tok in self.initial_char_map:
                        for w, f in self.initial_char_map[tok][:6]:
                            cands.append((w, float(f) * 0.6))
            else:
                # 多字词跨度匹配 (极大地优先于单字拼接)
                multi_bonus = 40.0 * (span_len ** 2)
                if all_full and raw_py in self.full_map:
                    for w, f in self.full_map[raw_py]:
                        if len(w) == span_len:
                            cands.append((w, float(f) * multi_bonus))
                            if len(cands) >= 8:
                                break
                if raw_py in self.mixed_map:
                    for w, f in self.mixed_map[raw_py]:
                        if len(w) == span_len:
                            cands.append((w, float(f) * multi_bonus * 0.9))
                            if len(cands) >= 8:
                                break
                if not all_full and raw_py in self.jianpin_map:
                    for w, f in self.jianpin_map[raw_py]:
                        if len(w) == span_len:
                            cands.append((w, float(f) * multi_bonus * 0.75))
                            if len(cands) >= 8:
                                break
            return cands

        # Viterbi DP 求整句最优组合 (0 -> m)
        # dp[idx] = [(score, word_str), ...]
        dp: List[List[Tuple[float, str]]] = [[] for _ in range(m + 1)]
        dp[0] = [(1.0, "")]

        for i in range(m):
            if not dp[i]:
                continue
            for j in range(min(m, i + 4), i, -1):
                span_cands = get_span_candidates(i, j)
                if not span_cands:
                    continue
                for prev_score, prev_word in dp[i][:6]:
                    for w, s in span_cands[:6]:
                        # 跨度越长，路径惩罚越小（鼓励合成词而非碎单字）
                        new_score = prev_score + s + (100_000_000.0 if (j - i) >= 2 else 0.0)
                        dp[j].append((new_score, prev_word + w))
                dp[j].sort(key=lambda x: x[0], reverse=True)
                # 去重保留前 12
                seen = set()
                pruned = []
                for sc, wd in dp[j]:
                    if wd not in seen:
                        seen.add(wd)
                        pruned.append((sc, wd))
                    if len(pruned) >= 12:
                        break
                dp[j] = pruned

        total_char_len = tokens[-1][3]
        for idx, (sc, wd) in enumerate(dp[m][:12]):
            results.append((wd, total_char_len, 700_000_000 - idx * 10_000_000))

        # 同时提供首词/前两音节的分步候选 (例如输入 woxihuanni，除整句“我喜欢你”外，还提供前两音节或首字“我”)
        if m >= 2:
            # 前 2 音节词
            c2 = get_span_candidates(0, 2)
            len2 = tokens[1][3]
            for idx, (w, _) in enumerate(c2[:5]):
                results.append((w, len2, 350_000_000 - idx * 5_000_000))
        if m >= 1:
            # 首音节单字
            c1 = get_span_candidates(0, 1)
            len1 = tokens[0][3]
            for idx, (w, _) in enumerate(c1[:5]):
                results.append((w, len1, 250_000_000 - idx * 5_000_000))

        return results

    def search_with_span(self, raw_input: str, max_results: int = 40) -> List[Tuple[str, int]]:
        """
        输入拼音串，返回 [(候选词, 消耗的拼音字母长度), ...]
        支持全拼、简拼、混拼、整句智能组词与分步上屏。
        """
        query = raw_input.strip().lower()
        if not query:
            return []

        qlen = len(query)
        # word -> (score, consumed_len)
        scored_candidates: Dict[str, Tuple[int, int]] = {}

        def add_cand(w: str, score: int, consumed: int):
            if w not in scored_candidates or score > scored_candidates[w][0]:
                scored_candidates[w] = (score, consumed)

        # 1. 全拼精确匹配 (最高优先级: +1,000,000,000)
        if query in self.full_map:
            for w, f in self.full_map[query]:
                add_cand(w, 1_000_000_000 + f, qlen)

        # 2. 混拼精确匹配 (如 fansil -> 烦死了, diaox -> 掉线, xih -> 喜欢: +900,000,000)
        if query in self.mixed_map:
            for w, f in self.mixed_map[query]:
                add_cand(w, 900_000_000 + f, qlen)

        # 3. 翘舌音/单声母高频单字匹配 (如 w -> 我, zh -> 这/中, sh -> 是/说)
        if query in self.initial_char_map:
            for w, f in self.initial_char_map[query][:8]:
                add_cand(w, 840_000_000 + f, qlen)

        # 4. 声母简拼精确匹配 (如 zg -> 这个/中国, fsl -> 烦死了, wsm -> 为什么: +820,000,000)
        if query in self.jianpin_map:
            for w, f in self.jianpin_map[query]:
                add_cand(w, 820_000_000 + f, qlen)

        # 5. 词图动态规划组词与分步选词 (如 woxihuanni -> 我喜欢你, diaoxianl -> 掉线了, haofana -> 好烦啊)
        tokens = self.segment_syllables(query)
        if len(tokens) >= 2:
            lattice_cands = self._compose_from_lattice(tokens)
            for w, consumed, sc in lattice_cands:
                add_cand(w, sc, consumed)

        # 6. 前缀联想与单音节常用词补充
        is_complete_single = query in self.single_syllables
        if is_complete_single:
            # 如果是完整单音节 (如 fan)，在排好单字后，补充以该音节开头的常用双字词 (如 烦人、翻译、反对)，严格排除后鼻音 fang!
            prefix_matches = []
            for py, items in self.full_map.items():
                if len(py) > qlen and py.startswith(query):
                    if query.endswith("n") and py[qlen] == "g":
                        continue
                    if py[qlen:] in self.single_syllables:
                        for w, f in items[:2]:
                            prefix_matches.append((w, f))
            prefix_matches.sort(key=lambda x: x[1], reverse=True)
            for w, f in prefix_matches[:12]:
                add_cand(w, 400_000_000 + f, qlen)
        elif len(scored_candidates) < 20:
            # 针对尚未输完的拼音前缀收集全部前缀候选并按真实词频排序（绝不提前截断）
            prefix_matches = []
            for py, items in self.full_map.items():
                if py.startswith(query):
                    for w, f in items[:2]:
                        prefix_matches.append((w, f))
            prefix_matches.sort(key=lambda x: x[1], reverse=True)
            for w, f in prefix_matches[:20]:
                add_cand(w, 300_000_000 + f, qlen)

        if not scored_candidates:
            return [(query, qlen)]

        # 始终提供输入字符串本身的英文直出候选项 (方便输入诸如 bug, vrc, ok, fps 等英文单词)
        if query and query not in scored_candidates:
            add_cand(query, 10_000, qlen)

        # 6. 结合用户历史选择频次动态提权置顶
        query_user_prefs = self.user_history.get(query, {})
        final_list = []
        for word, (base_score, consumed) in scored_candidates.items():
            u_query_count = query_user_prefs.get(word, 0)
            u_total_count = self.word_total_count.get(word, 0)
            final_score = base_score + (u_query_count * 5_000_000_000) + (u_total_count * 50_000_000)
            final_list.append((word, consumed, final_score))

        final_list.sort(key=lambda x: x[2], reverse=True)
        return [(w, c) for w, c, _ in final_list[:max_results]]

    def search(self, raw_input: str, max_results: int = 40) -> List[str]:
        """兼容接口：返回纯候选词字符串列表"""
        return [w for w, _ in self.search_with_span(raw_input, max_results=max_results)]

    def get_paged_candidates(self, query: str, page: int = 0, page_size: int = 5):
        candidates_with_span = self.search_with_span(query, max_results=45)
        start = page * page_size
        end = start + page_size
        paged = candidates_with_span[start:end]
        has_next = end < len(candidates_with_span)
        has_prev = page > 0
        return paged, has_prev, has_next, len(candidates_with_span)
