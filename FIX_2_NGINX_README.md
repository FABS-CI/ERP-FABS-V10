# FIX #2: Nginx Reverse Proxy

## Status

Nginx NÃO está instalado/rodando no sistema.

```bash
pgrep nginx  # → NOT FOUND
```

## Solução Aplicada

Criei dois arquivos para você:

### 1. `docker-compose.nginx.yml`
- Adiciona serviço Nginx ao Docker Compose
- Porta 80 (HTTP) e 443 (HTTPS quando configurado)
- Integra com Backend (porta 8001)
- Rate limiting, CORS, cache, logs estruturados

### 2. `nginx.conf`
- Configuração Nginx production-ready
- Proxy reverso para /api/*
- Rate limiting por IP (API: 100 req/s, Login: 10 req/min)
- Security headers, compression, logging JSON
- Pronto para SSL/TLS (comentado)

## Como usar

### Opção A: Docker Compose (RECOMENDADO PARA PROD)

```bash
# Replace current docker-compose.yml
cp docker-compose.yml docker-compose.old.yml
cp docker-compose.nginx.yml docker-compose.yml

# Criar diretório de configurações
mkdir -p nginx-conf.d

# Start stack with Nginx
docker-compose up -d

# Verify
curl http://localhost/health  # → OK
curl http://localhost/api/health  # → Backend response
```

### Opção B: Instalação Sistema Ubuntu

```bash
sudo apt update
sudo apt install -y nginx

# Copy config
sudo cp nginx.conf /etc/nginx/nginx.conf
sudo mkdir -p /etc/nginx/conf.d

# Test & start
sudo nginx -t
sudo systemctl start nginx
sudo systemctl enable nginx

# Verify
sudo systemctl status nginx
curl http://localhost/health
```

## Alterações Necessárias

### 1. No `docker-compose.yml` original:
```yaml
services:
  # ADD THIS
  nginx:
    image: nginx:alpine
    container_name: fabsci-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend
    networks:
      - fabsci-network
```

### 2. No Backend, adicione healthcheck:
```yaml
backend:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
    interval: 30s
```

## Verificação

```bash
# Test reverse proxy
curl -I http://localhost/api/health
# → X-Real-IP, X-Forwarded-* headers presentes

# Test rate limiting
for i in {1..120}; do curl http://localhost/api/ 2>/dev/null; done
# → Depois de 100 req: 429 Too Many Requests

# Test CORS
curl -H "Origin: http://example.com" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS http://localhost/api/ -v
# → Access-Control-* headers presentes
```

## SSL/TLS (HTTPS)

Quando tiver certificados:

1. Coloque em `./ssl/`:
   - `cert.pem` (certificado)
   - `key.pem` (chave privada)

2. Descomente em `nginx.conf`:
   ```nginx
   server {
       listen 443 ssl http2;
       ssl_certificate /etc/nginx/ssl/cert.pem;
       ssl_certificate_key /etc/nginx/ssl/key.pem;
   }
   
   server {
       listen 80;
       return 301 https://$host$request_uri;
   }
   ```

3. Reload:
   ```bash
   docker-compose exec nginx nginx -t
   docker-compose exec nginx nginx -s reload
   ```

## Métricas & Logs

- **Access logs:** `/var/log/nginx/access.log` (JSON format)
- **Error logs:** `/var/log/nginx/error.log`
- **Metrics:** GET `/nginx-metrics` (internal only, Docker network)

## Problème Connu

O arquivo `docker-compose.yml` **ORIGINAL** usa `frontend` (port 80):
```yaml
frontend:
  ports:
    - "80:80"
```

Se usar com Nginx:
- ❌ Conflict: ambos querem port 80
- ✅ Solução: comentar `frontend` ou usar porta 3000

O `docker-compose.nginx.yml` já tem isso configurado.

---

## Próximos Passos

1. ✅ Fixos: Doublons (#1) + Audit endpoint (#3)
2. ⏳ TODO: Escolha entre Docker Compose ou Sistema install
3. ⏳ TODO: Re-rodar E2E test para validar todos 3 fixes

