FROM python:3.7-alpine3.16

# Fix CVE-2022-43680, CVE-2019-8457, CVE-2021-46848, CVE-2022-42898
RUN apk update && apk add --upgrade expat=2.5.0-r0 krb5-libs=1.19.4-r0 gcc g++ linux-headers

WORKDIR /app

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]