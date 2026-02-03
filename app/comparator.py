# from rapidfuzz import fuzz
# from difflib import SequenceMatcher


# def highlight_diff(master_text, test_text):

#     matcher = SequenceMatcher(None, master_text.split(), test_text.split())

#     master_out = []
#     test_out = []

#     for tag, i1, i2, j1, j2 in matcher.get_opcodes():

#         master_chunk = " ".join(master_text.split()[i1:i2])
#         test_chunk = " ".join(test_text.split()[j1:j2])

#         if tag == "equal":
#             master_out.append(master_chunk)
#             test_out.append(test_chunk)

#         elif tag == "delete":
#             master_out.append(
#                 f"<span style='background-color:#ffb3b3'>{master_chunk}</span>"
#             )

#         elif tag == "insert":
#             test_out.append(
#                 f"<span style='background-color:#b3ffb3'>{test_chunk}</span>"
#             )

#         elif tag == "replace":
#             master_out.append(
#                 f"<span style='background-color:#ffcc99'>{master_chunk}</span>"
#             )

#             test_out.append(
#                 f"<span style='background-color:#ffcc99'>{test_chunk}</span>"
#             )

#     return " ".join(master_out), " ".join(test_out)


# def compare_pages(master, normal):

#     results = []

#     max_pages = max(len(master), len(normal))

#     for i in range(1, max_pages + 1):

#         m = master.get(i, "")
#         n = normal.get(i, "")

#         if not m:
#             results.append({
#                 "page": i,
#                 "status": "EXTRA PAGE 🚨",
#                 "score": 0,
#                 "master": "",
#                 "test": "<span style='background:#b3ffb3'>Entire page added</span>"
#             })
#             continue

#         if not n:
#             results.append({
#                 "page": i,
#                 "status": "MISSING PAGE 🚨",
#                 "score": 0,
#                 "master": "<span style='background:#ffb3b3'>Page removed</span>",
#                 "test": ""
#             })
#             continue

#         score = fuzz.token_ratio(m, n)

#         if score > 100:
#             status = "IDENTICAL ✅"
#             master_html = m
#             test_html = n
#         else:

#             if score > 85:
#                 status = "MINOR CHANGE ⚠"
#             else:
#                 status = "MAJOR CHANGE 🚨"

#             master_html, test_html = highlight_diff(m, n)

#         results.append({
#             "page": i,
#             "status": status,
#             "score": score,
#             "master": master_html,
#             "test": test_html
#         })

#     return results


import re
from rapidfuzz import fuzz
from difflib import SequenceMatcher
from nltk.tokenize import sent_tokenize
import nltk

nltk.download('punkt')
nltk.download('punkt_tab')


# =====================================================
# NORMALIZATION (Formatting Immunity)
# =====================================================

def normalize(text):

    text = text.lower()

    text = re.sub(r'\s+', ' ', text)

    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("’", "'")

    return text.strip()


# =====================================================
# SENTENCE SPLITTER
# =====================================================

def split_sentences(text):

    text = normalize(text)

    return sent_tokenize(text)


# =====================================================
# NUMBER DETECTOR
# =====================================================

number_pattern = re.compile(r'\$?\d+(?:,\d{3})*(?:\.\d+)?%?')


def extract_numbers(text):
    return number_pattern.findall(text)


# =====================================================
# RISK ENGINE
# =====================================================

def risk_score(master, test):

    risk = 0
    reasons = []

    master_nums = set(extract_numbers(master))
    test_nums = set(extract_numbers(test))

    if master_nums != test_nums:
        risk += 5
        reasons.append("💰 Financial / numeric value changed")

    keywords = [
        "liability",
        "termination",
        "penalty",
        "confidential",
        "payment",
        "insurance"
    ]

    for k in keywords:
        if k in master and k not in test:
            risk += 3
            reasons.append(f"⚠ Clause removed: {k}")

        if k not in master and k in test:
            risk += 3
            reasons.append(f"⚠ Clause added: {k}")

    return risk, reasons


