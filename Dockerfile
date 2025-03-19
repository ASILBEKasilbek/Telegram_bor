# 1. Rasm sifatida Python 3.10 ni ishlatamiz
FROM python:3.10

# 2. Ishchi katalogni yaratamiz
WORKDIR /app

# 3. Kerakli fayllarni konteyner ichiga ko‘chirib olamiz
COPY requirements.txt requirements.txt

# 4. Kutubxonalarni o‘rnatamiz
RUN pip install --no-cache-dir -r requirements.txt

# 5. Barcha kodni konteyner ichiga nusxalaymiz
COPY . .

# 6. Botni ishga tushiramiz
CMD ["python", "main.py"]
