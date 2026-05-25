FROM python:3.12-slim

WORKDIR /app

# 直接安装Python依赖（slim镜像已包含基本编译工具）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制项目文件
COPY . .

# 创建必要目录
RUN mkdir -p media staticfiles

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["sh", "-c", "python manage.py makemigrations --noinput && python manage.py migrate --noinput && (python manage.py shell -c \"from django.contrib.auth.models import User; exit(0 if User.objects.filter(is_superuser=True).exists() else 1)\" || python manage.py init_data) && python manage.py runserver 0.0.0.0:8000"]
