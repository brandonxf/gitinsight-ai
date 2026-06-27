# Despliegue gratuito — GitInsight AI

Guía para desplegar a **coste $0** en una VM **Oracle Cloud "Always Free"** (ARM
Ampere, hasta 4 vCPU / 24 GB RAM, gratis para siempre), usando **Groq free tier**
como LLM y **Caddy** para HTTPS automático. Sin GPU, sin problemas de RAM.

> ¿Por qué este combo? El LLM se ejecuta en Groq (no consume RAM de tu servidor),
> los embeddings corren en CPU con FastEmbed, y todo lo demás es ligero. En reposo
> el stack ronda ~1–2 GB, así que sobra de largo en la VM gratuita.

---

## 0. Lo que necesitas (todo gratis)

- Cuenta en **Oracle Cloud** (pide tarjeta solo para verificar; los recursos
  *Always Free* no se cobran).
- API key de **Groq**: <https://console.groq.com/keys>.
- (Recomendado) Un subdominio gratis en **DuckDNS** <https://www.duckdns.org>
  para tener HTTPS. Si no, puedes empezar con solo HTTP y la IP pública.

---

## 1. Crear la VM (Oracle Always Free)

1. Consola Oracle → **Compute → Instances → Create Instance**.
2. **Image**: Ubuntu 22.04 (o 24.04). **Shape**: *Ampere* `VM.Standard.A1.Flex`
   → asigna p. ej. **2 OCPU / 12 GB** (entra en Always Free; puedes subir a 4/24).
   - Si te da "out of capacity", reintenta o cambia de *Availability Domain*/región.
3. Descarga la **clave SSH** que te genera (o sube la tuya).
4. Crea la instancia y anota su **IP pública**.

### Abrir puertos 80 y 443

Hay que abrirlos en **dos sitios**:

a) **Security List / NSG** de la VCN (consola Oracle → Networking → tu VCN →
   Security List): añade *Ingress Rules* para `0.0.0.0/0` en TCP **80** y **443**.

b) Dentro de la VM (Oracle trae iptables restrictivo):

```bash
sudo iptables -I INPUT 1 -p tcp --dport 80  -j ACCEPT
sudo iptables -I INPUT 1 -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save     # persiste tras reinicios
```

---

## 2. Apuntar el dominio (opcional pero recomendado para HTTPS)

En DuckDNS crea un subdominio (p. ej. `gitinsight`) y pon la **IP pública** de la
VM. Tu sitio será `gitinsight.duckdns.org`.

---

## 3. Instalar Docker en la VM

```bash
ssh -i tu-clave.key ubuntu@TU_IP_PUBLICA

curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker            # o cierra y reabre la sesión SSH
docker compose version   # debe responder (plugin v2)
```

---

## 4. Clonar el repo y configurar el entorno

```bash
git clone https://github.com/brandonxf/gitinsight-ai.git
cd gitinsight-ai

cp .env.prod.example .env.prod
nano .env.prod
```

Rellena en `.env.prod`:

- `SITE_ADDRESS` → tu dominio (`gitinsight.duckdns.org`) para HTTPS, **o** `:80`
  si aún no tienes dominio.
- `POSTGRES_PASSWORD` → genera una:  `openssl rand -base64 24`
- `DATABASE_URL` → la misma contraseña que `POSTGRES_PASSWORD`.
- `CORS_ORIGINS` → `https://tu-dominio` (o `http://TU_IP` si vas sin dominio).
- `LLM_API_KEY` → tu key de Groq (`gsk_...`).

---

## 5. Construir y levantar

> En la VM ARM, el build genera imágenes **arm64** automáticamente (build nativo).

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

Aplica las migraciones de la base de datos (crea tablas + extensión pgvector):

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod \
  run --rm backend alembic upgrade head
```

Comprueba que todo está arriba:

```bash
docker compose -f docker-compose.prod.yml ps
```

Abre **https://tu-dominio** (o `http://TU_IP`). Caddy emite el certificado solo en
el primer acceso si pusiste un dominio.

---

## 6. Operación

```bash
# Logs
docker compose -f docker-compose.prod.yml logs -f backend worker

# Actualizar a la última versión
git pull
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
docker compose -f docker-compose.prod.yml --env-file .env.prod \
  run --rm backend alembic upgrade head   # si hubo migraciones nuevas

# Parar / reiniciar
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

### Backup de la base de datos

```bash
docker compose -f docker-compose.prod.yml exec db \
  pg_dump -U gitinsight gitinsight > backup_$(date +%F).sql
```

---

## Notas

- **Sin Ollama**: el chat usa Groq (gratis). Si algún día quieres LLM local,
  añade el servicio `ollama` y cambia `LLM_*` a apuntar a él (necesitarás más RAM).
- **Embeddings**: locales con FastEmbed. `EMBEDDING_THREADS=2` acota RAM/CPU; la
  primera indexación descarga el modelo (~130 MB) una sola vez.
- **Seguridad**: solo Caddy expone puertos (80/443). Postgres y Redis quedan en la
  red interna de Docker, sin acceso externo.
- **RAM esperada** (sin Ollama): ~1–2 GB en reposo; picos durante un análisis. Holgado
  en la VM Always Free.
- **Flower** (panel de Celery) no se incluye en producción; añádelo solo si lo
  necesitas para depurar.
