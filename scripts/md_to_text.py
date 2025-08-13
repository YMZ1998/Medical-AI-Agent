def md_to_text(md):
    import markdown2
    from bs4 import BeautifulSoup

    html = markdown2.markdown(md)
    soup = BeautifulSoup(html, "html.parser")

    def process_list(tag, level=0, ordered=False):
        """递归处理列表，保留编号或符号，并保持缩进"""
        items = []
        if ordered:
            start = int(tag.get("start", 1))
        for li in tag.find_all("li", recursive=False):
            prefix = " " * (level * 4)  # 每级缩进 4 空格
            if ordered:
                prefix += f"{start}. "
                start += 1
            else:
                prefix += "• "
            text_parts = []
            for child in li.children:
                if child.name == "ul":
                    text_parts.append("\n" + process_list(child, level+1, ordered=False))
                elif child.name == "ol":
                    text_parts.append("\n" + process_list(child, level+1, ordered=True))
                else:
                    text_parts.append(child.get_text(strip=True) if hasattr(child, 'get_text') else str(child))
            items.append(prefix + "".join(text_parts).strip())
        return "\n".join(items)

    output_lines = []
    for elem in soup.body.contents if soup.body else soup.contents:
        if elem.name == "ul":
            output_lines.append(process_list(elem, ordered=False))
        elif elem.name == "ol":
            output_lines.append(process_list(elem, ordered=True))
        else:
            text = elem.get_text(strip=True) if hasattr(elem, 'get_text') else str(elem)
            if text:
                output_lines.append(text)

    # 直接拼接，不加空行
    return "\n".join(line.strip() for line in output_lines if line.strip())



if __name__ == "__main__":
    md = open("../README.md", "r", encoding="utf-8").read()
    print(md)
    print("-" * 100)
    print(md_to_text(md))
