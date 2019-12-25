FROM python:3

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY settings_porter.py .
COPY tests tests
COPY default_settings .
ENTRYPOINT ["python3", "settings_porter.py"]
