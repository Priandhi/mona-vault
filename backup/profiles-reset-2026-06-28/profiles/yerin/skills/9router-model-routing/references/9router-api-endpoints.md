# 9Router API Endpoints Reference

9Router is a Next.js app. All routes are documented in the build manifest.

## Finding Endpoints
```bash
cat /usr/lib/node_modules/9router/app/.next-cli-build/app-path-routes-manifest.json | python3 -m json.tool
```

## Auth
All API calls require auth cookie. Login first:
```bash
curl -s -c cookies.txt http://localhost:20128/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"password":"Mona187"}'
```

## Kiro OAuth Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/oauth/kiro/import` | Import refresh token (body: `{"refreshToken": "..."}`) |
| GET | `/api/oauth/kiro/auto-import` | Auto-detect from `~/.aws/sso/cache/kiro-auth-token.json` |
| GET | `/api/oauth/kiro/social-authorize?provider=google` | Get AWS Builder ID OAuth URL |
| POST | `/api/oauth/kiro/social-exchange` | Exchange OAuth code for token |

## Provider Management
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/providers` | List all connections |
| GET | `/api/providers/{id}` | Get provider details |
| POST | `/api/providers/{id}/test` | Test provider connection |
| GET | `/api/providers/{id}/models` | List provider models |

## Dashboard Routes
| Route | Purpose |
|-------|---------|
| `/dashboard/providers` | All providers list |
| `/dashboard/providers/kiro` | Kiro AI provider page |
| `/dashboard/providers/{id}` | Individual provider page |
| `/dashboard/providers/new` | Add new provider |

## Settings
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/settings` | Get all settings |
| POST | `/api/settings` | Update settings |

## Key Files
- Database: `~/.9router/db/data.sqlite`
- Auth secret: `~/.9router/auth/cli-secret`
- Kiro token cache: `~/.aws/sso/cache/kiro-auth-token.json`
- 9Router source: `/usr/lib/node_modules/9router/`
- Route manifest: `/usr/lib/node_modules/9router/app/.next-cli-build/app-path-routes-manifest.json`
