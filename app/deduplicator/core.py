def find_exact_duplicates(texts: list[str]) -> list[list[int]]:
    """
    Finds exact duplicate texts in a list of texts.

    Args:
        texts: A list of strings.

    Returns:
        A list of lists, where each inner list contains the indices of duplicate texts.
    """
    duplicates = []
    seen_texts = {}
    for i, text in enumerate(texts):
        if text in seen_texts:
            seen_texts[text].append(i)
        else:
            seen_texts[text] = [i]

    for text_indices in seen_texts.values():
        if len(text_indices) > 1:
            duplicates.append(text_indices)

    return duplicates

def remove_exact_duplicates(texts: list[str]) -> list[str]:
    """
    Removes exact duplicate texts from a list of texts.

    Args:
        texts: A list of strings.

    Returns:
        A list of unique strings.
    """
    unique_texts = []
    seen_texts = set()
    for text in texts:
        if text not in seen_texts:
            unique_texts.append(text)
            seen_texts.add(text)
    return unique_texts

def find_near_duplicates(texts: list[str], similarity_threshold: float = 0.8) -> list[list[int]]:
    """
    Finds near-duplicate texts in a list of texts.

    Args:
        texts: A list of strings.
        similarity_threshold: The minimum similarity ratio for texts to be considered near-duplicates.

    Returns:
        A list of lists, where each inner list contains the indices of near-duplicate texts.
    """
    from difflib import SequenceMatcher
    # print(f"DEBUG: find_near_duplicates called with threshold {similarity_threshold}") # Optional: print threshold once
    num_texts = len(texts)
    if num_texts == 0:
        return []

    adj = [[] for _ in range(num_texts)]
    # 1. Build adjacency list for the graph
    for i in range(num_texts):
        for j in range(i + 1, num_texts):
            # Avoid re-calculating for (j,i) if (i,j) is done, though SM is cheap.
            # For robustness, ensure strings are used if they are not already.
            s1 = str(texts[i])
            s2 = str(texts[j])
            similarity = SequenceMatcher(None, s1, s2).ratio()
            # DEBUG PRINT (removed):
            # print(f"DEBUG: Texts '{s1}' vs '{s2}', Ratio: {similarity:.4f}, Threshold: {similarity_threshold}, Condition: {similarity >= similarity_threshold}")
            if similarity >= similarity_threshold:
                adj[i].append(j)
                adj[j].append(i)

    visited = [False] * num_texts
    duplicate_groups = []
    # 2. Find connected components (BFS/DFS)
    for i in range(num_texts):
        if not visited[i]:
            current_group_nodes = set() # Use set for efficient add and check during BFS traversal
            q = [i] # Queue for BFS
            visited[i] = True
            head = 0
            while head < len(q):
                u = q[head]
                head += 1
                current_group_nodes.add(u)
                for v in adj[u]:
                    if not visited[v]:
                        visited[v] = True
                        q.append(v)

            if len(current_group_nodes) > 1:
                # Sort nodes within the group for consistent output
                duplicate_groups.append(sorted(list(current_group_nodes)))

    # Sort the groups themselves for consistent test results, though not strictly necessary for functionality
    return sorted(duplicate_groups)
