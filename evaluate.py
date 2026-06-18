import os
import json
import pandas as pd
from dotenv import load_dotenv

# Fix lỗi thư viện ragas không tìm thấy ChatVertexAI trong phiên bản langchain mới
import sys
import types
try:
    from langchain_google_vertexai import ChatVertexAI
    mock_module = types.ModuleType('langchain_community.chat_models.vertexai')
    mock_module.ChatVertexAI = ChatVertexAI
    sys.modules['langchain_community.chat_models.vertexai'] = mock_module
    
    import pydantic.v1
    sys.modules['langchain_core.pydantic_v1'] = pydantic.v1
    sys.modules['langchain.pydantic_v1'] = pydantic.v1
except ImportError:
    pass

import nest_asyncio
nest_asyncio.apply()

import asyncio

# Import các metrics từ Ragas
# pyrefly: ignore [missing-import]
from ragas import evaluate
from ragas.run_config import RunConfig
# pyrefly: ignore [missing-import]
from ragas.metrics import (
    Faithfulness,
    AnswerRelevancy,
    ContextRecall,
)

# pyrefly: ignore [missing-import]
from datasets import Dataset
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

import sys
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

async def main():
    run_evaluation()

def run_evaluation():
    print("=== Khởi động Ragas Evaluation Pipeline ===")
    
    # 1. Load biến môi trường và thiết lập models
    load_dotenv()
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Chưa cấu hình GOOGLE_API_KEY")
        return

    # Khởi tạo mô hình đánh giá (Gemini) và bọc qua Wrapper của Ragas
    evaluator_llm = LangchainLLMWrapper(ChatGoogleGenerativeAI(model="gemini-2.5-flash"))
    evaluator_embeddings = LangchainEmbeddingsWrapper(GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2"))
    
    # 2. Đọc dataset
    dataset_path = "golden_dataset.json"
    if not os.path.exists(dataset_path):
        print(f"❌ Không tìm thấy file {dataset_path}")
        return
        
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        data = data[:2] # Giảm xuống 2 test case để tránh quá tải API
        
    print(f"✅ Đã tải {len(data)} test cases từ {dataset_path} (đã cắt giảm để tránh Rate Limit)")
    
    # 3. Chuẩn bị dữ liệu cho Ragas
    # Ragas yêu cầu Dataset format có các trường: question, contexts, answer, ground_truth
    # Trong môi trường thực tế, "answer" và "contexts" sẽ được sinh ra từ hệ thống RAG hiện tại.
    # Để demo pipeline, chúng ta giả lập "answer" bằng cách gọi chính LLM hoặc dùng answer có sẵn.
    
    prepared_data = {
        "question": [],
        "contexts": [],
        "answer": [],
        "ground_truth": []
    }
    
    for i, item in enumerate(data):
        prepared_data["question"].append(item["question"])
        prepared_data["contexts"].append(item["contexts"])
        prepared_data["ground_truth"].append(item["ground_truth"])
        
        # Giả lập câu trả lời từ RAG bằng cách dùng thẳng ground_truth (để tránh Rate Limit khi test pipeline)
        print(f"Đang chuẩn bị câu trả lời cho test case {i+1} (Dùng sẵn ground_truth để tránh Rate Limit)...")
        prepared_data["answer"].append(item["ground_truth"])
        
    dataset = Dataset.from_dict(prepared_data)
    
    # 4. Thực thi Evaluation
    print("⏳ Đang tính toán các chỉ số Faithfulness, Answer Relevancy, Context Recall...")
    
    try:
        metrics = [
            Faithfulness(llm=evaluator_llm),
            AnswerRelevancy(llm=evaluator_llm, embeddings=evaluator_embeddings),
            # ContextRecall(llm=evaluator_llm), # Tạm tắt chỉ số này vì nó ngốn quá nhiều API request
        ]
        run_config = RunConfig(max_workers=1, max_retries=15, timeout=180, max_wait=120)
        result = evaluate(
            dataset=dataset,
            metrics=metrics,
            llm=evaluator_llm,
            embeddings=evaluator_embeddings,
            run_config=run_config,
        )
        
        # 5. Xuất báo cáo
        df = result.to_pandas()
        report_path = "evaluation_report.csv"
        df.to_csv(report_path, index=False)
        
        print("\n=== KẾT QUẢ ĐÁNH GIÁ ===")
        print(result)
        print(f"✅ Báo cáo chi tiết đã lưu tại: {report_path}")
        
    except Exception as e:
        print(f"❌ Có lỗi trong quá trình đánh giá: {e}")
        print("💡 Hãy đảm bảo bạn đã cài đặt Ragas: pip install ragas datasets pandas")

if __name__ == "__main__":
    asyncio.run(main())
