FROM python:3.9-alpine

COPY . .

RUN apk add --update --no-cache --virtual .tmp gcc libc-dev linux-headers
RUN apk add --no-cache jpeg-dev zlib-dev
RUN pip install -r requirements.txt
RUN apk del .tmp

RUN crontab crontab

CMD ["crond", "-f"]
