#Slim is a lightweight Debian Linux that plays well with Postgre
FROM python:3.12-slim
#forces log messages to print immediately to the terminal
ENV PYTHONUNBUFFERED=1
#stops Python from writing useless .py
ENV PYTHONDONTWRITEBYTECODE=1
#command to set your folder inside the container to /app.
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
#coping your entire Django project into the /app folder.
COPY . . 
#command to expose network port
EXPOSE 8000
#The Boot Command: This is what runs when the container start
CMD ["gunicorn","--bind","0.0.0.0:8000","config.wsgi:application"]
