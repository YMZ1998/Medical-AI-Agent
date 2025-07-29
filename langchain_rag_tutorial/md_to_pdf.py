import markdown
import pdfkit

with open('./data/test.md', 'r', encoding='utf-8') as f:
    md_text = f.read()

html_text = markdown.markdown(md_text)

print(html_text)

pdfkit.from_string(html_text, './data/books/test2.pdf')
