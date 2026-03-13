"""Aho-Corasick trie construction: goto function and BFS failure function."""
from collections import deque


def build_automaton(patterns: list[str]) -> tuple[list[dict], list[list[int]], list[int]]:
    """Build the Aho-Corasick automaton for the given patterns.

    Returns:
        goto:   goto[state][ch] = next_state
        output: output[state]   = list of pattern indices that end at state
        fail:   fail[state]     = failure link state
    """
    goto: list[dict] = [{}]
    output: list[list[int]] = [[]]
    fail: list[int] = [0]

    # Step 1: build goto (trie insertion)
    for idx, pattern in enumerate(patterns):
        cur = 0
        for ch in pattern:
            if ch not in goto[cur]:
                goto[cur][ch] = len(goto)
                goto.append({})
                output.append([])
                fail.append(0)
            cur = goto[cur][ch]
        output[cur].append(idx)

    # Step 2: build failure function using BFS
    queue: deque[int] = deque()

    # Depth-1 nodes: failure link = root (0)
    for ch, s in goto[0].items():
        fail[s] = 0
        queue.append(s)

    while queue:
        r = queue.popleft()
        for ch, s in goto[r].items():
            queue.append(s)
            # Walk up failure links to find longest proper suffix that is a trie prefix
            state = fail[r]
            while state != 0 and ch not in goto[state]:
                state = fail[state]
            fail[s] = goto[state].get(ch, 0)
            if fail[s] == s:
                fail[s] = 0
            # Union output with failure link's output
            output[s] = output[s] + output[fail[s]]

    return goto, output, fail
