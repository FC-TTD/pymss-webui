FROM pymss-preview-runtime:h-bd63eb3d3ceeebfe
COPY deploy/chain/app.py /app/chain_api.py
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
ENTRYPOINT []
CMD ["python","-m","uvicorn","chain_api:app","--host","0.0.0.0","--port","8000","--workers","1"]
