# Sử dụng image Python 3.11 gọn nhẹ
FROM python:3.11-slim

# Thiết lập thư mục làm việc trong Container
WORKDIR /app

# Copy file requirements và cài đặt thư viện
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn backend vào Container
COPY . .

# Tạo các thư mục cần thiết
RUN mkdir -p chroma_db_storage uploaded_papers

# Mở cổng 8000 cho FastAPI
EXPOSE 8000

# Lệnh chạy ứng dụng khi Container khởi động
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
