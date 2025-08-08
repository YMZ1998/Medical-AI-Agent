def md_to_text(md):
    import markdown2
    from bs4 import BeautifulSoup

    html = markdown2.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()

    # 去掉多余空行，只保留单个空行分隔段落
    lines = [line.strip() for line in text.splitlines()]
    filtered_lines = []
    for line in lines:
        if line != "":
            filtered_lines.append(line)
        else:
            # 避免连续多个空行
            if filtered_lines and filtered_lines[-1] != "":
                filtered_lines.append(line)
    return "\n".join(filtered_lines).strip()



if __name__ == "__main__":
    md = open("../README.md", "r", encoding="utf-8").read()
    print(md)
    print("-" * 100)
    print(md_to_text(md))

