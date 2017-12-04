FROM python

RUN pip install requests

#ENV PEW_EMAIL
#ENV PEW_PASSWORD
ENV PEW_SESSION_FILE=/config/session.json
ENV PEW_OUTPUT_DIR=/output

WORKDIR /app

COPY . /app

VOLUME /config /output

CMD python main.py


