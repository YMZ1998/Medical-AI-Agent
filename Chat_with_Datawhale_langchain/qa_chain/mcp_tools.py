import os
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
from Chat_with_Datawhale_langchain.utils.call_embedding import get_embedding
from api_config import api_config


def delete_md_files(folder: str):
    count = 0
    for filename in os.listdir(folder):
        if filename.endswith(".md"):
            file_path = os.path.join(folder, filename)
            try:
                os.remove(file_path)
                print(f"已删除: {file_path}")
                count += 1
            except Exception as e:
                print(f"删除失败: {file_path}，原因: {e}")
    print(f"✅ 共删除 {count} 个 .md 文件")


class InstructionDetector:
    def __init__(self, embeddings, texts: list[str], threshold: float = 0.75):
        self.embeddings = embeddings
        self.texts = texts
        self.threshold = threshold
        self.text_embs = self.embeddings.embed_documents(texts)
        self.dir_path = "chat_logs"

    def match(self, text: str) -> bool:
        text = text.strip()
        if not text:
            return False
        emb = self.embeddings.embed_query(text)
        sims = cosine_similarity([emb], self.text_embs)[0]
        max_sim = max(sims)
        print(f"[DEBUG] 相似度 = {max_sim:.4f}")
        return max_sim >= self.threshold


class ChatSaver:
    def __init__(self, folder: str = "chat_logs"):
        self.folder = folder
        os.makedirs(folder, exist_ok=True)

    def save(self, chat_history: list[str]) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.folder, f"chat_history_{timestamp}.md")
        with open(filename, "w", encoding="utf-8") as f:
            for msg in chat_history:
                f.write(msg + "\n\n")
        print(f"✅ 聊天记录已保存至: {filename}")
        return filename


class SemanticTool:
    def __init__(self, name, examples, handler, embeddings, threshold=0.75):
        self.name = name
        self.detector = InstructionDetector(embeddings, examples, threshold)
        self.handler = handler

    def try_handle(self, text: str):
        if self.detector.match(text):
            print(f"[DEBUG] 语义匹配触发工具：{self.name}")
            return self.handler(text)
        return None


class ToolRegistry:
    def __init__(self):
        self.tools: list[SemanticTool] = []

    def register_tool(self, tool: SemanticTool):
        self.tools.append(tool)

    def match_tool(self, text: str):
        for tool in self.tools:
            result = tool.try_handle(text)
            if result is not None:
                return result
        return None


class ChatSession:
    def __init__(self, embedding_model_name="tongyi"):
        self.embeddings = get_embedding(embedding_model_name, api_config.get_api_key())
        self.chat_history = []
        self.dir_path = "chat_logs"
        self.saver = ChatSaver(self.dir_path)
        self.tool_registry = ToolRegistry()
        self.register_semantic_tools()

    def add_user_message(self, msg: str):
        self.chat_history.append(f"你：{msg}")

    def add_assistant_message(self, msg: str):
        self.chat_history.append(f"助手：{msg}")

    def save_chat(self, *_):
        path = self.saver.save(self.chat_history)
        return f"✅ 聊天记录已保存至：{path}"

    def clear_chat(self, *_):
        delete_md_files(self.dir_path)
        self.chat_history.clear()
        return "✅ 聊天记录已清空。"

    def show_chat_history(self, *_):
        if not self.chat_history:
            return "📭 当前无聊天记录。"
        return "📝 最近聊天记录：\n" + "-" * 20 + "\n" + "\n".join(self.chat_history[-5:]) + "\n" + "-" * 20

    def register_semantic_tools(self):
        self.tool_registry.register_tool(SemanticTool(
            name="保存聊天",
            examples=[
                "保存对话", "记录聊天", "请保存一下", "帮我备份", "能不能保存聊天记录", "我想把聊天内容留下来"
            ],
            handler=self.save_chat,
            embeddings=self.embeddings
        ))
        self.tool_registry.register_tool(SemanticTool(
            name="清空聊天",
            examples=[
                "清空对话", "重置聊天", "请清除所有记录", "把聊天内容清空", "重新开始"
            ],
            handler=self.clear_chat,
            embeddings=self.embeddings
        ))
        self.tool_registry.register_tool(SemanticTool(
            name="查看历史",
            examples=[
                "查看聊天记录", "展示最近聊天", "能看到刚才说的吗", "看看之前的聊天", "回顾一下聊天内容"
            ],
            handler=self.show_chat_history,
            embeddings=self.embeddings
        ))

    def default_reply(self, user_input: str) -> str:
        return "（模拟回复）我理解了你的问题。"

    def process_input(self, user_input: str) -> str:
        user_input = user_input.strip()
        if not user_input:
            return ""

        self.add_user_message(user_input)

        # 尝试语义匹配工具
        tool_response = self.tool_registry.match_tool(user_input)
        if tool_response:
            self.add_assistant_message(tool_response)
            return tool_response

        # 默认 LLM 回复
        reply = self.default_reply(user_input)
        self.add_assistant_message(reply)
        return reply

    def interactive_loop(self):
        print("🗨️ 开始聊天（输入空行退出）")
        while True:
            user_input = input("你：").strip()
            if not user_input:
                print("👋 再见！")
                break
            reply = self.process_input(user_input)
            print(f"助手：{reply}")


if __name__ == "__main__":
    session = ChatSession()
    session.interactive_loop()
