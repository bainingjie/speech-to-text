FROM python:3.9.13
WORKDIR /app
COPY . /app



RUN pip install -r requirements.txt && \
    apt-get update && \
    apt-get install -y portaudio19-dev && \
    pip install PyAudio && \
    pip install langchain && \
    pip install langchain-anthropic
EXPOSE 8000
# CMD ["python", "-m", "speech_to_text"]
CMD ["python", "llm.py"]