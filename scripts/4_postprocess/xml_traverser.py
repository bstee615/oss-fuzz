import xml.etree.ElementTree as ET


def dfs(node, calls):
    if node.tag == "call":
        calls.append(node)
    for child in node:
        dfs(child, calls)


def get_calls(root):
    calls = []
    dfs(root, calls)
    return calls


# %%
if __name__ == "__main__":
    root = ET.parse('traces-1m-worker_3_overnight_portclash/trace-angus-mail-BASE64EncoderStreamFuzzer.xml').getroot()
    calls = get_calls(root)
