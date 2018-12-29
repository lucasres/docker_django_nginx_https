# docker + django + nginx + certbot

## Iniciando o docker
Primeiro criei o seu arquivo Dockerfile:
 ```
 FROM python:3
 ENV PYTHONUNBUFFERED 1
 RUN mkdir /code
 WORKDIR /code
 ADD requirements.txt /code/
 RUN pip install -r requirements.txt
 ADD ./src/ /code/
```

Os arquivos do django estão na pasta src, que serao adicionada no container em code.

Agora crie o docker-compose.yml:
```
version: '2'

services:
  nginx:
    image: nginx:latest
    container_name: nginx_app
    ports:
      - "80:8000"
      - "443:443"
    volumes:
      - ./src:/code
      - ./config/nginx:/etc/nginx/conf.d
    depends_on:
      - web

  web:
    build: .
    container_name: django_app
    command: python3 manage.py runserver 0.0.0.0:8000
    volumes:
      - ./src:/code
    ports:
      - "8000:8000"
```

Temos dois serviços, um que  o nginx rodando na porta 80 e 443 e uma aplicação django rodando na porta 8000
para executar use o comando

```
sh inicia.sh
```
## Configurando o ngninx

As configurações do nginx estão na pasta config/nginx/nginx.conf, existe um volume no serviço do ngninx que mapeia para o container em /etc/nginx/conf.d

```
...
volumes:
   - ./config/nginx:/etc/nginx/conf.d
...
```

o arquivo ngnix.conf
```
upstream web {
  ip_hash;
  server web:8000;
}

server {

    location /static/ {
        autoindex on;
        alias /static/;
    }

    location / {
        proxy_pass http://web/;
    }
    listen 8000;

    server_name dominiohaha.tk;
}
```

Percebemos que temos um upstream que aponta pro serviço do django(web:8000). O bloco server recebe as requisições no nosso dominio e encaminham para o upstream

## Gerando os certificados

Certbot - https://certbot.eff.org/

Apenas instale o certbot no servidor, apos isso crie uma pasta em:
```
mkdir /root/certs-data/
```
Depois execute:
```
sudo certbot certonly --webroot -w /root/certs-data/ -d DOMINIO_AQUI
```
Esse comando vai dar erro pois não vai ser possivel passar no desafio do certbot
Para passar execute os passos:
configure o nginx.conf, adicionando o campo abaixo no server:
```
location ^~ /.well-known {
      allow all;
      root  /data/letsencrypt/;
    }
```
agora vamos criar um volume no nginx com a pasta que criamos:
```
volumes:
  - /root/certs-data/:/data/letsencrypt/
```
Essa pasta tem um arquivo chamado index.html, ele eh quem vai fazer passar no teste:
```
cd /root/cd certs-data/
mkdir .well-known
cd .well-known
echo test >> index.html
```
reenicia o servidor:
```
sh inicia.sh
```
tente acessar dominio.com/.well-know, ele tera que retornar test

por ultimo:
```
sudo certbot certonly --webroot -w /root/certs-data/ -d DOMINIO_AQUI
```
caso tudo der certo, os certificados serao gerados, eles estão em etc/letsencrypt/lives/dominio.com/, mas nessa pasta so tem os links para os arquivos.
Eles estão realmente em etc/letsencrypts/archive/dominio.com/
Tera varios arquivos mas os que nos interesa são:
privkey1.pem <- chave privada
fullchain.pem <- chave pública

agora é so add um volume para o nginx 
```
volumes:
   - /apps/config/certs:/etc/certificates
```
Lembre de copiar os arquivos de etc/letsencrypts/archive/dominio.com/ para app/config/certs

agora que ja temos os certificados mapeados para o container do ngninx precisamos configurar o nginx.conf para receber requisiçes de https
```
upstream web {
  ip_hash;
  server web:8000;
}

server {
    
    listen 8000;
    server_name dominiohaha.tk;
    return 301 https://$host$request_uri;
    
}

server { 
    location /static/ {
        autoindex on;
        alias /static/;
    }

    location / {
        proxy_pass http://web/;
    }
    
    server_name dominiohaha.tk;

    location ^~ /.well-known {
        allow all;
        root  /data/letsencrypt/;
    }

    listen 443 ssl;
    server_name dominiohaha.tk;
    ssl_certificate /etc/certificates/fullchain1.pem;
    ssl_certificate_key /etc/certificates/privkey1.pem;
}
```
observe que botamos o local o mesmo onde criamos os volumes, uma vez que o docker mapeia os arquivos locais no diretorio que mandamos na hora que criamos nossos volumes

reinici o servidor e ja era
```
sh inicia.sh
```
