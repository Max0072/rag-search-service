
# Health check
``` bash
curl -X GET "https://ragservice-production-f1b3.up.railway.app/api/v1/health"
```

``` bash
curl -X GET "https://ragservice-production-f1b3.up.railway.app/docs"
```

``` bash
curl -X GET "https://ragservice-production-f1b3.up.railway.app/redoc"
```

``` bash
curl -X DELETE "https://ragservice-production-f1b3.up.railway.app/api/v1/clear-all"
```

``` bash
curl -X POST "https://ragservice-production-f1b3.up.railway.app/api/v1/upload_json"

```


``` bash
curl -X POST "https://ragservice-production-f1b3.up.railway.app/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {
      "chunks": "WebSocket Socket.io real-time updates SSE",
      "contains": "WebSocket"
    },
    "fields": ["call_id", "chunk_text", "date", "attendants", "score"],
    "top_k": 20,
    "min_score": 0.3
  }'
```

``` bash

```


``` bash

```

``` bash

```


``` bash

```

``` bash

```

``` bash

```

``` bash

```

``` bash

```