# =====================================================
# HIGHLIGHT ENGINE
# =====================================================

def highlight(master, test):

    matcher = SequenceMatcher(None, master.split(), test.split())

    m_out = []
    t_out = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():

        m_chunk = " ".join(master.split()[i1:i2])
        t_chunk = " ".join(test.split()[j1:j2])

        if tag == "equal":
            m_out.append(m_chunk)
            t_out.append(t_chunk)

        elif tag == "delete":
            m_out.append(
                f"<span style='background:#ffb3b3'>{m_chunk}</span>"
            )

        elif tag == "insert":
            t_out.append(
                f"<span style='background:#b3ffb3'>{t_chunk}</span>"
            )

        else:  # replace
            m_out.append(
                f"<span style='background:#ffd699'>{m_chunk}</span>"
            )

            t_out.append(
                f"<span style='background:#ffd699'>{t_chunk}</span>"
            )

    return " ".join(m_out), " ".join(t_out)


# =====================================================
# SMART COMPARATOR
# =====================================================

def smart_compare(master_text, test_text):

    master_sent = split_sentences(master_text)
    test_sent = split_sentences(test_text)

    used = set()
    results = []

    for m in master_sent:

        best_score = 0
        best_match = None
        best_idx = None

        for i, t in enumerate(test_sent):

            if i in used:
                continue

            score = fuzz.token_sort_ratio(m, t)

            if score > best_score:
                best_score = score
                best_match = t
                best_idx = i

        if best_match is None:
            results.append({
                "type": "REMOVED 🚨",
                "master": m,
                "test": "",
                "risk": 4,
                "reasons": ["Sentence removed"]
            })
            continue

        used.add(best_idx)

        if normalize(m) == normalize(best_match):
            continue  # identical → skip noise

        risk, reasons = risk_score(m, best_match)

        if best_score > 90:
            change_type = "MODIFIED ⚠"
        else:
            change_type = "MAJOR CHANGE 🚨"
            risk += 2

        m_html, t_html = highlight(m, best_match)

        results.append({
            "type": change_type,
            "master": m_html,
            "test": t_html,
            "risk": risk,
            "reasons": reasons
        })

    # detect added sentences
    for i, t in enumerate(test_sent):
        if i not in used:
            results.append({
                "type": "ADDED 🚨",
                "master": "",
                "test": f"<span style='background:#b3ffb3'>{t}</span>",
                "risk": 4,
                "reasons": ["New sentence added"]
            })




    # build full document highlight
        master_html, test_html = full_document_highlight(
            master_text,
            test_text
        )

        total_risk = sum(r["risk"] for r in results)

        all_reasons = list({
            reason
            for r in results
            for reason in r["reasons"]
        })

        return {
            "changes": sorted(results, key=lambda x: -x["risk"]),
            "master_html": master_html,
            "test_html": test_html,
            "risk": total_risk,
            "reasons": all_reasons
        }



def full_document_highlight(master_text, test_text):

    matcher = SequenceMatcher(None, master_text.split(), test_text.split())

    master_out = []
    test_out = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():

        m_chunk = " ".join(master_text.split()[i1:i2])
        t_chunk = " ".join(test_text.split()[j1:j2])

        if tag == "equal":
            master_out.append(m_chunk)
            test_out.append(t_chunk)

        elif tag == "delete":
            master_out.append(
                f"<span style='background:#ffb3b3'>{m_chunk}</span>"
            )

        elif tag == "insert":
            test_out.append(
                f"<span style='background:#b3ffb3'>{t_chunk}</span>"
            )

        else:
            master_out.append(
                f"<span style='background:#ffd699'>{m_chunk}</span>"
            )

            test_out.append(
                f"<span style='background:#ffd699'>{t_chunk}</span>"
            )

    return " ".join(master_out), " ".join(test_out)
