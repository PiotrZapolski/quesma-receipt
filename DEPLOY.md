# Deploy: quesma.agentshub.pl

Statyczna strona z katalogu `site/` (nginx w kontenerze), wspolny serwer Hetzner,
wspolny Caddy jako reverse proxy. Deploy idzie zawsze przez GitHub: push na `main`
-> self-hosted runner na prodzie -> `git reset --hard` + `docker compose up`.

Repo: `https://github.com/PiotrZapolski/quesma-receipt` (branch `main`).

## Jednorazowa konfiguracja serwera (jako root)

Najpierw przeczytaj `/root/SERVER.md` na serwerze - opisuje aktualny uklad
katalogow, nazwe kontenera Caddy i sposob przeladowania konfiguracji.

### 1. Klon repo

```bash
mkdir -p /var/www/clients
cd /var/www/clients
git clone https://github.com/PiotrZapolski/quesma-receipt.git quesma
```

### 2. Runner GitHub Actions

Zarejestruj self-hosted runnera dla repo `PiotrZapolski/quesma-receipt`:

https://github.com/PiotrZapolski/quesma-receipt/settings/actions/runners/new

- labelki: `self-hosted,hetzner`
- runner musi chodzic jako uzytkownik, ktory ma dostep do dockera i prawo czytac
  oraz zapisywac `/var/www/clients/quesma` (tak jak runner lakfam: `hetzner-lakfam`)

### 3. Caddy

Dopisz blok z `deploy/Caddyfile.snippet` do wspolnego Caddyfile, a potem przeladuj:

```bash
docker exec <kontener-caddy> caddy reload --config /etc/caddy/Caddyfile
```

Dokladna nazwa kontenera i sciezka do Caddyfile - patrz `/root/SERVER.md`.

### 4. Pierwsze uruchomienie recznie

```bash
cd /var/www/clients/quesma
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Sprawdzenie:

```bash
curl -fsS -H 'Host: quesma.agentshub.pl' http://localhost/healthz
```

Od tego momentu kazdy push na `main` deployuje sie sam (workflow
`.github/workflows/deploy.yml`, mozna go tez odpalic recznie przez
"Run workflow" / `workflow_dispatch`).

## Lokalnie

```bash
docker compose up
```

Strona: http://localhost:8095 (health: http://localhost:8095/healthz).

Uwaga: na laptopie wlasciciela nic nie startuje bez jego wyraznej zgody -
powyzsza komenda jest do odpalenia recznie przez czlowieka, nie przez agenta.
