# 第一行代码：导入相关的库
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.deepseek import DeepSeek
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 加载本地嵌入模型，避免open ai api
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-zh")

# 创建 Deepseek LLM
llm = DeepSeek(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY")
)

# 第二行代码：加载数据
#documents = SimpleDirectoryReader(input_files=["data/黑悟空/设定.txt"]).load_data()
documents = SimpleDirectoryReader(
    input_dir="../data/Avionics_files"  # 直接指定文件夹路径，无需写具体文件名
).load_data()

# 第三行代码：构建索引
index = VectorStoreIndex.from_documents(
    documents,
    embed_model=embed_model
)

# 第四行代码：创建问答引擎
query_engine = index.as_query_engine(
    llm=llm
)

# 第五行代码: 开始问答
# print(query_engine.query("黑神话悟空中有哪些战斗工具？"))
print(query_engine.query(" 需求编号： REQ-LG-001 功能描述： 起落架控制逻辑。 具体规约： 当且仅当起落架控制手柄（Gear Handle）处于“DOWN”位置，且飞行速度（Airspeed）低于 250 节时，起落架执行机构应在 3 秒内接收到“放下（Deploy）”指令。若速度超过 250 节，即使手柄在“DOWN”位，也不允许执行放下动作，并需触发告警。"
                         "请你先分解原子需求，再根据 IEEE 829 标准模板生成对原子需求点的测试用例"))
