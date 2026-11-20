# Límites, errores y reintentos

Este documento describe los límites de uso de la API de PagoNube, el formato
de los errores y la política recomendada de reintentos.

## Límite de solicitudes

Cada API key puede realizar hasta **120 solicitudes por minuto**. Además, se
permite un burst máximo de **20 solicitudes en 10 segundos**.

El límite es por clave, no por usuario ni por IP. Si una integración usa varias
claves, cada una tiene su propio cupo.

### Headers de límite

Cada respuesta incluye headers con el estado del cupo:

| Header | Significado |
|---|---|
| `X-RateLimit-Limit` | Límite total por minuto |
| `X-RateLimit-Remaining` | Solicitudes restantes en la ventana actual |
| `X-RateLimit-Reset` | Timestamp UNIX en que se reinicia la ventana |

Cuando se supera el límite, la API responde `429 Too Many Requests` con el
código `rate_limit_exceeded` y el header `Retry-After` indicando cuántos
segundos esperar.

## Formato de error

Todos los errores tienen la misma estructura:

```json
{
  "error": {
    "code": "validation_error",
    "message": "El monto debe ser mayor o igual a 100.",
    "request_id": "req_01HZX..."
  }
}
```

El `request_id` es único por solicitud y sirve para rastrearla en el panel de
desarrolladores o al contactar al soporte.

## Códigos de error

| HTTP | Código | Significado |
|---|---|---|
| `400` | `invalid_request` | JSON mal formado o header faltante |
| `401` | `unauthorized` | API key ausente, inválida o expirada |
| `403` | `forbidden` | La clave no tiene el scope necesario |
| `404` | `not_found` | El recurso solicitado no existe |
| `409` | `conflict` | Conflicto de idempotencia o estado |
| `422` | `validation_error` | Datos inválidos (monto, moneda, plazo) |
| `429` | `rate_limit_exceeded` | Se superó el límite de solicitudes |
| `500` | `internal_error` | Error interno de PagoNube |
| `503` | `service_unavailable` | Servicio temporalmente no disponible |

## Qué errores se pueden reintentar

No todos los errores son transitorios. Reintentar un error de validación solo
genera más tráfico y el mismo resultado.

| Error | ¿Reintentar? |
|---|---|
| `400`, `401`, `403`, `404`, `422` | No |
| `409` | No, salvo que se haya resuelto el conflicto |
| `429` | Sí, respetando `Retry-After` |
| `500`, `503` | Sí, con backoff exponencial |
| Timeout de red | Sí, con la misma `Idempotency-Key` |

## Backoff exponencial

La política recomendada es:

1. Esperar 1 segundo.
2. Si falla, esperar 2 segundos.
3. Si falla, esperar 4 segundos.
4. Máximo 3 reintentos.

Se debe agregar una variación aleatoria (jitter) para evitar que muchos clientes
reintenten exactamente al mismo tiempo.

En operaciones de escritura, como crear un pago o un reembolso, hay que reutilizar
la misma `Idempotency-Key` en cada reintento. Así se evita duplicar la operación.

## Webhooks

PagoNube reintenta la entrega de un webhook hasta **5 veces** si la aplicación
no responde con `2xx`. Los intervalos son crecientes: 10 segundos, 30 segundos,
2 minutos, 10 minutos y 1 hora.

La aplicación debe:

- Responder rápido (menos de 5 segundos).
- Verificar la firma `X-PagoNube-Signature`.
- Ser idempotente: un mismo evento puede llegar más de una vez.
- Guardar el `event_id` para detectar duplicados.

Si después de los 5 intentos el webhook sigue fallando, el evento queda
disponible en el panel de desarrolladores para reenvío manual.

## Paginación

Los endpoints de listado devuelven como máximo **50 elementos por página**.

```http
GET /v1/pagos?limit=50&cursor=pag_01HZX...
```

La respuesta incluye `next_cursor`. Cuando `next_cursor` es `null`, no hay más
páginas.

## Timeouts

El tiempo máximo recomendado para una solicitud es de **10 segundos**. Si la
aplicación no recibe respuesta en ese plazo, debe cancelar la solicitud y
reintentar según la política anterior.

Para operaciones de escritura, el timeout no significa que la operación no se
haya realizado. Por eso siempre hay que reutilizar la `Idempotency-Key`.

## Buenas prácticas

- Monitorear los headers `X-RateLimit-*` para anticiparse a los límites.
- Respetar `Retry-After` cuando la API lo devuelve.
- No reintentar errores `4xx` de validación.
- Usar jitter en el backoff.
- Registrar `request_id` y `event_id` para trazabilidad.
- Implementar idempotencia tanto en las llamadas salientes como en los webhooks
  entrantes.
