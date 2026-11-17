FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN useradd --create-home --uid 1000 muhuresearch
COPY --chown=muhuresearch:muhuresearch . /app
USER muhuresearch
EXPOSE 7860
CMD ["python","-B","app.py","--host","0.0.0.0","--port","7860","--data-dir","dataset"]
